# Purpose: This script creates or updates a Revit filter and applies graphic overrides to a view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule, FilterStringRule, FilterStringEquals,
    BuiltInParameter, OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    ElementParameterFilter, LogicalAndFilter # Though LogicalAndFilter not strictly needed for one rule
)
from Autodesk.Revit.Exceptions import ArgumentException

# --- Helper function to find the Solid Fill pattern ---
def find_solid_fill_pattern(doc):
    """Finds the first solid fill drafting pattern element."""
    fill_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    for pattern_element in fill_patterns:
        if pattern_element is not None:
            try:
                pattern = pattern_element.GetFillPattern()
                # Check if pattern is valid, IsSolidFill is True, and target is Drafting
                if pattern and pattern.IsSolidFill and pattern.Target == FillPatternTarget.Drafting:
                    return pattern_element.Id
            except Exception:
                # Handle potential errors getting pattern details
                continue
    return ElementId.InvalidElementId

# --- Main Script ---

# Filter Definition
filter_name = "Electrical Fixtures - Emergency"
# Target category: Electrical Fixtures
target_category_id = ElementId(BuiltInCategory.OST_ElectricalFixtures)
# Target parameter: Comments (Instance parameter)
target_parameter_id = ElementId(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
# Target value: "Emergency" (case-sensitive)
parameter_value = "Emergency"
# Override color: Bright Yellow
override_color = Color(255, 255, 0)

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid graphical view or it's a view template.")
else:
    # Prepare categories list
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Create the filter rule
    filter_rule = None
    try:
        # Create a rule: Comments equals "Emergency" (case-sensitive string)
        str_evaluator = FilterStringEquals()
        filter_rule = ParameterFilterRuleFactory.CreateFilterRule(target_parameter_id, str_evaluator, parameter_value)
    except ArgumentException as ae:
         print("# Error creating filter rule (ArgumentException): {0} - Ensure parameter 'Comments' exists, is of type Text/String, and is applicable to Electrical Fixtures.".format(ae.Message))
    except Exception as e:
         print("# Error creating filter rule: {0}".format(e))

    if filter_rule:
        filter_rules = List[FilterRule]()
        filter_rules.Add(filter_rule)

        # Check if a filter with the same name already exists
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        new_filter_id = ElementId.InvalidElementId
        try:
            # Transaction managed externally
            if existing_filter:
                print("# Filter named '{0}' already exists. Using existing filter.".format(filter_name))
                new_filter_id = existing_filter.Id
                # Optional: Update existing filter's rules/categories if needed
                try:
                    # Check if categories or rules need updating
                    current_categories = existing_filter.GetCategories()
                    current_rules = existing_filter.GetRules() # Basic check

                    needs_category_update = True
                    if len(current_categories) == len(categories) and current_categories[0] == categories[0]: # Simple check for single category
                        needs_category_update = False

                    # Rudimentary rule check (better comparison is complex)
                    needs_rule_update = len(current_rules) != len(filter_rules)
                    # TODO: Add more robust rule comparison if necessary

                    if needs_category_update:
                        existing_filter.SetCategories(categories)
                        print("# Updated existing filter '{0}' categories.".format(filter_name))
                    if needs_rule_update:
                         existing_filter.SetRules(filter_rules)
                         print("# Updated existing filter '{0}' rules.".format(filter_name))
                    if not needs_category_update and not needs_rule_update:
                        print("# Existing filter '{0}' configuration matches. No update needed.".format(filter_name))

                except Exception as update_e:
                    print("# Error updating existing filter '{0}': {1}".format(filter_name, update_e))
                    new_filter_id = ElementId.InvalidElementId # Prevent proceeding if update fails
            else:
                # Create the Parameter Filter Element
                try:
                    new_filter = ParameterFilterElement.Create(doc, filter_name, categories, filter_rules)
                    new_filter_id = new_filter.Id
                    print("# Created new filter: '{0}'".format(filter_name))
                except Exception as create_e:
                    print("# Error creating ParameterFilterElement: {0}".format(create_e))

            if new_filter_id != ElementId.InvalidElementId:
                # Find solid fill pattern
                solid_fill_id = find_solid_fill_pattern(doc)
                if solid_fill_id == ElementId.InvalidElementId:
                    print("# Warning: Could not find a 'Solid fill' drafting pattern. Color override might not be fully visible without a pattern.")

                # --- Define Override Settings ---
                ogs = OverrideGraphicSettings()
                # Apply color to surface pattern (projection)
                ogs.SetSurfaceForegroundPatternColor(override_color)
                if solid_fill_id != ElementId.InvalidElementId:
                    ogs.SetSurfaceForegroundPatternVisible(True)
                    ogs.SetSurfaceForegroundPatternId(solid_fill_id)
                else:
                     ogs.SetSurfaceForegroundPatternVisible(False) # Hide if no pattern

                # Apply color to cut pattern
                ogs.SetCutForegroundPatternColor(override_color)
                if solid_fill_id != ElementId.InvalidElementId:
                     ogs.SetCutForegroundPatternVisible(True)
                     ogs.SetCutForegroundPatternId(solid_fill_id)
                else:
                     ogs.SetCutForegroundPatternVisible(False) # Hide if no pattern

                # --- Apply Filter and Overrides to Active View ---
                try:
                    # Check if filter is already applied to the view
                    applied_filters = active_view.GetFilters()
                    if new_filter_id not in applied_filters:
                        active_view.AddFilter(new_filter_id)
                        print("# Added filter '{0}' to view '{1}'.".format(filter_name, active_view.Name))
                    else:
                        print("# Filter '{0}' was already present in view '{1}'.".format(filter_name, active_view.Name))

                    # Set the overrides for the filter in the view
                    active_view.SetFilterOverrides(new_filter_id, ogs)
                    # Ensure the filter is enabled (visible)
                    active_view.SetFilterVisibility(new_filter_id, True)
                    print("# Applied graphic overrides for filter '{0}' in view '{1}'.".format(filter_name, active_view.Name))

                except Exception as apply_e:
                    # Check if the view supports V/G overrides before blaming the apply step
                    if not active_view.AreGraphicsOverridesAllowed():
                         print("# Error: The current view type ('{0}') does not support Visibility/Graphics Overrides.".format(active_view.ViewType))
                    else:
                         print("# Error applying filter or overrides to view '{0}': {1}".format(active_view.Name, apply_e))
        except Exception as outer_e:
            # Catch errors during filter creation/update or applying to view
            print("# An error occurred during filter processing: {0}".format(outer_e))
        finally:
            # Transaction commit/rollback handled externally
            pass
    else:
        # Error message already printed during rule creation attempt
        pass