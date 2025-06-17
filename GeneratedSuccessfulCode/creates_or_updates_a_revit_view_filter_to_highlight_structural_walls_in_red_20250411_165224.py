# Purpose: This script creates or updates a Revit view filter to highlight structural walls in red.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    LogicalOrFilter, ElementParameterFilter, FilterRule, ParameterFilterRuleFactory,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget, View,
    BuiltInParameter, ElementFilter # Added ElementFilter
)

# Define Filter settings
filter_name = "Structural Walls - Cut"
target_category_id = ElementId(BuiltInCategory.OST_Walls)
structural_usage_param_id = ElementId(BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM)
red_color = Color(255, 0, 0)

# Get the active view (assuming doc is pre-defined)
active_view = doc.ActiveView

# Check if active_view is valid and not a template
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
else:
    # Find the "Solid fill" pattern ElementId
    solid_fill_pattern_id = ElementId.InvalidElementId
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    for pattern_elem in fill_pattern_collector:
        fill_pattern = pattern_elem.GetFillPattern()
        # Check if pattern is not null and is solid fill
        if fill_pattern and fill_pattern.IsSolidFill:
            solid_fill_pattern_id = pattern_elem.Id
            break # Found the first solid fill pattern

    if solid_fill_pattern_id == ElementId.InvalidElementId:
        print("# Error: Could not find a 'Solid fill' pattern in the project.")
    else:
        # Define categories for the filter
        categories = List[ElementId]()
        categories.Add(target_category_id)

        # Define filter rules: Structural Usage is Bearing (1) OR Shear (2) OR StructuralCombined (3)
        rule1 = ParameterFilterRuleFactory.CreateEqualsRule(structural_usage_param_id, 1) # Bearing
        rule2 = ParameterFilterRuleFactory.CreateEqualsRule(structural_usage_param_id, 2) # Shear
        rule3 = ParameterFilterRuleFactory.CreateEqualsRule(structural_usage_param_id, 3) # StructuralCombined

        # Wrap rules in ElementParameterFilter objects
        filter1 = ElementParameterFilter(rule1)
        filter2 = ElementParameterFilter(rule2)
        filter3 = ElementParameterFilter(rule3)

        # Create a list of ElementFilter objects (NOT FilterRule)
        element_filters = List[ElementFilter]()
        element_filters.Add(filter1)
        element_filters.Add(filter2)
        element_filters.Add(filter3)

        # Combine the ElementFilter objects with OR logic
        # LogicalOrFilter constructor expects IList<ElementFilter>
        element_filter_combined = LogicalOrFilter(element_filters)

        # Check if a filter with the same name already exists
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        parameter_filter = None
        if existing_filter:
             # Use the existing filter if found.
             # Note: This script won't update its rules or categories if they differ.
             parameter_filter = existing_filter
             # print("# Using existing filter: {}".format(filter_name)) # Optional Debug
        else:
            # Create the Parameter Filter Element if it doesn't exist
            # IMPORTANT: This creation requires a Transaction, which is assumed to be handled externally.
            try:
                parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter_combined)
                # print("# Created new filter: {}".format(filter_name)) # Optional Debug
            except Exception as e:
                # Use standard string formatting compatible with IronPython 2.7
                print("# Error creating filter '{}': {}. It might already exist.".format(filter_name, e))


        if parameter_filter:
            # Define Override Graphic Settings
            override_settings = OverrideGraphicSettings()
            # Set cut pattern visibility, ID, and color
            override_settings.SetCutForegroundPatternVisible(True)
            override_settings.SetCutForegroundPatternId(solid_fill_pattern_id)
            override_settings.SetCutForegroundPatternColor(red_color)
            # Ensure background is not interfering
            override_settings.SetCutBackgroundPatternVisible(False)

            # Apply the filter to the active view
            # IMPORTANT: Adding/modifying filters requires a Transaction, assumed to be handled externally.
            try:
                # Check if filter is already applied before adding
                if not active_view.IsFilterApplied(parameter_filter.Id):
                     active_view.AddFilter(parameter_filter.Id)
                # Set the overrides for the filter in the view
                active_view.SetFilterOverrides(parameter_filter.Id, override_settings)
                # print("# Successfully applied filter '{}' with overrides to active view.".format(filter_name)) # Optional Debug
            except Exception as e:
                # Use standard string formatting compatible with IronPython 2.7
                print("# Error applying filter or overrides to the view: {}".format(e))
        elif not existing_filter:
             # This case occurs if creation failed and filter didn't exist before
             print("# Filter '{}' could not be found or created.".format(filter_name))