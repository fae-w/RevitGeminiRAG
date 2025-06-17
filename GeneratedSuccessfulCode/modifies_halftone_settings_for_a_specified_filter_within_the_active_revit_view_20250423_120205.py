# Purpose: This script modifies halftone settings for a specified filter within the active Revit view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    OverrideGraphicSettings,
    View,
    ElementId,
    ViewType
)
from Autodesk.Revit.UI import UIDocument
import System # For exception handling

# --- Configuration ---
target_filter_name = "Existing Elements Filter"
target_halftone_setting = False # Set Halftone to Off

# --- Get Active Document and View ---
# uidoc is assumed available
# doc is assumed available
active_view = doc.ActiveView
error_messages = []
proceed_execution = True

# --- Validate Active View ---
if not active_view:
    error_messages.append("# Error: No active view found.")
    proceed_execution = False
elif not isinstance(active_view, View):
    error_messages.append("# Error: Active document is not a View.")
    proceed_execution = False
elif active_view.IsTemplate:
    error_messages.append("# Error: Active view is a View Template. Cannot apply overrides directly.")
    proceed_execution = False
else:
    # Check if the view type supports filters that can be overridden graphically
    supported_view_types = [
        ViewType.FloorPlan,
        ViewType.CeilingPlan,
        ViewType.Elevation,
        ViewType.Section,
        ViewType.Detail,
        ViewType.DraftingView,
        ViewType.ThreeD,
        # ViewType.AreaPlan, ViewType.EngineeringPlan might also work
    ]
    if active_view.ViewType not in supported_view_types:
         error_messages.append("# Error: Active view type ('{}') does not typically support direct filter graphic overrides.".format(active_view.ViewType))
         proceed_execution = False

# --- Find the Filter Element ---
parameter_filter_element = None
if proceed_execution:
    collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    found_filter = False
    # Use FirstOrDefault LINQ method for efficiency if System.Core is referenced,
    # otherwise iterate. Iteration is safer in basic IronPython setup.
    for f in collector:
        if f.Name == target_filter_name:
            parameter_filter_element = f
            found_filter = True
            # print("# Found filter: '{}' (ID: {})".format(target_filter_name, f.Id)) # Optional debug
            break
    if not found_filter:
        error_messages.append("# Error: Filter named '{}' not found in the document.".format(target_filter_name))
        proceed_execution = False

# --- Check if Filter is Applied and Modify Overrides ---
if proceed_execution and parameter_filter_element:
    filter_id = parameter_filter_element.Id
    is_applied = False
    try:
        # Check if the filter is applied to the view
        applied_filters = active_view.GetFilters() # Returns ICollection<ElementId>
        # Efficiently check if the filter_id is in the collection
        is_applied = filter_id in applied_filters

        if is_applied:
             # Check if the filter is actually enabled (visible) in the view's V/G settings
             if not active_view.GetIsFilterEnabled(filter_id):
                 print("# Info: Filter '{}' is applied to view '{}' but is currently disabled (not visible). Overrides will be set but have no visual effect until enabled.".format(target_filter_name, active_view.Name))

             # Get existing overrides (important for preserving other settings)
             current_overrides = active_view.GetFilterOverrides(filter_id)
             # If no overrides exist yet, GetFilterOverrides returns a default/empty OverrideGraphicSettings object
             # (or potentially null in older API versions, though unlikely now - safer to handle)
             if current_overrides is None:
                 current_overrides = OverrideGraphicSettings() # Start fresh if null returned

             # Create a new override settings object based on the current ones (copy constructor)
             new_overrides = OverrideGraphicSettings(current_overrides)

             # Set the desired halftone setting
             new_overrides.SetHalftone(target_halftone_setting)

             # Check if we can apply the overrides (might be locked by template or view type)
             # This is the crucial check for template control
             if active_view.IsFilterOverridesEditable(filter_id):
                 active_view.SetFilterOverrides(filter_id, new_overrides)
                 print("# Successfully set Halftone={} for filter '{}' in view '{}'.".format(target_halftone_setting, target_filter_name, active_view.Name))
             else:
                 # Provide more specific feedback if possible
                 template_id = active_view.ViewTemplateId
                 if template_id != ElementId.InvalidElementId:
                      template = doc.GetElement(template_id)
                      template_name = template.Name if template else "Invalid ID"
                      # Check if the 'Filters' parameter is controlled by the template
                      param_controlled = False
                      if template:
                           try:
                                # Check which parameters the template controls
                                controlled_params = template.GetTemplateParameterIds()
                                # Find the BuiltInParameter for V/G Overrides Filters
                                filters_param_id = ElementId(Autodesk.Revit.DB.BuiltInParameter.VIS_GRAPHICS_FILTERS)
                                if filters_param_id in controlled_params:
                                    param_controlled = True
                           except System.Exception:
                                # Older API might not have GetTemplateParameterIds or specific BIPS
                                pass # Fallback to generic message

                      if param_controlled:
                          error_messages.append("# Error: Cannot apply overrides for filter '{}' in view '{}'. The 'Filters' setting is controlled by the View Template: '{}'.".format(target_filter_name, active_view.Name, template_name))
                      else:
                           error_messages.append("# Error: Cannot apply overrides for filter '{}' in view '{}'. Although a template ('{}') is applied, the 'Filters' setting might not be controlled by it, or another restriction exists.".format(target_filter_name, active_view.Name, template_name))

                 else:
                      # If IsFilterOverridesEditable is false and no template, it's likely a view type limitation or internal state
                      error_messages.append("# Error: Cannot apply overrides for filter '{}' in view '{}'. No template applied, but overrides are not editable (possibly due to view type or other restrictions).".format(target_filter_name, active_view.Name))
        else:
            error_messages.append("# Error: Filter '{}' is not applied to the active view '{}'.".format(target_filter_name, active_view.Name))

    except System.Exception as e:
        # Catch Revit API exceptions
        error_messages.append("# Error processing filter '{}' in view '{}'. Reason: {}".format(target_filter_name, active_view.Name, e.Message))
    except Exception as py_err:
         # Catch IronPython exceptions
         error_messages.append("# Error: An unexpected Python error occurred: {}".format(py_err))

# Print any accumulated errors at the end
if error_messages:
    for msg in error_messages:
        print(msg)