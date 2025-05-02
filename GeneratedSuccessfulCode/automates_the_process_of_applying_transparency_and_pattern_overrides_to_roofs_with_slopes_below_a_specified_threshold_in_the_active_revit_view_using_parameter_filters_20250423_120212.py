# Purpose: This script automates the process of applying transparency and pattern overrides to roofs with slopes below a specified threshold in the active Revit view using parameter filters.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for List and Exceptions
import math
from System import Exception as SysException
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    FilterRule,
    ParameterFilterRuleFactory,
    OverrideGraphicSettings,
    View,
    Category,
    ParameterFilterUtilities # For potential future checks
)
# Color might be needed if clearing patterns fully
# from Autodesk.Revit.DB import Color

# --- Configuration ---
filter_name = "Transparent Roofs"
slope_threshold_degrees = 5.0
target_transparency = 60
target_pattern_visibility = False # Turn patterns off (both foreground and background)

# --- Get Active View ---
# doc and uidoc are assumed pre-defined
active_view = doc.ActiveView
valid_view = False
if active_view and isinstance(active_view, View) and not active_view.IsTemplate:
    # Check if the view type supports filters (e.g., not a Schedule View, etc.)
    if active_view.AreGraphicsOverridesAllowed():
         valid_view = True
    else:
        print("# Error: The active view '{}' (Type: {}) does not support graphic overrides.".format(active_view.Name, active_view.ViewType))
else:
    print("# Error: No active graphical view found, the active 'view' is not a valid View element, or it is a view template.")

