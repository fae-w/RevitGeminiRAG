# Purpose: This script highlights walls with specific fire ratings by creating and applying view filters.

﻿# Purpose: This script creates two view filters to highlight walls with specific 'Fire Rating' values ('120 minutes' or '2 hr')
#          by coloring their cut pattern solid orange in the active view.
# Note: Revit's API does not directly support creating a SINGLE ParameterFilterElement
#       with an OR condition between rules for the same parameter but different values.
#       Therefore, this script creates TWO separate filters to achieve the desired visual effect.

# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule, FilterStringRule, FilterStringEquals,
    BuiltInParameter, OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    ElementParameterFilter # May not be needed for creation, but good to have? No, not needed here.
    # LogicalAndFilter, LogicalOrFilter # Not applicable for ParameterFilterElement creation rules
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
                # Handle potential errors getting pattern details
                continue
    return ElementId.InvalidElementId

# --- Configuration ---
filter_name_base = "Fire Rated Walls"
fire_rating_values = ["120 minutes", "2 hr"] # Values to check for OR condition
# Assumption: The 'Fire Rating' parameter corresponds to the built-in parameter FIRE_RATING.
# If this is a shared or project parameter, this ID needs to be found differently.
target_parameter_id = ElementId(BuiltInParameter.FIRE_RATING)
target_category_id = ElementId(BuiltInCategory.OST_Walls)
override_color = Color(255, 165, 0) # Orange

# --- Main Script ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid graphical view or it's a view template.")
else:
    # Find solid fill pattern
    solid_fill_id = find_solid_fill_pattern(doc)
    if solid_fill_id == ElementId.InvalidElementId:
        print("# Warning: Could not find a 'Solid fill' drafting pattern. Color override might not be fully visible without a pattern.")

    # Prepare categories list (used for both filters)
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # --- Define Override Settings (used for both filters) ---
    ogs = OverrideGraphicSettings()
    # Apply color to cut pattern
    ogs.SetCutForegroundPatternColor(override_color)
    if solid_fill_id != ElementId.InvalidElementId:
        ogs.SetCutForegroundPatternVisible(True)
        ogs.SetCutForegroundPatternId(solid_fill_id)
    else:
        ogs.SetCutForegroundPatternVisible(False) # Hide if no pattern found

    # --- Process each fire rating value to create/update a filter ---
    created_or_updated_count = 0
    error_count = 0

    for value in fire_rating_values:
        # Construct filter name for this specific value
        filter_name = "{} - {}".format(filter_name_base, value.replace(" ", "")) # e.g., Fire Rated Walls - 120minutes

        # Create the filter rule for the current value
        filter_rule = None
        try:
            str_evaluator = FilterStringEquals()
            filter_rule = ParameterFilterRuleFactory.CreateFilterRule(target_parameter_id, str_evaluator, value)
        except ArgumentException as ae:
            print("# Error creating filter rule for value '{}' (ArgumentException): {} - Ensure parameter 'FIRE_RATING' exists, is Text/String, and applicable to Walls.".format(value, ae.Message))
            error_count += 1
            continue # Skip to next value if rule creation fails
        except Exception as e:
            print("# Error creating filter rule for value '{}': {}".format(value, e))
            error_count += 1
            continue # Skip to next value

        if filter_rule:
            filter_rules = List[FilterRule]()
            filter_rules.Add(filter_rule)

            # Check if a filter with this specific name already exists
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
                    # Optional: Update existing filter's rules/categories if needed (simple check)
                    try:
                        # Basic check: If categories or rules seem different, update them
                        current_categories = existing_filter.GetCategories()
                        current_rules = existing_filter.GetRules()

                        needs_category_update = True
                        if len(current_categories) == len(categories):
                            cat_set_current = set(c.IntegerValue for c in current_categories)
                            cat_set_new = set(c.IntegerValue for c in categories)
                            if cat_set_current == cat_set_new:
                                needs_category_update = False

                        # Simple rule check (assuming only one rule per filter here)
                        needs_rule_update = True
                        if len(current_rules) == len(filter_rules):
                             # Basic comparison based on string representation (might not be fully robust)
                             if str(current_rules[0]) == str(filter_rules[0]):
                                needs_rule_update = False


                        if needs_category_update:
                           existing_filter.SetCategories(categories)
                           print("# Updated existing filter '{}' categories.".format(filter_name))
                        if needs_rule_update:
                            existing_filter.SetRules(filter_rules)
                            print("# Updated existing filter '{}' rules.".format(filter_name))
                        if not needs_category_update and not needs_rule_update:
                             print("# Existing filter '{}' configuration matches. No update needed.".format(filter_name))
                        created_or_updated_count +=1


                    except Exception as update_e:
                        print("# Error updating existing filter '{}': {}".format(filter_name, update_e))
                        new_filter_id = ElementId.InvalidElementId # Prevent proceeding if update fails
                        error_count += 1

                else:
                    # Create the Parameter Filter Element
                    try:
                        new_filter = ParameterFilterElement.Create(doc, filter_name, categories, filter_rules)
                        new_filter_id = new_filter.Id
                        print("# Created new filter: '{}'".format(filter_name))
                        created_or_updated_count += 1
                    except Exception as create_e:
                        print("# Error creating ParameterFilterElement '{}': {}".format(filter_name, create_e))
                        error_count += 1

                # --- Apply Filter and Overrides to Active View ---
                if new_filter_id != ElementId.InvalidElementId:
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
                        print("# Error applying filter or overrides for '{}' to view '{}': {}".format(filter_name, active_view.Name, apply_e))
                        error_count += 1
            except Exception as outer_e:
                # Catch errors during filter creation/update or applying to view
                print("# An error occurred during processing for filter '{}': {}".format(filter_name, outer_e))
                error_count += 1
            finally:
                 # Transaction handled externally
                 pass
        else:
            # Error message already printed during rule creation attempt
             pass # error_count already incremented

    # Final summary
    if created_or_updated_count > 0:
        print("# Successfully created/updated and applied {} filter(s).".format(created_or_updated_count))
    if error_count > 0:
        print("# Encountered {} error(s) during the process.".format(error_count))
    if created_or_updated_count == 0 and error_count == 0:
        print("# No changes made. Filters might have already existed and matched criteria, or no applicable values processed.")