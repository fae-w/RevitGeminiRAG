# Purpose: This script creates or updates a Revit filter to apply graphic overrides to load-bearing walls in the active view.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    LogicalOrFilter, ElementParameterFilter, FilterRule, ParameterFilterRuleFactory,
    OverrideGraphicSettings, View, BuiltInParameter, ElementFilter
)
# Autodesk.Revit.DB.Structure is not strictly needed if using ParameterFilterRuleFactory with BuiltInParameter
# from Autodesk.Revit.DB.Structure import StructuralWallUsage

# Define Filter settings
filter_name = "Load Bearing Walls"
target_category_id = ElementId(BuiltInCategory.OST_Walls)
structural_usage_param_id = ElementId(BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM)
line_weight = 5 # Define the desired heavy line weight (1-16)

# Get the active view (assuming doc and uidoc are pre-defined)
active_view = doc.ActiveView

# Check if active_view is valid and not a template
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
else:
    # Define categories for the filter
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Define filter rules: Structural Usage is Bearing (1) OR Shear (2)
    # Note: Enum values for StructuralWallUsage are: Bearing = 1, Shear = 2
    rule1 = ParameterFilterRuleFactory.CreateEqualsRule(structural_usage_param_id, 1) # Bearing
    rule2 = ParameterFilterRuleFactory.CreateEqualsRule(structural_usage_param_id, 2) # Shear

    # Wrap rules in ElementParameterFilter objects
    filter1 = ElementParameterFilter(rule1)
    filter2 = ElementParameterFilter(rule2)

    # Create a list of ElementFilter objects
    element_filters = List[ElementFilter]()
    element_filters.Add(filter1)
    element_filters.Add(filter2)

    # Combine the ElementFilter objects with OR logic
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
         parameter_filter = existing_filter
         # print("# Using existing filter: '{}'".format(filter_name)) # Optional debug
    else:
        # Create the Parameter Filter Element if it doesn't exist
        # IMPORTANT: This creation requires an external Transaction.
        try:
            parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter_combined)
            # print("# Created new filter: '{}'".format(filter_name)) # Optional debug
        except Exception as e:
            print("# Error creating filter '{}': {}. Might already exist or creation failed.".format(filter_name, e))


    if parameter_filter:
        # Define Override Graphic Settings
        override_settings = OverrideGraphicSettings()

        # Validate and set line weight
        if 1 <= line_weight <= 16:
             override_settings.SetCutLineWeight(line_weight)
             override_settings.SetProjectionLineWeight(line_weight)
        else:
             print("# Warning: Invalid line weight ({}), must be between 1 and 16. Using default.".format(line_weight))
             # Optionally set a default or skip setting the weight
             # override_settings.SetCutLineWeight(1)
             # override_settings.SetProjectionLineWeight(1)

        # Apply the filter to the active view
        # IMPORTANT: Adding/modifying filters requires an external Transaction.
        try:
            # Check if filter is already applied before adding
            applied_filters = active_view.GetFilters()
            if parameter_filter.Id not in applied_filters:
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