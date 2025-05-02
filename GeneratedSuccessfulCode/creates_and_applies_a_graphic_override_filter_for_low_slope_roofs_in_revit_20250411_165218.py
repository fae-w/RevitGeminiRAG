# Purpose: This script creates and applies a graphic override filter for low slope roofs in Revit.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')
import math # For trigonometric functions

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule,
    BuiltInParameter, OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    UnitUtils, ForgeTypeId, UnitTypeId
)
from Autodesk.Revit.Exceptions import ArgumentException # Import for potential exception handling

# --- Helper function to find a drafting fill pattern by name ---
def find_drafting_fill_pattern_by_name(doc, pattern_name):
    """Finds the first drafting fill pattern element by name (case-insensitive)."""
    fill_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    pattern_name_lower = pattern_name.lower()
    for pattern_element in fill_patterns:
        if pattern_element is not None:
            try:
                pattern = pattern_element.GetFillPattern()
                # Check if pattern is not null, is a drafting pattern, and name matches
                if (pattern is not None and
                        pattern.Target == FillPatternTarget.Drafting and
                        pattern_element.Name.lower() == pattern_name_lower):
                    return pattern_element.Id
            except Exception:
                continue # Ignore patterns that cause errors
    return ElementId.InvalidElementId

# --- Main Script ---

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid project view or is a view template.")
else:
    # --- Filter Definition ---
    filter_name = "Low Slope Roofs"
    target_category_id = ElementId(BuiltInCategory.OST_Roofs)
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Rule: 'Slope' < 5 degrees
    # The ROOF_SLOPE parameter stores the slope as a unitless ratio (rise/run).
    # We need to convert 5 degrees to this ratio.
    param_id = ElementId(BuiltInParameter.ROOF_SLOPE)
    angle_degrees = 5.0
    try:
        angle_radians = math.radians(angle_degrees)
        value_ratio = math.tan(angle_radians) # Slope ratio tan(angle)
    except Exception as calc_e:
        print("# Error calculating slope ratio: {}".format(calc_e))
        value_ratio = None

    filter_rule = None
    if value_ratio is not None:
        try:
            # Create a "less than" rule for the numeric ratio
            filter_rule = ParameterFilterRuleFactory.CreateLessRule(param_id, value_ratio)
        except ArgumentException as ae:
            print("# Error creating filter rule (ArgumentException): {} - Ensure parameter '{}' is valid for Roofs.".format(ae.Message, "ROOF_SLOPE"))
        except Exception as e:
            print("# Error creating filter rule: {}".format(e))

    if filter_rule:
        filter_rules = List[FilterRule]() # Use the imported FilterRule base class
        filter_rules.Add(filter_rule)

        # --- Find Fill Pattern ---
        # Using "Vertical" as a distinct pattern. Adjust if needed.
        target_pattern_name = "Vertical"
        distinct_pattern_id = find_drafting_fill_pattern_by_name(doc, target_pattern_name)
        found_pattern_name = target_pattern_name # Store the name found

        if distinct_pattern_id == ElementId.InvalidElementId:
             print("# Warning: Could not find a drafting fill pattern named '{}'. Surface pattern override will not be applied.".format(target_pattern_name))

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
                print("# Filter named '{}' already exists. Using existing filter.".format(filter_name))
                new_filter_id = existing_filter.Id
                # Optional: Update existing filter's rules/categories if needed
                try:
                    existing_filter.SetCategories(categories)
                    existing_filter.SetRules(filter_rules)
                    print("# Updated existing filter '{}' categories and rules.".format(filter_name))
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
                # --- Define Override Settings ---
                ogs = OverrideGraphicSettings()
                green_color = Color(0, 255, 0)

                # Apply surface pattern override (if found)
                if distinct_pattern_id != ElementId.InvalidElementId:
                    ogs.SetSurfaceForegroundPatternVisible(True)
                    ogs.SetSurfaceForegroundPatternId(distinct_pattern_id)
                    ogs.SetSurfaceForegroundPatternColor(green_color) # Example: Green color
                    print("# Overrides will use surface pattern: '{}' with Green color.".format(found_pattern_name))
                else:
                    ogs.SetSurfaceForegroundPatternVisible(False) # Ensure no pattern if not found
                    # Optionally set a solid color even without pattern
                    # ogs.SetProjectionLineColor(green_color) # Or surface color if appropriate

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
                    # Check for specific error related to V/G overrides support
                    if "View type does not support Visibility/Graphics Overrides" in str(apply_e):
                         print("# Error: The current view ('{}', type: {}) does not support Visibility/Graphics Overrides.".format(active_view.Name, active_view.ViewType))
                    else:
                         print("# Error applying filter or overrides to view '{}': {}".format(active_view.Name, apply_e))
        except Exception as outer_e:
            # Catch errors during filter creation/update or applying to view
            print("# An error occurred during filter processing: {}".format(outer_e))
        finally:
            # Transaction commit/rollback handled externally
            pass
    elif value_ratio is None:
         # Error message already printed during slope calculation
         pass
    else:
        # Error message already printed during rule creation attempt
        pass