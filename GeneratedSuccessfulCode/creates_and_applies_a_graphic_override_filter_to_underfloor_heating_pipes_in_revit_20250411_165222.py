# Purpose: This script creates and applies a graphic override filter to underfloor heating pipes in Revit.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
# No need for System.Collections explicitly, generic List works

# Revit API DB Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    BuiltInParameter,
    ParameterFilterRuleFactory,
    FilterRule,
    ElementParameterFilter,
    LogicalAndFilter, # Though implicitly handled by ParameterFilterElement rules
    OverrideGraphicSettings,
    Color,
    View,
    LinePatternElement,
    Element # Base class, also for Element.Name.GetValue
)
# Specific Plumbing imports
from Autodesk.Revit.DB.Plumbing import PipingSystemType

# System Imports
from System.Collections.Generic import List
from System import Double

# --- Helper function to find an element by class and name ---
def find_element_by_name(doc, element_class, name):
    """Finds the first element of a specific class by name (case-insensitive)."""
    collector = FilteredElementCollector(doc).OfClass(element_class)
    name_lower = name.lower()
    # Need to iterate as OfClass doesn't filter by name directly efficiently
    for element in collector:
        element_name = None
        try:
            # Prefer the static method for robustness
            element_name = Element.Name.GetValue(element)
        except Exception:
            # Fallback to direct property access if static method fails
            try:
                if hasattr(element, "Name"):
                    element_name = element.Name
            except Exception:
                # Ignore elements where name cannot be retrieved
                continue

        # Check if a valid name was retrieved and matches (use 'str' for IronPython 2)
        if element_name is not None and isinstance(element_name, str) and element_name.lower() == name_lower:
             return element.Id

    return ElementId.InvalidElementId # Return InvalidElementId if not found

# --- Configuration ---
filter_name = "Underfloor Heating Pipes"
target_category_bic = BuiltInCategory.OST_PipeCurves
system_type_name = "Hydronic Supply/Return" # Assumes a PipingSystemType with this exact name exists
elevation_param_bip = BuiltInParameter.RBS_PIPE_BOTTOM_ELEVATION
elevation_threshold_feet = 0.0 # Filter pipes where bottom elevation < 0 relative to level
invisible_line_pattern_name = "<Invisible lines>" # Revit uses <...> for some built-in patterns

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined
active_view = doc.ActiveView

