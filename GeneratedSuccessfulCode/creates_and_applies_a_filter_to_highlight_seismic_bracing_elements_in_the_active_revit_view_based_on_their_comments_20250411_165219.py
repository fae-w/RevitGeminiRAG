# Purpose: This script creates and applies a filter to highlight seismic bracing elements in the active Revit view based on their comments.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory,
    OverrideGraphicSettings, Color, View, BuiltInParameter, ElementFilter
)

# Define Filter settings
filter_name = "Seismic Bracing"
target_category_id = ElementId(BuiltInCategory.OST_StructuralFraming)
# Use the BuiltInParameter for 'Comments'
comments_param_id = ElementId(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
comments_value_match = "Seismic Brace"
override_color = Color(255, 165, 0) # Orange

# Get the active view (assuming doc and uidoc are pre-defined)
active_view = doc.ActiveView

# Check if active_view is valid and not a template
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
else:
    # Define categories for the filter
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Define filter rule: Comments equals "Seismic Brace"
    # Ensure case-sensitive comparison matches Revit's behavior if needed.
    # ParameterFilterRuleFactory.CreateEqualsRule performs a case-sensitive comparison for strings.
    rule = ParameterFilterRuleFactory.CreateEqualsRule(comments_param_id, comments_value_match)

    # Wrap the rule in an ElementParameterFilter
    # The ElementParameterFilter constructor takes a FilterRule
    element_filter = ElementParameterFilter(rule)

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
         # print("# Using existing filter: '{{}}'".format(filter_name)) # Optional debug
    else:
        # Create the Parameter Filter Element if it doesn't exist
        # IMPORTANT: This creation requires an external Transaction.
        try:
            parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
            # print("# Created new filter: '{{}}'".format(filter_name)) # Optional debug
        except Exception as e:
            print("# Error creating filter '{{}}': {{}}. Might already exist or creation failed.".format(filter_name, e))


    if parameter_filter:
        # Define Override Graphic Settings
        override_settings = OverrideGraphicSettings()
        override_settings.SetProjectionLineColor(override_color)
        override_settings.SetCutLineColor(override_color)
        # Optional: Make lines solid if desired
        # solid_pattern_id = LinePatternElement.GetSolidPatternId()
        # override_settings.SetProjectionLinePatternId(solid_pattern_id)
        # override_settings.SetCutLinePatternId(solid_pattern_id)

        # Apply the filter to the active view
        # IMPORTANT: Adding/modifying filters requires an external Transaction.
        try:
            # Check if filter is already applied before adding
            if not active_view.IsFilterApplied(parameter_filter.Id):
                 active_view.AddFilter(parameter_filter.Id)
                 # print("# Added filter '{{}}' to the view.".format(filter_name)) # Optional debug

            # Set the overrides for the filter in the view
            active_view.SetFilterOverrides(parameter_filter.Id, override_settings)
            # print("# Successfully applied filter '{{}}' with overrides to active view.".format(filter_name)) # Optional debug
        except Exception as e:
            print("# Error applying filter or overrides to the view: {{}}".format(e))
    elif not existing_filter:
         # This case occurs if creation failed and filter didn't exist before
         print("# Filter '{{}}' could not be found or created.".format(filter_name))