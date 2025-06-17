# Purpose: This script hides non-structural columns in the active Revit view using a parameter filter.

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
    BuiltInParameter, # Ensure this is imported
    OverrideGraphicSettings
)
# Import necessary .NET classes
from System.Collections.Generic import List

# Define Filter settings
filter_name = "Non-Structural Columns"
target_category_id = ElementId(BuiltInCategory.OST_Columns) # Architectural Columns

# Parameter to check: COLUMN_IS_STRUCTURAL (for OST_Columns)
# Ensure BuiltInParameter is correctly imported and the member exists
try:
    structural_param_bip = BuiltInParameter.COLUMN_IS_STRUCTURAL
except AttributeError:
    print("# Error: BuiltInParameter.COLUMN_IS_STRUCTURAL not found. Check Revit API version or parameter name.")
    structural_param_id = ElementId.InvalidElementId # Set to invalid to prevent further errors
else:
    structural_param_id = ElementId(structural_param_bip)

parameter_value_false = 0 # 0 represents False/No for Yes/No parameters

# Get the active view (assume 'doc' is pre-defined)
active_view = doc.ActiveView

# Proceed only if the parameter ID is valid and we have a valid active view
if structural_param_id != ElementId.InvalidElementId:
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
        print("# Error: No active graphical view found or active view is a template.")
    else:
        # Define categories for the filter
        categories = List[ElementId]()
        categories.Add(target_category_id)
        # Note: To include Structural Columns (OST_StructuralColumns), add its category ID
        # and potentially adjust the filter rule or create a separate filter, as they
        # might use a different parameter (e.g., INSTANCE_STRUCTURAL_PARAM).

        # Define filter rule: Structural parameter is False (unchecked)
        # Use CreateEqualsRule for integer comparison (0 for False)
        # Ensure the parameter ID is valid before creating the rule
        rule = ParameterFilterRuleFactory.CreateEqualsRule(structural_param_id, parameter_value_false)

        # Wrap the rule(s) in an ElementParameterFilter
        # CreateEqualsRule returns a FilterRule. ElementParameterFilter needs IList<FilterRule> or a single FilterRule.
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
            # Apply the filter to the active view and hide elements
            # IMPORTANT: Adding/modifying filters requires an external Transaction.
            try:
                # Check if filter is already applied before adding
                applied_filters = active_view.GetFilters()
                if parameter_filter.Id not in applied_filters:
                     active_view.AddFilter(parameter_filter.Id)
                     # print("# Added filter '{}' to the view.".format(filter_name)) # Debug removed

                # Set the visibility for the filter in the view to False (Hide)
                if active_view.IsFilterEnabled(parameter_filter.Id): # Check if enabled before setting visibility
                    active_view.SetFilterVisibility(parameter_filter.Id, False)
                    # print("# Successfully set filter '{}' to hidden in active view.".format(filter_name)) # Debug removed

                # Optional: Ensure no graphic overrides interfere if only visibility is desired
                # This clears any existing overrides for this filter on this view
                active_view.SetFilterOverrides(parameter_filter.Id, OverrideGraphicSettings())

            except Exception as e:
                print("# Error applying filter or setting visibility to the view: {}".format(e))
        elif not existing_filter:
             # This case occurs if creation failed and filter didn't exist before
             print("# Filter '{}' could not be found or created.".format(filter_name))
# The initial check for structural_param_id handles the case where the BIP was not found.