# Proceed only if we have a valid view where overrides are allowed
if active_view and isinstance(active_view, View) and active_view.AreGraphicsOverridesAllowed():

    # --- Find Necessary Element IDs ---
    system_type_id = find_element_by_name(doc, PipingSystemType, system_type_name)
    invisible_pattern_id = find_element_by_name(doc, LinePatternElement, invisible_line_pattern_name)
    target_category_id = ElementId(target_category_bic)
    sys_type_param_id = ElementId(BuiltInParameter.RBS_PIPING_SYSTEM_TYPE_PARAM)
    elevation_param_id = ElementId(elevation_param_bip)

    # Check if all required elements/parameters were found
    if (system_type_id != ElementId.InvalidElementId and
            target_category_id != ElementId.InvalidElementId and
            sys_type_param_id != ElementId.InvalidElementId and
            elevation_param_id != ElementId.InvalidElementId):

        # --- Create Filter Rules ---
        rules = List[FilterRule]()
        rule1_ok = False
        rule2_ok = False

        try:
            rule1 = ParameterFilterRuleFactory.CreateEqualsRule(sys_type_param_id, system_type_id)
            rules.Add(rule1)
            rule1_ok = True
        except Exception as e_rule1:
            # Log error or handle externally if needed
            print("Error creating system type rule: {}".format(e_rule1)) # Basic logging
            pass # Error creating system type rule

        try:
            # Use System.Double for the numeric value
            rule2 = ParameterFilterRuleFactory.CreateLessRule(elevation_param_id, Double(elevation_threshold_feet))
            rules.Add(rule2)
            rule2_ok = True
        except Exception as e_rule2:
             # Log error or handle externally if needed
             print("Error creating elevation rule: {}".format(e_rule2)) # Basic logging
             pass # Error creating elevation rule

        # Proceed only if both rules were created successfully
        if rule1_ok and rule2_ok:
            # --- Define Categories ---
            categories = List[ElementId]()
            categories.Add(target_category_id)

            # --- Check if Filter Already Exists ---
            existing_filter_id = ElementId.InvalidElementId
            collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
            filter_name_lower = filter_name.lower() # For case-insensitive check
            for pfe in collector:
                try:
                    pfe_name = Element.Name.GetValue(pfe)
                    # Use 'str' for IronPython 2 string check
                    if pfe_name is not None and isinstance(pfe_name, str) and pfe_name.lower() == filter_name_lower:
                       existing_filter_id = pfe.Id
                       break
                except:
                    # Handle cases where name cannot be retrieved
                    pass

            filter_id_to_apply = ElementId.InvalidElementId

            if existing_filter_id != ElementId.InvalidElementId:
                filter_id_to_apply = existing_filter_id
                # Optional: Update existing filter rules/categories if needed (requires transaction - handled externally)
                try:
                    existing_filter = doc.GetElement(existing_filter_id)
                    # Ensure categories match (important for applying to view)
                    existing_categories = existing_filter.GetCategories()
                    # Basic check if categories differ (more robust check might compare sets)
                    if len(existing_categories) != len(categories) or categories[0] not in existing_categories:
                         existing_filter.SetCategories(categories) # Requires transaction
                    existing_filter.SetRules(rules) # Requires transaction
                except Exception as update_e:
                    # Log update error
                    print("Error updating existing filter: {}".format(update_e)) # Basic logging
                    pass
            else:
                # --- Create the Parameter Filter Element ---
                try:
                    # ParameterFilterElement.Create expects IList<FilterRule> for AND logic
                    new_filter = ParameterFilterElement.Create(doc, filter_name, categories, rules) # Requires transaction
                    filter_id_to_apply = new_filter.Id
                except Exception as e_create:
                    # Handle potential race condition or other creation errors
                    if "name is already in use" in str(e_create).lower():
                         # Re-query in case it was created between the check and the create call
                         collector_retry = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                         filter_name_lower_retry = filter_name.lower()
                         for pfe_retry in collector_retry:
                            try:
                                pfe_retry_name = Element.Name.GetValue(pfe_retry)
                                # Use 'str' for IronPython 2 string check
                                if pfe_retry_name is not None and isinstance(pfe_retry_name, str) and pfe_retry_name.lower() == filter_name_lower_retry:
                                     filter_id_to_apply = pfe_retry.Id
                                     break
                            except:
                                pass
                    else:
                         # Log other creation errors externally
                         print("Error creating filter: {}".format(e_create)) # Basic logging
                    # If filter_id_to_apply remains InvalidElementId, application below will fail gracefully

            # --- Apply Filter to Active View ---
            if filter_id_to_apply != ElementId.InvalidElementId:
                # --- Define Override Settings ---
                ogs = OverrideGraphicSettings()

                if invisible_pattern_id != ElementId.InvalidElementId:
                    # Preferred method: Use Invisible lines pattern to hide pipe body
                    ogs.SetProjectionLinePatternId(invisible_pattern_id)
                    ogs.SetCutLinePatternId(invisible_pattern_id)
                    # Set line weight to minimum to ensure lines are truly invisible
                    ogs.SetProjectionLineWeight(1)
                    ogs.SetCutLineWeight(1)
                    # Ensure no color override interferes
                    ogs.SetProjectionLineColor(Color.InvalidColorValue) # Use invalid color to not override
                    ogs.SetCutLineColor(Color.InvalidColorValue)
                else:
                    # Fallback: Set color to white (less reliable) and minimum weight
                    print("Warning: '<Invisible lines>' pattern not found. Using white color override as fallback.") # Basic logging
                    white_color = Color(255, 255, 255)
                    ogs.SetProjectionLineColor(white_color)
                    ogs.SetCutLineColor(white_color)
                    ogs.SetProjectionLineWeight(1)
                    ogs.SetCutLineWeight(1)

                # Hide Surface and Cut Patterns for clarity
                ogs.SetSurfacePatternsVisible(False)
                ogs.SetCutPatternsVisible(False)
                # Ensure Halftone is not set
                ogs.SetHalftone(False)

                # --- Apply Filter and Overrides ---
                # Transaction handled externally
                try:
                    # Check if filter is applicable to the view (category must be visible)
                    if active_view.IsFilterApplicable(filter_id_to_apply):
                        # Check if filter is already added to the view
                        applied_filters = active_view.GetFilters()
                        if filter_id_to_apply not in applied_filters:
                             active_view.AddFilter(filter_id_to_apply) # Requires transaction

                        # Apply overrides and ensure filter is visible (active)
                        active_view.SetFilterOverrides(filter_id_to_apply, ogs) # Requires transaction
                        active_view.SetFilterVisibility(filter_id_to_apply, True) # Requires transaction
                    else:
                         print("Warning: Filter '{}' is not applicable to the current view (category might be hidden).".format(filter_name)) # Basic logging

                except Exception as e_apply:
                    # Log application error externally
                    print("Error applying filter/overrides: {}".format(e_apply)) # Basic logging
                    pass # Error applying filter/overrides
            else:
                 print("Error: Could not find or create the filter '{}'.".format(filter_name)) # Basic logging
        else:
             print("Error: Failed to create one or both filter rules.") # Basic logging
    else:
        # Basic logging for missing elements
        if system_type_id == ElementId.InvalidElementId: print("Error: PipingSystemType '{}' not found.".format(system_type_name))
        if target_category_id == ElementId.InvalidElementId: print("Error: Target category ID is invalid.") # Should not happen with BuiltInCategory
        if sys_type_param_id == ElementId.InvalidElementId: print("Error: System Type Parameter ID is invalid.") # Should not happen with BuiltInParameter
        if elevation_param_id == ElementId.InvalidElementId: print("Error: Elevation Parameter ID is invalid.") # Should not happen with BuiltInParameter
else:
     # Basic logging for invalid view
     if not active_view: print("Error: No active view found.")
     elif not isinstance(active_view, View): print("Error: Active document is not a View.")
     elif not active_view.AreGraphicsOverridesAllowed(): print("Error: Graphics Overrides are not allowed in the active view.")