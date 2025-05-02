# Purpose: This script creates and applies graphic override filters to the active Revit view to color code rooms based on their department parameter.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List, ICollection

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    ElementCategoryFilter,
    Category,
    ParameterFilterRuleFactory,
    FilterStringRule, # Specific rule type for strings
    FilterRule, # Base class for rules list
    BuiltInParameter,
    Color,
    FillPatternElement,
    FillPatternTarget,
    ParameterFilterUtilities # To check filterable categories and parameters
)
from Autodesk.Revit.Exceptions import ArgumentException # For potential errors

# --- Configuration ---
# Define the department-to-color mapping and filter names
department_colors = {
    "Office": {"Color": Color(0, 0, 255), "FilterName": "Room Dept - Office"},    # Blue
    "Circulation": {"Color": Color(0, 255, 0), "FilterName": "Room Dept - Circulation"}, # Green
    "Service": {"Color": Color(255, 255, 0), "FilterName": "Room Dept - Service"}     # Yellow
    # Add more mappings as needed
}
target_bic = BuiltInCategory.OST_Rooms
param_bip_to_try = BuiltInParameter.ROOM_DEPARTMENT # Try built-in first
param_name_to_find = "Department" # Fallback name if BIP doesn't work
param_id = ElementId.InvalidElementId # Initialize as invalid

# --- Helper function to find the Solid Fill pattern ---
def find_solid_fill_pattern(doc):
    """Finds the first solid fill pattern element."""
    fp_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_pattern_elem = next((fp for fp in fp_collector if fp.GetFillPattern().IsSolidFill), None)
    if solid_pattern_elem:
        return solid_pattern_elem.Id
    return ElementId.InvalidElementId

# --- Get Rooms Category ---
rooms_category = Category.GetCategory(doc, target_bic)
if rooms_category is None:
    print("# Error: Rooms category (OST_Rooms) not found in the document.")
    rooms_category_id = ElementId.InvalidElementId
else:
    rooms_category_id = rooms_category.Id

# --- Check if Category is Filterable ---
filterable_categories = ParameterFilterUtilities.GetAllFilterableCategories()
if rooms_category_id == ElementId.InvalidElementId or rooms_category_id not in filterable_categories:
    print("# Error: The 'Rooms' category (OST_Rooms) is not filterable or not found.")
    can_proceed = False
else:
    # --- Check if Parameter is Filterable for the Category ---
    categories_list_for_check = List[ElementId]([rooms_category_id])
    filterable_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories_list_for_check)

    # Try the BuiltInParameter first
    temp_param_id = ElementId(param_bip_to_try)
    if temp_param_id in filterable_params:
        param_id = temp_param_id
        print("# Using BuiltInParameter ROOM_DEPARTMENT (ID: {})".format(param_id))
    else:
        print("# Warning: BuiltInParameter ROOM_DEPARTMENT (ID: {}) not filterable for Rooms. Trying to find parameter by name: '{}'".format(temp_param_id, param_name_to_find))
        # If BIP failed, search by name
        found_param_id = ElementId.InvalidElementId
        room_collector = FilteredElementCollector(doc).OfCategory(target_bic).WhereElementIsNotElementType()
        elements_checked = 0
        element_search_limit = 10 # Limit search for efficiency

        for room in room_collector:
             if elements_checked >= element_search_limit:
                 print("# Reached element search limit ({}) for parameter discovery.".format(element_search_limit))
                 break
             param = room.LookupParameter(param_name_to_find)
             if param and param.Id in filterable_params:
                 found_param_id = param.Id
                 print("# Found filterable parameter by name: '{}' (ID: {}) on element {}".format(param_name_to_find, found_param_id, room.Id))
                 break
             elements_checked += 1

        if found_param_id != ElementId.InvalidElementId:
            param_id = found_param_id
        else:
            print("# Error: Could not find a filterable parameter named '{}' for the Rooms category.".format(param_name_to_find))
            param_id = ElementId.InvalidElementId

    # Set proceed flag based on finding a valid category and parameter
    can_proceed = (rooms_category_id != ElementId.InvalidElementId and param_id != ElementId.InvalidElementId)


