# Purpose: This script creates/updates a Revit filter to highlight poorly insulated exterior walls.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for List and Exceptions
clr.AddReference('System.Collections') # Required for List

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
    Color,
    FillPatternElement,
    FillPatternTarget,
    View,
    ElementParameterFilter,
    Category,
    ParameterFilterUtilities # For potential future checks
)

# --- Configuration ---
filter_name = "Poorly Insulated Exterior Walls"
target_category_id = ElementId(BuiltInCategory.OST_Walls)
thermal_resistance_threshold = 3.0 # R-value threshold (assuming Imperial units: (h·ft²·°F)/Btu)
target_function_value = 0 # Integer value for WallFunction.Exterior enum
override_pattern_name = "Diagonal Crosshatch" # Name of the desired fill pattern
override_color = Color(255, 0, 0) # Red color

# --- Get Active View ---
active_view = doc.ActiveView
valid_view = False
if active_view and isinstance(active_view, View) and not active_view.IsTemplate:
    # Check if the view type supports filters
    if active_view.AreGraphicsOverridesAllowed():
        valid_view = True
    else:
        print("# Error: The active view '{{}}' (Type: {{}}) does not support graphic overrides.".format(active_view.Name, active_view.ViewType))
else:
    print("# Error: No active graphical view found, the active 'view' is not a valid View element, or it is a view template.")

# --- Proceed only if view is valid ---
if valid_view:
    # --- Find Fill Pattern ---
    fill_pattern_id = ElementId.InvalidElementId
    pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    found_pattern = None
    for pattern in pattern_collector:
        if pattern.Name == override_pattern_name:
            # Surface patterns are typically Model patterns
            fp = pattern.GetFillPattern()
            if fp and fp.Target == FillPatternTarget.Model:
                found_pattern = pattern
                break # Found the first model pattern with the name

    if found_pattern:
        fill_pattern_id = found_pattern.Id
        print("# Found Fill Pattern: '{{}}' (ID: {{}})".format(override_pattern_name, fill_pattern_id))
    else:
        # Attempt to find a Drafting pattern if Model pattern wasn't found
        for pattern in pattern_collector:
             if pattern.Name == override_pattern_name:
                fp = pattern.GetFillPattern()
                if fp and fp.Target == FillPatternTarget.Drafting:
                     found_pattern = pattern
                     print("# Warning: Found Drafting pattern '{{}}' instead of Model pattern. Using it.".format(override_pattern_name))
                     break
        if found_pattern:
             fill_pattern_id = found_pattern.Id
        else:
             print("# Error: Fill pattern named '{{}}' not found in the document. Cannot set pattern override.".format(override_pattern_name))
             # Script will continue, but pattern override won't be set correctly

    # --- Prepare Filter Categories ---
    category_ids = List[ElementId]()
    category_ids.Add(target_category_id)

    # Basic sanity check for category existence
    wall_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Walls)
    if not wall_cat:
        print("# Error: Wall category (OST_Walls) not found in the document.")
        valid_view = False # Stop processing

