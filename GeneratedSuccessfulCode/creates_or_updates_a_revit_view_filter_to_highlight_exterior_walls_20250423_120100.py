# Purpose: This script creates or updates a Revit view filter to highlight exterior walls.

﻿# Purpose: Create or update a view filter to highlight walls with "Exterior" in their type name with a blue projection line color.

import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory, FilterStringRule, FilterStringContains, # Using FilterStringRule for text matching
    OverrideGraphicSettings, Color, View, BuiltInParameter, ParameterFilterUtilities
)
# Import .NET List
from System.Collections.Generic import List

# --- Configuration ---
filter_name = "Exterior Walls - Color"
target_category_id = ElementId(BuiltInCategory.OST_Walls)
filter_string_value = "Exterior" # The text to search for in the Type Name
override_color = Color(0, 0, 255) # Blue color

# --- Get Active View ---
active_view = doc.ActiveView

# Validate active view
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Requires an active, non-template graphical view.")
else:
    # --- Define Categories ---
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # --- Define Filter Rule ---
    # Get the parameter ElementId for Type Name (ALL_MODEL_TYPE_NAME)
    type_name_param_id = ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME)

    # Create the filter rule: Type Name contains "Exterior" (case-insensitive by default)
    # FilterStringContains is the evaluator class for this rule type
    # For Revit 2022+, use ParameterFilterRuleFactory directly. Older versions might need FilterStringRule constructor.
    try:
        # Modern approach (Revit 2019+)
        filter_rule = ParameterFilterRuleFactory.CreateContainsRule(type_name_param_id, filter_string_value)
    except AttributeError:
        # Fallback for potentially older API versions if ParameterFilterRuleFactory is missing CreateContainsRule
        # This assumes FilterStringRule exists and takes evaluator, value, case_sensitive args
        evaluator = FilterStringContains()
        case_sensitive = False # Default for CreateContainsRule is case-insensitive
        filter_rule = FilterStringRule(ParameterValueProvider(type_name_param_id), evaluator, filter_string_value, case_sensitive)


    # Create the ElementParameterFilter from the rule
    element_filter = ElementParameterFilter(filter_rule)

    # --- Check for Existing Filter ---
    existing_filter = None
    filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    for f in filter_collector:
        if f.Name == filter_name:
            existing_filter = f
            break

    parameter_filter = None
    if existing_filter:
        parameter_filter = existing_filter
        # Optional: Update existing filter's categories and rules if needed (requires transaction)
        # try:
        #     existing_filter.SetCategories(categories)
        #     existing_filter.SetElementFilter(element_filter)
        #     # print("# Updated existing filter: {}".format(filter_name)) # Escaped Optional
        # except Exception as update_err:
        #     print("# Warning: Failed to update existing filter '{}': {}".format(filter_name, update_err)) # Escaped
    else:
        # --- Create New Filter ---
        # IMPORTANT: This creation requires a Transaction, which is assumed to be handled externally.
        try:
            # Check if filter name is valid for creation (can sometimes fail if invalid chars exist)
             if ParameterFilterElement.IsNameUnique(doc, filter_name):
                 parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                 # print("# Created new filter: {}".format(filter_name)) # Escaped Optional
             else:
                 # This case should ideally be caught by the existence check, but added for safety
                 print("# Error: Filter name '{}' is already in use (but wasn't found directly).".format(filter_name)) # Escaped
        except Exception as e:
            print("# Error creating filter '{}': {}".format(filter_name, e)) # Escaped

    # --- Apply Filter and Overrides to View ---
    if parameter_filter:
        # Define Override Graphic Settings
        override_settings = OverrideGraphicSettings()
        override_settings.SetProjectionLineColor(override_color)
        # Optional: Set other overrides like pattern, line weight, etc. if needed
        # override_settings.SetProjectionLineWeight(5) # Example

        # Apply the filter to the active view
        # IMPORTANT: Adding/modifying filters requires a Transaction, assumed to be handled externally.
        try:
            # Check if the filter is already applied to the view
            applied_filters = active_view.GetFilters()
            if parameter_filter.Id not in applied_filters:
                active_view.AddFilter(parameter_filter.Id)
                # print("# Added filter '{}' to view '{}'".format(filter_name, active_view.Name)) # Escaped Optional

            # Set the overrides for the filter in the view
            active_view.SetFilterOverrides(parameter_filter.Id, override_settings)

            # Ensure the filter is enabled (might be added but disabled)
            if not active_view.GetFilterVisibility(parameter_filter.Id):
                 active_view.SetFilterVisibility(parameter_filter.Id, True) # VIsibility controls hide/show not enable/disable filter graphic override application
            if not active_view.IsFilterEnabled(parameter_filter.Id): # Check if filter overrides are enabled
                 active_view.SetIsFilterEnabled(parameter_filter.Id, True) # Enable filter overrides


            # print("# Applied overrides for filter '{}' in view '{}'".format(filter_name, active_view.Name)) # Escaped Optional

        except Exception as e:
            print("# Error applying filter or overrides to the view '{}': {}".format(active_view.Name, e)) # Escaped
    elif not existing_filter:
        # This case means creation failed and it didn't exist before
        print("# Filter '{}' could not be found or created.".format(filter_name)) # Escaped