# --- Main Processing Logic (if category and parameter are valid) ---
if can_proceed:
    # --- Find solid fill pattern ---
    solid_fill_id = find_solid_fill_pattern(doc)
    if solid_fill_id == ElementId.InvalidElementId:
        print("# Warning: Could not find a 'Solid fill' pattern. Overrides will be applied without fill pattern.")
        apply_fill = False
    else:
        apply_fill = True
        print("# Found Solid Fill Pattern ID: {}".format(solid_fill_id))

    # --- Get Active View ---
    active_view = doc.ActiveView
    if active_view is None or not active_view.IsValidObject:
        print("# Error: No active view found or the active view is invalid.")
        can_proceed = False
    elif not active_view.AreGraphicsOverridesAllowed():
        print("# Error: View '{}' (Type: {}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
        can_proceed = False

    if can_proceed:
        # --- Process each Department filter ---
        categories_for_filter = List[ElementId]()
        categories_for_filter.Add(rooms_category_id)

        existing_filters_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        existing_filters_map = {f.Name: f for f in existing_filters_collector}

        for dept_value, config in department_colors.items():
            filter_name = config["FilterName"]
            target_color = config["Color"]
            filter_element = None

            print("\n# --- Processing Department: '{}' ---".format(dept_value))

            # Create the filter rule: Department EQUALS dept_value
            filter_rule = None
            try:
                # Create the rule for string equality (case-sensitive by default)
                filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(param_id, dept_value)
            except ArgumentException as arg_ex:
                 param_name_for_error = param_name_to_find # Default
                 try:
                     param_elem = doc.GetElement(param_id)
                     if param_elem: param_name_for_error = param_elem.Name
                 except: pass
                 print("# Error creating filter rule for '{}' (ArgumentException): {} - Check parameter '{}' (ID: {}).".format(dept_value, arg_ex.Message, param_name_for_error, param_id))
                 continue # Skip to next department
            except Exception as rule_ex:
                print("# Error creating filter rule for '{}': {}".format(dept_value, rule_ex))
                continue # Skip to next department

            if filter_rule:
                filter_rules = List[FilterRule]()
                filter_rules.Add(filter_rule)

                # Find or Create Filter Element (Transaction managed externally)
                if filter_name in existing_filters_map:
                    filter_element = existing_filters_map[filter_name]
                    print("# Using existing filter: '{}'".format(filter_name))
                    # Optional: Update existing filter rules/categories if needed (outside scope of simple creation)
                    try:
                        current_categories = filter_element.GetCategories()
                        if rooms_category_id not in current_categories:
                            all_cats = List[ElementId](current_categories)
                            all_cats.Add(rooms_category_id)
                            filter_element.SetCategories(all_cats)
                            print("# Added Rooms category to existing filter '{}'".format(filter_name))
                        # Note: Checking/updating rules can be complex, skipping deep check for this example
                        # filter_element.SetRules(filter_rules) # Uncomment to force rule update
                    except Exception as update_ex:
                        print("# Warning: Could not update existing filter '{}': {}".format(filter_name, update_ex))

                else:
                    print("# Creating new filter: '{}'".format(filter_name))
                    try:
                        filter_element = ParameterFilterElement.Create(
                            doc,
                            filter_name,
                            categories_for_filter,
                            filter_rules
                        )
                        existing_filters_map[filter_name] = filter_element # Add to map for future reference if needed
                        print("# Filter '{}' created successfully.".format(filter_name))
                    except Exception as create_ex:
                        print("# Error creating filter '{}': {}".format(filter_name, create_ex))
                        filter_element = None # Ensure filter_element is None if creation failed

                # Apply Filter to Active View (if filter exists/was created)
                if filter_element is not None:
                    filter_id = filter_element.Id
                    try:
                        # Check if the filter is already added to the view
                        applied_filter_ids = active_view.GetFilters()
                        if filter_id not in applied_filter_ids:
                            active_view.AddFilter(filter_id)
                            print("# Filter '{}' added to view '{}'.".format(filter_name, active_view.Name))
                        else:
                            print("# Filter '{}' is already present in view '{}'.".format(filter_name, active_view.Name))

                        # Define the graphic overrides
                        override_settings = OverrideGraphicSettings()

                        # Set surface pattern (Projection) - Visible surfaces when looking at the model
                        override_settings.SetProjectionLineColor(target_color) # Optional
                        if apply_fill:
                            override_settings.SetSurfaceForegroundPatternVisible(True)
                            override_settings.SetSurfaceForegroundPatternId(solid_fill_id)
                            override_settings.SetSurfaceForegroundPatternColor(target_color)
                        else:
                            override_settings.SetSurfaceForegroundPatternVisible(False)

                        # Set cut pattern - Visible surfaces when the element is cut
                        override_settings.SetCutLineColor(target_color) # Optional
                        if apply_fill:
                            override_settings.SetCutForegroundPatternVisible(True)
                            override_settings.SetCutForegroundPatternId(solid_fill_id)
                            override_settings.SetCutForegroundPatternColor(target_color)
                        else:
                            override_settings.SetCutForegroundPatternVisible(False)

                        # Apply the overrides to the filter in the view
                        active_view.SetFilterOverrides(filter_id, override_settings)
                        # Ensure the filter is visible/active in the view
                        active_view.SetFilterVisibility(filter_id, True)
                        print("# Color override ({}) applied for filter '{}' in view '{}'.".format(dept_value, filter_name, active_view.Name))

                    except Exception as view_ex:
                        print("# Error applying filter/overrides for '{}' to view '{}': {}".format(filter_name, active_view.Name, view_ex))
                else:
                    print("# Filter '{}' could not be found or created. Cannot apply to view.".format(filter_name))
            else:
                # Error creating rule was already printed
                pass

# Final messages if initial checks failed
elif rooms_category_id == ElementId.InvalidElementId:
    print("# Cannot proceed: Rooms category not found or not filterable.")
elif param_id == ElementId.InvalidElementId:
    print("# Cannot proceed: Department parameter not found or not filterable.")
elif active_view is None or not active_view.IsValidObject or not active_view.AreGraphicsOverridesAllowed():
     # Error message already printed above
     pass

# print("# Script finished.") # Optional final message