if valid_view:
    # --- Prepare Filter Rules ---
    rules = List[FilterRule]()
    rules_ok = True

    # Rule 1: Function == Exterior (Value 0)
    try:
        function_param_id = ElementId(BuiltInParameter.FUNCTION_PARAM)
        # Optional: Verify parameter filterability
        # filterable_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, category_ids)
        # if function_param_id not in filterable_params:
        #     print("# Error: Function parameter is not filterable for Walls.")
        #     rules_ok = False

        if rules_ok:
            rule1 = ParameterFilterRuleFactory.CreateEqualsRule(function_param_id, target_function_value)
            rules.Add(rule1)
    except SysException as e:
        print("# Error creating Function filter rule: {}".format(e))
        rules_ok = False

    # Rule 2: Thermal Resistance (R) < threshold
    if rules_ok:
        try:
            thermal_param_id = ElementId(BuiltInParameter.THERMAL_RESISTANCE_PARAM)
            # Optional: Verify parameter filterability
            # if thermal_param_id not in filterable_params: # Uncomment if filterable_params check is enabled above
            #     print("# Error: Thermal Resistance (R) parameter is not filterable for Walls.")
            #     rules_ok = False

            if rules_ok:
                rule2 = ParameterFilterRuleFactory.CreateLessRule(thermal_param_id, thermal_resistance_threshold)
                rules.Add(rule2)
        except SysException as e:
            print("# Error creating Thermal Resistance filter rule: {}".format(e))
            rules_ok = False

    if rules_ok and rules.Count == 2:
        # --- Create ElementParameterFilter (implicitly ANDs the rules) ---
        element_filter = None
        try:
            # The ElementParameterFilter constructor takes the list of rules and implies AND logic
            element_filter = ElementParameterFilter(rules)
        except SysException as ef_e:
            print("# Error creating ElementParameterFilter: {}".format(ef_e))
            rules_ok = False # Stop if filter logic cannot be created

    if rules_ok and element_filter:
        # --- Find or Create Filter Element ---
        filter_element = None
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        existing_filters = [f for f in collector if f.Name.Equals(filter_name, System.StringComparison.OrdinalIgnoreCase)]

        if existing_filters:
            filter_element = existing_filters[0]
            print("# Found existing filter definition: '{{}}' (ID: {{}}). Will update it.".format(filter_name, filter_element.Id))
            update_success = True
            # Update categories and rules for the existing filter
            try:
                current_cats = filter_element.GetCategories()
                if len(current_cats) != len(category_ids) or not all(c in current_cats for c in category_ids):
                     filter_element.SetCategories(category_ids)
                     print("# Updated categories for existing filter '{{}}'.".format(filter_name))
            except SysException as cat_update_e:
                 print("# Warning: Failed to update categories for existing filter '{{}}': {{}}".format(filter_name, cat_update_e))

            try:
                # For ElementParameterFilter based filters, use SetElementFilter
                filter_element.SetElementFilter(element_filter)
                print("# Updated rules for existing filter '{{}}'.".format(filter_name))
            except SysException as rules_e:
                print("# Error updating rules for filter '{{}}': {{}}".format(filter_name, rules_e))
                filter_element = None # Cannot proceed if rules fail to update
                update_success = False

            if not update_success:
                 filter_element = None

        else:
            # Create a new filter definition if not found
            try:
                 if ParameterFilterElement.IsNameUnique(doc, filter_name):
                     # Create using the ElementParameterFilter directly
                     filter_element = ParameterFilterElement.Create(doc, filter_name, category_ids, element_filter)
                     print("# Created new filter definition: '{{}}' (ID: {{}}).".format(filter_name, filter_element.Id))
                 else:
                    print("# Error: Filter name '{{}}' is already in use (but wasn't found directly).".format(filter_name))
                    filter_element = None

            except SysException as create_e:
                print("# Error creating ParameterFilterElement '{{}}': {{}}".format(filter_name, create_e))
                filter_element = None

        # Proceed only if filter element exists or was successfully created/updated
        if filter_element:
            filter_id = filter_element.Id

            # --- Define Override Settings ---
            override_settings = OverrideGraphicSettings()
            apply_overrides_to_view = True
            try:
                # Set Surface Pattern Color
                override_settings.SetSurfaceForegroundPatternColor(override_color)

                # Set Surface Pattern only if a valid pattern ID was found
                if fill_pattern_id != ElementId.InvalidElementId:
                    override_settings.SetSurfaceForegroundPatternId(fill_pattern_id)
                    override_settings.SetSurfaceForegroundPatternVisible(True)
                else:
                    print("# Info: Skipping surface pattern override as the pattern '{{}}' was not found.".format(override_pattern_name))
                    override_settings.SetSurfaceForegroundPatternVisible(False) # Ensure pattern is not shown if ID is invalid

                # Optional: Make transparent or set other overrides if needed
                # override_settings.SetSurfaceTransparency(50)

            except SysException as override_e:
                print("# Error defining override graphic settings: {{}}".format(override_e))
                apply_overrides_to_view = False

            if apply_overrides_to_view:
                # --- Apply Filter and Overrides to Active View ---
                try:
                    # Add the filter to the view if it's not already applied
                    if not active_view.IsFilterApplied(filter_id):
                        if active_view.CanApplyFilter(filter_id):
                             active_view.AddFilter(filter_id)
                             print("# Added filter '{{}}' to view '{{}}'.".format(filter_name, active_view.Name))
                        else:
                             print("# Error: Cannot add filter '{{}}' (ID: {{}}) to view '{{}}'. Check view compatibility.".format(filter_name, filter_id, active_view.Name))
                             apply_overrides_to_view = False
                    else:
                        print("# Filter '{{}}' was already applied to view '{{}}'.".format(filter_name, active_view.Name))

                    # Set the overrides for this specific filter within this view
                    if apply_overrides_to_view:
                        active_view.SetFilterOverrides(filter_id, override_settings)
                        print("# Applied/Updated overrides for filter '{{}}' in view '{{}}'.".format(filter_name, active_view.Name))

                        # Ensure the filter is enabled and visible
                        if not active_view.GetFilterVisibility(filter_id):
                            active_view.SetFilterVisibility(filter_id, True)
                        if not active_view.IsFilterEnabled(filter_id):
                            active_view.SetIsFilterEnabled(filter_id, True)

                except SysException as apply_e:
                    print("# Error applying filter or setting overrides in view '{{}}': {{}}".format(active_view.Name, apply_e))

        elif not filter_element:
             print("# Filter processing stopped because the filter definition could not be created or updated.")
    elif not rules_ok:
        print("# Filter processing stopped because filter rules could not be created or combined.")

# Final message if the initial view check failed
elif not valid_view:
    print("# Filter processing stopped due to invalid active view or category issue.")