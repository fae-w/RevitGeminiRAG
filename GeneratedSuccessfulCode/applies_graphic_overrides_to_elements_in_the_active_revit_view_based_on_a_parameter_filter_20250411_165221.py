# Purpose: This script applies graphic overrides to elements in the active Revit view based on a parameter filter.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ParameterFilterElement,
    ElementId,
    ElementParameterFilter,
    FilterRule,
    ParameterFilterRuleFactory,
    View,
    BuiltInParameter,
    OverrideGraphicSettings
)
# Import necessary .NET classes
from System.Collections.Generic import List

# Define Filter settings
filter_name = "Steel Beams - Primary"
target_category_id = ElementId(BuiltInCategory.OST_StructuralFraming) # Category for beams
# Use the 'Type Comments' parameter
parameter_bip = BuiltInParameter.ALL_MODEL_TYPE_COMMENTS
parameter_value = "Primary Structure" # Text to check for containment
projection_line_weight = 5

# Get the active view (assume 'doc' is pre-defined)
active_view = doc.ActiveView

# Ensure the parameter exists before trying to use it
parameter_id = ElementId(parameter_bip)
if parameter_id == ElementId.InvalidElementId:
     print("# Error: BuiltInParameter.ALL_MODEL_TYPE_COMMENTS not found. Check Revit API version or parameter name.")
else:
    # Check if active_view is valid and not a template
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
        print("# Error: No active graphical view found or active view is a template.")
    else:
        # Define categories for the filter
        categories = List[ElementId]()
        categories.Add(target_category_id)

        # Define filter rule: 'Type Comments' contains 'Primary Structure'
        # CreateContainsRule needs ElementId, string value, and case sensitivity (optional, default false)
        rule = ParameterFilterRuleFactory.CreateContainsRule(parameter_id, parameter_value, False) # Case-insensitive

        # Wrap the rule(s) in an ElementParameterFilter
        filter_rules_list = List[FilterRule]()
        filter_rules_list.Add(rule)
        element_filter = ElementParameterFilter(filter_rules_list) # Use list constructor

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
             # print("# Using existing filter: '{}'".format(filter_name)) # Debug removed
        else:
            # Create the Parameter Filter Element if it doesn't exist
            # IMPORTANT: This creation requires an external Transaction.
            try:
                parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                # print("# Created new filter: '{}'".format(filter_name)) # Debug removed
            except Exception as e:
                print("# Error creating filter '{}': {}. Might already exist or creation failed.".format(filter_name, e))


        if parameter_filter:
            # Define Override Graphic Settings
            override_settings = OverrideGraphicSettings()
            # Set the projection line weight (valid range is 1-16)
            if 1 <= projection_line_weight <= 16:
                 override_settings.SetProjectionLineWeight(projection_line_weight)
            else:
                 print("# Warning: Invalid projection line weight ({}), must be between 1 and 16. Using default.".format(projection_line_weight))
                 # Optionally set a default or skip setting the weight
                 # override_settings.SetProjectionLineWeight(1) # Example default

            # Apply the filter to the active view
            # IMPORTANT: Adding/modifying filters requires an external Transaction.
            try:
                # Check if filter is already applied before adding
                applied_filters = active_view.GetFilters()
                if parameter_filter.Id not in applied_filters:
                     active_view.AddFilter(parameter_filter.Id)
                     # print("# Added filter '{}' to the view.".format(filter_name)) # Debug removed

                # Set the overrides for the filter in the view
                active_view.SetFilterOverrides(parameter_filter.Id, override_settings)
                # print("# Successfully applied filter '{}' with overrides to active view.".format(filter_name)) # Debug removed
            except Exception as e:
                print("# Error applying filter or overrides to the view: {}".format(e))
        elif not existing_filter:
             # This case occurs if creation failed and filter didn't exist before
             print("# Filter '{}' could not be found or created.".format(filter_name))