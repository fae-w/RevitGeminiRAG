# Purpose: This script creates and applies a filter to hide unplaced rooms (area = 0) in the active Revit view.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    BuiltInParameter,
    Category,
    ParameterFilterRuleFactory,
    FilterDoubleRule,
    FilterRule,
    ElementParameterFilter,
    View,
    OverrideGraphicSettings
)

# --- Configuration ---
filter_name = "Unplaced Rooms"
target_bic = BuiltInCategory.OST_Rooms

# --- Get Room Category and Area Parameter ---
room_category = Category.GetCategory(doc, target_bic)
room_area_param_id = ElementId(BuiltInParameter.ROOM_AREA)

if room_category is None:
    print("# Error: Room category (OST_Rooms) not found in the document.")
    # Stop execution if the category doesn't exist
    parameter_filter = None
elif room_area_param_id == ElementId.InvalidElementId:
    print("# Error: Room Area parameter (ROOM_AREA) not found.")
    parameter_filter = None
else:
    room_category_id = room_category.Id
    parameter_filter = None

    # --- Find or Create Filter Element ---
    collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    for existing_filter in collector:
        if existing_filter.Name == filter_name:
            parameter_filter = existing_filter
            # print(f"# Using existing filter: '{filter_name}'") # Optional debug
            break

    if parameter_filter is None:
        # print(f"# Creating new filter: '{filter_name}'") # Optional debug
        # Define the categories the filter applies to
        categories_for_filter = List[ElementId]()
        categories_for_filter.Add(room_category_id)

        # Create the filter rule: Room Area equals 0.0
        # Use CreateEqualsRule for double comparison. Epsilon is needed for non-exact comparison,
        # but for exactly 0.0, a small epsilon or direct comparison might work.
        # Let's try CreateEqualsRule directly with 0.0 - assumes exact zero for unplaced.
        # If issues arise, ParameterFilterRuleFactory.CreateDoubleValueRule with FilterNumericEquals might be needed.
        try:
            # Testing with simple equals rule first. Area is double, so pass 0.0
            filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(room_area_param_id, 0.0)
        except Exception as rule_ex:
            # Fallback or alternative approach if needed, e.g., less than a small epsilon
            # filter_rule = ParameterFilterRuleFactory.CreateDoubleRule(room_area_param_id, FilterNumericLess(), 0.001, 1e-6) # Example: Area < 0.001
            print(f"# Warning: Could not create simple equals rule for Area=0.0 ({rule_ex}). Filter creation might fail.")
            filter_rule = None # Ensure it's None if rule creation failed

        if filter_rule:
            # Create the ElementParameterFilter from the rule
            # ElementParameterFilter constructor needs IList<FilterRule> or a single FilterRule
            element_filter = ElementParameterFilter(filter_rule)

            try:
                # Create the ParameterFilterElement (Transaction managed externally)
                parameter_filter = ParameterFilterElement.Create(
                    doc,
                    filter_name,
                    categories_for_filter,
                    element_filter
                )
                # print(f"# Filter '{filter_name}' created successfully.") # Optional debug
            except Exception as create_ex:
                print(f"# Error creating filter '{filter_name}': {create_ex}")
                parameter_filter = None # Ensure filter_element is None if creation failed
        else:
             print(f"# Could not create filter rule for filter '{filter_name}'.")


# --- Apply Filter to Active View ---
if parameter_filter is not None:
    filter_id = parameter_filter.Id
    active_view = doc.ActiveView

    if active_view is not None and active_view.IsValidObject:
        # Check if the view type supports filters/overrides
        if active_view.AreGraphicsOverridesAllowed():
            try:
                # Check if the filter is already added to the view
                applied_filter_ids = active_view.GetFilters()
                if filter_id not in applied_filter_ids:
                    # Add the filter to the view (Transaction managed externally)
                    active_view.AddFilter(filter_id)
                    # print(f"# Filter '{filter_name}' added to view '{active_view.Name}'.") # Optional debug

                # Define the graphic overrides (set visibility to False)
                override_settings = OverrideGraphicSettings()
                override_settings.SetVisibility(False)

                # Apply the overrides to the filter in the view (Transaction managed externally)
                active_view.SetFilterOverrides(filter_id, override_settings)
                # print(f"# 'Hide' override applied for filter '{filter_name}' in view '{active_view.Name}'.") # Optional debug

            except Exception as view_ex:
                print(f"# Error applying filter/overrides to view '{active_view.Name}': {view_ex}")
        else:
            print(f"# Error: View '{active_view.Name}' (Type: {active_view.ViewType}) does not support graphic overrides/filters.")
    else:
        print("# Error: No active view found or the active view is invalid.")
elif room_category is not None and room_area_param_id != ElementId.InvalidElementId: # Only print if category/param existed but filter failed
    print(f"# Filter '{filter_name}' could not be found or created. Cannot apply to view.")