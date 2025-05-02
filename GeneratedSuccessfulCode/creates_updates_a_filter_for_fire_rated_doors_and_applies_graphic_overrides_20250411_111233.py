# Purpose: This script creates/updates a filter for fire-rated doors and applies graphic overrides.

# Purpose: This script creates or updates a filter for 60-minute fire-rated doors in the active view and applies magenta-colored graphic overrides.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule, FilterStringRule, FilterStringEquals, # Explicit rule types
    BuiltInParameter, OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    ElementParameterFilter, LogicalAndFilter # Needed for filter creation/rule logic
)
from Autodesk.Revit.Exceptions import ArgumentException # Import for potential exception handling

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
                # Handle potential errors getting pattern details, though unlikely for standard patterns
                continue
    return ElementId.InvalidElementId

# --- Main Script ---

# Filter Definition
filter_name = "Fire Rated Doors - 60min"
# Assumption: The "Fire Rating" parameter corresponds to the built-in parameter DOOR_FIRE_RATING.
target_parameter_id = ElementId(BuiltInParameter.DOOR_FIRE_RATING)
# Assumption: The value to match is exactly "60 min" (case-sensitive string).
parameter_value = "60 min"
target_category_id = ElementId(BuiltInCategory.OST_Doors)
override_color = Color(255, 0, 255) # Magenta

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid graphical view or it's a view template.")
# Removed the incorrect 'CanApplyFilterOverrides' check here
else:
    # Prepare categories list
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Create the filter rule
    filter_rule = None
    try:
        # Create a rule: DOOR_FIRE_RATING equals "60 min"
        # Using the explicit FilterStringRule / FilterStringEquals
        str_evaluator = FilterStringEquals()
        filter_rule = ParameterFilterRuleFactory.CreateFilterRule(target_parameter_id, str_evaluator, parameter_value)
        # Note: Case sensitivity is handled by FilterStringEquals by default.
        # Alternative (potentially less robust for all string cases):
        # filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(target_parameter_id, parameter_value) # Might implicitly convert/fail for strings

    except ArgumentException as ae:
         print("# Error creating filter rule (ArgumentException): {} - Ensure parameter 'DOOR_FIRE_RATING' exists, is of type Text/String, and is applicable to Doors.".format(ae.Message))
    except Exception as e:
         print("# Error creating filter rule: {}".format(e))

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
                print("# Filter named '{}' already exists. Using existing filter.".format(filter_name))
                new_filter_id = existing_filter.Id
                # Optional: Update existing filter's rules/categories if needed
                try:
                    # Check if categories or rules need updating before attempting to set
                    current_categories = existing_filter.GetCategories()
                    current_rules = existing_filter.GetRules() # Note: Comparing rule lists requires careful logic
                    
                    needs_category_update = True # Assume update needed unless proven otherwise
                    if len(current_categories) == len(categories):
                         cat_set_current = set(c.IntegerValue for c in current_categories)
                         cat_set_new = set(c.IntegerValue for c in categories)
                         if cat_set_current == cat_set_new:
                             needs_category_update = False

                    # Simple rule count check (deep comparison is more complex)
                    needs_rule_update = len(current_rules) != len(filter_rules) # Add more sophisticated rule comparison if necessary

                    if needs_category_update:
                        existing_filter.SetCategories(categories)
                        print("# Updated existing filter '{}' categories.".format(filter_name))
                    if needs_rule_update: # Only update rules if they seem different
                         existing_filter.SetRules(filter_rules)
                         print("# Updated existing filter '{}' rules.".format(filter_name))
                    if not needs_category_update and not needs_rule_update:
                        print("# Existing filter '{}' configuration matches. No update needed.".format(filter_name))

                except Exception as update_e:
                    print("# Error updating existing filter '{}': {}".format(filter_name, update_e))
                    new_filter_id = ElementId.InvalidElementId # Prevent proceeding if update fails
            else:
                # Create the Parameter Filter Element
                try:
                    # Create takes name, categories, and the *rules* (not the logical filter)
                    # LogicalAndFilter is used when combining MULTIPLE rules, not needed for one rule.
                    new_filter = ParameterFilterElement.Create(doc, filter_name, categories, filter_rules)
                    new_filter_id = new_filter.Id
                    print("# Created new filter: '{}'".format(filter_name))
                except Exception as create_e:
                    print("# Error creating ParameterFilterElement: {}".format(create_e))

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
                     ogs.SetSurfaceForegroundPatternVisible(False) # Explicitly hide if no pattern found

                # Apply color to cut pattern
                ogs.SetCutForegroundPatternColor(override_color)
                if solid_fill_id != ElementId.InvalidElementId:
                     ogs.SetCutForegroundPatternVisible(True)
                     ogs.SetCutForegroundPatternId(solid_fill_id)
                else:
                     ogs.SetCutForegroundPatternVisible(False) # Explicitly hide if no pattern found

                # --- Apply Filter and Overrides to Active View ---
                try:
                    # Check if filter is already applied to the view
                    applied_filters = active_view.GetFilters()
                    if new_filter_id not in applied_filters:
                        active_view.AddFilter(new_filter_id)
                        print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                    else:
                        print("# Filter '{}' was already present in view '{}'.".format(filter_name, active_view.Name))

                    # Set the overrides for the filter in the view
                    active_view.SetFilterOverrides(new_filter_id, ogs)
                    # Ensure the filter is enabled (visible)
                    active_view.SetFilterVisibility(new_filter_id, True)
                    print("# Applied graphic overrides for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

                except Exception as apply_e:
                    print("# Error applying filter or overrides to view '{}': {}".format(active_view.Name, apply_e))
        except Exception as outer_e:
            # Catch errors during filter creation/update or applying to view
            print("# An error occurred during filter processing: {}".format(outer_e))
        finally:
            # Transaction commit/rollback handled externally
            pass
    else:
        # Error message already printed during rule creation attempt
        pass