# --- Proceed only if view is valid ---
if valid_view:
    # --- Calculate Slope Threshold (Ratio) ---
    slope_threshold_ratio = None
    try:
        # ROOF_SLOPE parameter stores the slope as a unitless ratio (rise/run).
        # Handle potential vertical slope (tan(90) is undefined) or near vertical
        if abs(slope_threshold_degrees - 90.0) < 1e-9:
            slope_threshold_ratio = float('inf') # Effectively infinite slope ratio
        elif abs(slope_threshold_degrees + 90.0) < 1e-9:
             slope_threshold_ratio = float('-inf') # Though slope param usually positive
        else:
            slope_threshold_ratio = math.tan(math.radians(slope_threshold_degrees)) # Slope ratio tan(angle)
    except SysException as calc_e:
        print("# Error calculating slope threshold ratio: {}".format(calc_e))
        slope_threshold_ratio = None # Ensure it's None on error

    if slope_threshold_ratio is not None:
        # --- Prepare Filter Categories ---
        roof_category_id = ElementId(BuiltInCategory.OST_Roofs)
        category_ids = List[ElementId]()
        category_ids.Add(roof_category_id)

        # Check if the category exists (basic sanity check)
        roof_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Roofs)
        if not roof_cat:
            print("# Error: Roof category (OST_Roofs) not found in the document.")
        else:
            # --- Prepare Filter Rules ---
            slope_param_id = ElementId(BuiltInParameter.ROOF_SLOPE)

            # Optional: Verify if this parameter is filterable for the category
            # filterable_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, category_ids)
            # if slope_param_id not in filterable_params:
            #    print("# Error: The 'Slope' (ROOF_SLOPE) parameter is not filterable for the Roofs category.")
            # Assuming ROOF_SLOPE is generally filterable for roofs

            # Create the "less than" rule for the slope parameter
            filter_rule = None
            try:
                # ParameterFilterRuleFactory.CreateLessRule(parameterId, value)
                # The value should be the double representing the slope ratio
                filter_rule = ParameterFilterRuleFactory.CreateLessRule(slope_param_id, slope_threshold_ratio)
            except SysException as rule_e:
                print("# Error creating filter rule for Slope parameter ({}): {}".format(slope_param_id, rule_e))
                # This can happen if the parameter isn't applicable or filterable

            if filter_rule:
                rules = List[FilterRule]()
                rules.Add(filter_rule)

                # --- Find or Create Filter Element ---
                filter_element = None
                collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                # Case-insensitive comparison might be better in practice
                existing_filters = [f for f in collector if f.Name.Equals(filter_name, System.StringComparison.OrdinalIgnoreCase)]

                if existing_filters:
                    filter_element = existing_filters[0]
                    print("# Found existing filter definition: '{}' (ID: {}). Will update it.".format(filter_name, filter_element.Id))
                    update_success = True
                    # Update categories and rules for the existing filter
                    try:
                        current_cats = filter_element.GetCategories()
                        # Check if categories need update (simple count check first, then content)
                        if len(current_cats) != len(category_ids) or not all(c in current_cats for c in category_ids):
                             filter_element.SetCategories(category_ids)
                             print("# Updated categories for existing filter '{}'.".format(filter_name))
                    except SysException as cat_update_e:
                         print("# Warning: Failed to update categories for existing filter '{}': {}".format(filter_name, cat_update_e))
                         # Continue to try updating rules, but log the category issue

                    try:
                        filter_element.SetRules(rules)
                        print("# Updated rules for existing filter '{}'.".format(filter_name))
                    except SysException as rules_e:
                        print("# Error updating rules for filter '{}': {}".format(filter_name, rules_e))
                        filter_element = None # Cannot proceed if rules fail to update
                        update_success = False

                    if not update_success:
                         filter_element = None # Ensure it's None if update failed critically

                else:
                    # Create a new filter definition if not found
                    try:
                        filter_element = ParameterFilterElement.Create(doc, filter_name, category_ids)
                        filter_element.SetRules(rules) # Set rules after creation
                        print("# Created new filter definition: '{}' (ID: {}).".format(filter_name, filter_element.Id))
                    except SysException as create_e:
                        print("# Error creating ParameterFilterElement '{}': {}".format(filter_name, create_e))
                        filter_element = None # Ensure it's None if creation fails

                # Proceed only if filter element exists or was successfully created/updated
                if filter_element:
                    # --- Define Override Settings ---
                    override_settings = OverrideGraphicSettings()
                    apply_overrides_to_view = True
                    try:
                        override_settings.SetSurfaceTransparency(target_transparency)
                        # Set both foreground and background pattern visibility to False
                        override_settings.SetSurfaceForegroundPatternVisible(target_pattern_visibility)
                        override_settings.SetSurfaceBackgroundPatternVisible(target_pattern_visibility)

                        # Optional: Clear pattern IDs and colors if absolutely necessary to ensure no pattern shows
                        # override_settings.SetSurfaceForegroundPatternId(ElementId.InvalidElementId)
                        # override_settings.SetSurfaceBackgroundPatternId(ElementId.InvalidElementId)
                        # Requires Color import: from Autodesk.Revit.DB import Color
                        # override_settings.SetSurfaceForegroundPatternColor(Color.InvalidColorValue)
                        # override_settings.SetSurfaceBackgroundPatternColor(Color.InvalidColorValue)

                    except SysException as override_e:
                        print("# Error defining override graphic settings: {}".format(override_e))
                        apply_overrides_to_view = False # Don't try to apply invalid overrides

                    if apply_overrides_to_view:
                        filter_id = filter_element.Id
                        # --- Apply Filter and Overrides to Active View ---
                        try:
                            # Add the filter to the view if it's not already applied
                            if not active_view.IsFilterApplied(filter_id):
                                if active_view.CanApplyFilter(filter_id):
                                     active_view.AddFilter(filter_id)
                                     print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                                else:
                                     print("# Error: Cannot add filter '{}' (ID: {}) to view '{}'. Check view compatibility.".format(filter_name, filter_id, active_view.Name))
                                     apply_overrides_to_view = False # Cannot set overrides if filter cannot be added
                            else:
                                print("# Filter '{}' was already applied to view '{}'.".format(filter_name, active_view.Name))

                            # Set the overrides for this specific filter within this view, only if it could be added/was present
                            if apply_overrides_to_view:
                                active_view.SetFilterOverrides(filter_id, override_settings)
                                print("# Applied/Updated overrides for filter '{}' in view '{}' (Transparency: {}%, Patterns Visible: {}).".format(filter_name, active_view.Name, target_transparency, target_pattern_visibility))

                        except SysException as apply_e:
                            print("# Error applying filter or setting overrides in view '{}': {}".format(active_view.Name, apply_e))

                elif not filter_element:
                     print("# Filter processing stopped because the filter definition could not be created or updated.")
            else:
                 print("# Filter processing stopped because the filter rule could not be created.")
    else:
         print("# Filter processing stopped because the slope threshold could not be calculated.")
# No explicit sys.exit() needed, script finishes naturally or after printing errors.