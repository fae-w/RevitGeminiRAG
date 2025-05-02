# Purpose: This script creates or updates a Revit filter to hide specified levels in the active view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View, Level,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule,
    FilterStringRuleEvaluator, FilterStringEquals, FilterStringContains, # Import string evaluators if needed
    BuiltInParameter, ViewType
)
from Autodesk.Revit.Exceptions import ArgumentException

# --- Configuration ---
filter_name = "TEMP - Hide Levels Except Specific" # Use a temporary or specific name
target_level_names = ["Level 1", "Roof Level"]
case_sensitive_comparison = True # Set to False for case-insensitive comparison

# --- Main Script ---

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid project view or is a view template.")
# Check if the view type typically shows levels and supports filters
elif active_view.ViewType not in [ViewType.Elevation, ViewType.Section, ViewType.DraftingView, ViewType.Legend, ViewType.CeilingPlan, ViewType.FloorPlan]:
     print("# Warning: Active view type ('{}') might not display Levels effectively or fully support filters. Proceeding anyway.".format(active_view.ViewType))

# Proceed only if the view is valid
if active_view and isinstance(active_view, View) and not active_view.IsTemplate:

    # --- Find Target Levels (Optional but good practice to check) ---
    # This script proceeds assuming the levels exist, as per the prompt focus on applying the filter.
    # You could add checks here to ensure "Level 1" and "Roof Level" exist.
    # Example check (optional):
    # level_collector = FilteredElementCollector(doc).OfClass(Level)
    # found_levels = {lvl.Name: lvl.Id for lvl in level_collector if lvl.Name in target_level_names}
    # if len(found_levels) != len(target_level_names):
    #     print("# Warning: Not all target levels ('{}') were found in the project.".format("', '".join(target_level_names)))
    #     # Decide whether to proceed or stop based on requirements

    # --- Filter Definition ---
    categories = List[ElementId]()
    categories.Add(ElementId(BuiltInCategory.OST_Levels))

    # Rules: Select levels where Name is NOT "Level 1" AND Name is NOT "Roof Level"
    # Use BuiltInParameter.DATUM_TEXT for Level Name filtering
    param_id = ElementId(BuiltInParameter.DATUM_TEXT)

    filter_rules = List[FilterRule]()
    all_rules_valid = True

    for level_name_to_exclude in target_level_names:
        try:
            # Create a "not equals" rule for string values
            # API requires FilterStringRuleEvaluator for string rules
            # FilterStringEquals with inverted logic is NOT directly available via factory.
            # Using CreateEqualsRule and then inverting the final filter application or using NotEquals rule.
            # ParameterFilterRuleFactory.CreateNotEqualsRule seems appropriate here.
            rule = ParameterFilterRuleFactory.CreateNotEqualsRule(param_id, level_name_to_exclude, case_sensitive_comparison)
            filter_rules.Add(rule)
        except ArgumentException as ae:
            print("# Error creating filter rule for '{}' (ArgumentException): {} - Ensure parameter 'DATUM_TEXT' is valid for Levels.".format(level_name_to_exclude, ae.Message))
            all_rules_valid = False
            break # Stop if one rule fails
        except Exception as e:
            print("# Error creating filter rule for '{}': {}".format(level_name_to_exclude, e))
            all_rules_valid = False
            break # Stop if one rule fails

    if all_rules_valid and filter_rules.Count > 0:
        # Check if a filter with the same name already exists
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        new_filter_id = ElementId.InvalidElementId
        try:
            # Transaction is handled externally
            if existing_filter:
                print("# Filter named '{}' already exists. Updating existing filter rules and categories.".format(filter_name))
                try:
                    existing_filter.SetCategories(categories)
                    existing_filter.SetRules(filter_rules)
                    new_filter_id = existing_filter.Id
                    print("# Updated existing filter '{}'.".format(filter_name))
                except Exception as update_e:
                    print("# Error updating existing filter '{}': {}".format(filter_name, update_e))
                    new_filter_id = ElementId.InvalidElementId # Prevent proceeding if update fails
            else:
                # Create the Parameter Filter Element
                try:
                    new_filter = ParameterFilterElement.Create(doc, filter_name, categories, filter_rules)
                    new_filter_id = new_filter.Id
                    print("# Created new filter: '{}'".format(filter_name))
                except Exception as create_e:
                    print("# Error creating ParameterFilterElement: {}".format(create_e))

            if new_filter_id != ElementId.InvalidElementId:
                # --- Apply Filter to Active View ---
                try:
                    # Check if filter is already applied to the view
                    applied_filters = active_view.GetFilters()
                    if new_filter_id not in applied_filters:
                        active_view.AddFilter(new_filter_id)
                        print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                    else:
                        print("# Filter '{}' was already present in view '{}'.".format(filter_name, active_view.Name))

                    # Set the filter to be NOT visible (hides matching elements)
                    # Note: OverrideGraphicSettings are not needed for simple hiding
                    active_view.SetFilterVisibility(new_filter_id, False)
                    print("# Set filter '{}' to hide matching elements (Levels NOT named '{}') in view '{}'.".format(filter_name, "' or '".join(target_level_names), active_view.Name))

                except Exception as apply_e:
                    # Check for specific error related to V/G overrides support
                    if "View type does not support Visibility/Graphics Overrides" in str(apply_e) or \
                       "View type does not support filters" in str(apply_e): # Added check for filter support
                         print("# Error: The current view ('{}', type: {}) does not support Filters or Visibility/Graphics Overrides.".format(active_view.Name, active_view.ViewType))
                    else:
                         print("# Error applying filter visibility to view '{}': {}".format(active_view.Name, apply_e))
        except Exception as outer_e:
            # Catch errors during filter creation/update or applying to view
            print("# An error occurred during filter processing: {}".format(outer_e))
        finally:
            # Transaction commit/rollback handled externally
            pass
    elif not all_rules_valid:
         print("# Filter application aborted due to errors creating filter rules.")
    else:
         print("# No filter rules were generated (perhaps no target level names provided?). Filter not applied.")

# Else for initial view check handled above
elif not active_view or active_view.IsTemplate:
     # Error message already printed
     pass