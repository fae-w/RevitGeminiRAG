# Purpose: This script applies graphic overrides to elements matching a filter in the active Revit view.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory,
    OverrideGraphicSettings, View, BuiltInParameter, LinePatternElement, ElementFilter
)

# --- Configuration ---
filter_name = "Unistrut Elements"
target_category_id = ElementId(BuiltInCategory.OST_StructuralFraming)
# Use SYMBOL_NAME_PARAM which usually holds the Type Name
type_name_param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)
type_name_contains_value = "Unistrut"
# Specify the desired line pattern name (ensure this pattern exists in the project)
target_line_pattern_name = "Dash" # Example: use "Dash", "Hidden", "Solid", etc.

# --- Get Active View ---
active_view = doc.ActiveView

# Check if active_view is valid and not a template
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
else:
    # --- Find Line Pattern Element ID ---
    target_line_pattern_id = ElementId.InvalidElementId
    line_pattern_collector = FilteredElementCollector(doc).OfClass(LinePatternElement)
    for pattern_elem in line_pattern_collector:
        if pattern_elem.Name == target_line_pattern_name:
            target_line_pattern_id = pattern_elem.Id
            break

    if target_line_pattern_id == ElementId.InvalidElementId:
        print("# Error: Could not find Line Pattern named '{}' in the project.".format(target_line_pattern_name))
    else:
        # --- Define Filter Categories ---
        categories = List[ElementId]()
        categories.Add(target_category_id)

        # --- Define Filter Rule ---
        # Rule: Type Name (SYMBOL_NAME_PARAM) contains "Unistrut" (case-sensitive)
        # Use CreateContainsRule for string comparison
        rule = ParameterFilterRuleFactory.CreateContainsRule(type_name_param_id, type_name_contains_value, False) # False for case-sensitive

        # --- Create ElementParameterFilter ---
        element_filter = ElementParameterFilter(rule)

        # --- Check for Existing Filter ---
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        # --- Create or Get Filter Element ---
        parameter_filter = None
        if existing_filter:
            parameter_filter = existing_filter
            # print("# Using existing filter: '{}'".format(filter_name)) # Optional Debug
            # Optional: Consider updating the existing filter's rules/categories if necessary
            # existing_filter.SetCategories(categories)
            # existing_filter.SetElementFilter(element_filter)
            # Note: Modifying existing filter also requires a transaction
        else:
            # Create the Parameter Filter Element if it doesn't exist
            # IMPORTANT: This creation requires an external Transaction.
            try:
                # Check if the element filter is valid for parameter filter element
                if ParameterFilterElement.ElementFilterIsAcceptableForParameterFilterElement(doc, categories, element_filter):
                     parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                     # print("# Created new filter: '{}'".format(filter_name)) # Optional Debug
                else:
                     print("# Error: The defined filter rule is not acceptable for a ParameterFilterElement.")

            except Exception as e:
                print("# Error creating filter '{}': {}. Might already exist or creation failed.".format(filter_name, e))


        # --- Apply Filter and Overrides to View ---
        if parameter_filter:
            # Define Override Graphic Settings
            override_settings = OverrideGraphicSettings()
            # Set the projection line pattern
            override_settings.SetProjectionLinePatternId(target_line_pattern_id)
            # Optional: Set cut line pattern as well if needed
            # override_settings.SetCutLinePatternId(target_line_pattern_id)
            # Optional: Set line color if needed
            # override_settings.SetProjectionLineColor(Color(255, 0, 0)) # Red example

            # Apply the filter to the active view
            # IMPORTANT: Adding/modifying filters requires an external Transaction.
            try:
                # Check if filter is already applied before adding
                if not active_view.IsFilterApplied(parameter_filter.Id):
                    active_view.AddFilter(parameter_filter.Id)
                    # print("# Added filter '{}' to the view.".format(filter_name)) # Optional debug

                # Set the overrides for the filter in the view
                active_view.SetFilterOverrides(parameter_filter.Id, override_settings)
                # print("# Successfully applied filter '{}' with overrides to active view.".format(filter_name)) # Optional debug
            except Exception as e:
                print("# Error applying filter or overrides to the view: {}".format(e))
        elif not existing_filter:
            # This case occurs if creation failed and filter didn't exist before
             print("# Filter '{}' could not be found or created.".format(filter_name))