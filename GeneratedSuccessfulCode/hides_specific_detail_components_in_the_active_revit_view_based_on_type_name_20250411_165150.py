# Purpose: This script hides specific detail components in the active Revit view based on type name.

﻿import clr
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

# --- Configuration ---
filter_name = "Hide Detail Items (Excl. Break Line)"
target_category_id = ElementId(BuiltInCategory.OST_DetailComponents)
# Parameter to filter by: Type Name
type_name_param_id = ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME)
# Value to check within the Type Name
exclude_string = "Break Line"
# Case sensitivity for the string check (False means case-insensitive)
case_sensitive = False
# --- End Configuration ---

# Get the active view
active_view = doc.ActiveView

# Proceed only if we have a valid active view that can have filters applied
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate or not active_view.AreGraphicsOverridesAllowed():
    print("# Error: No active graphical view found, active view is a template, or view does not allow overrides/filters.")
else:
    # Define categories for the filter
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Define filter rule: Type Name does NOT contain 'Break Line'
    # We want to select elements to hide, so we select those whose type name *doesn't* contain the exclusion string.
    try:
        # ParameterFilterRuleFactory.CreateNotContainsRule(paramId, stringValue, caseSensitive)
        rule = ParameterFilterRuleFactory.CreateNotContainsRule(type_name_param_id, exclude_string, case_sensitive)
    except Exception as e:
        print("# Error creating filter rule: {}. Check if the parameter exists.".format(e))
        rule = None

    if rule:
        # Wrap the rule in an ElementParameterFilter
        filter_rules_list = List[FilterRule]()
        filter_rules_list.Add(rule)
        element_filter = ElementParameterFilter(filter_rules_list) # Constructor takes IList<FilterRule>

        # Check if a filter with the same name already exists
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                # Optional: Check if existing filter matches criteria (categories, rules) - Skipped for simplicity
                break

        parameter_filter = None
        if existing_filter:
             parameter_filter = existing_filter
             # print("# Using existing filter: '{}'".format(filter_name)) # Debug removed
        else:
            # Create the Parameter Filter Element if it doesn't exist
            # IMPORTANT: This creation requires an external Transaction (assumed handled by C# wrapper).
            try:
                parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                # print("# Created new filter: '{}'".format(filter_name)) # Debug removed
            except Exception as e:
                print("# Error creating filter '{}': {}. Might already exist or creation failed.".format(filter_name, e))

        if parameter_filter:
            # Apply the filter to the active view and hide elements
            # IMPORTANT: Adding/modifying filters requires an external Transaction (assumed handled by C# wrapper).
            try:
                # Check if filter is already applied before adding
                applied_filters = active_view.GetFilters()
                if parameter_filter.Id not in applied_filters:
                     active_view.AddFilter(parameter_filter.Id)
                     # print("# Added filter '{}' to the view.".format(filter_name)) # Debug removed

                # Set the visibility for the filter in the view to False (Hide)
                # Elements matching the filter (Type Name NOT containing "Break Line") will be hidden.
                active_view.SetFilterVisibility(parameter_filter.Id, False)

                # Optional: Clear any graphic overrides to ensure only visibility is affected.
                active_view.SetFilterOverrides(parameter_filter.Id, OverrideGraphicSettings())

                # print("# Successfully applied filter '{}' to hide matching elements in active view.".format(filter_name)) # Debug removed

            except Exception as e:
                print("# Error applying filter or setting visibility to the view: {}".format(e))
        elif not existing_filter:
             # This case occurs if creation failed and filter didn't exist before
             print("# Filter '{}' could not be found or created.".format(filter_name))