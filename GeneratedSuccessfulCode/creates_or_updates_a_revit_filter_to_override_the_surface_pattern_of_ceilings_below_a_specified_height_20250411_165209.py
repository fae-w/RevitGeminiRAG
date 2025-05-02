# Purpose: This script creates or updates a Revit filter to override the surface pattern of ceilings below a specified height.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule,
    BuiltInParameter, OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    UnitUtils, ForgeTypeId, UnitTypeId # Corrected imports
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
    filter_name = "Ceilings Below 2400mm"
    target_category_id = ElementId(BuiltInCategory.OST_Ceilings)
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Rule: 'Height Offset From Level' < 2400mm
    param_id = ElementId(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM)

    # Convert 2400mm to internal units (feet)
    value_internal_units = None
    try:
        value_mm = 2400.0
        # Use ForgeTypeId (Revit 2021+ API) for unit conversion
        value_internal_units = UnitUtils.ConvertToInternalUnits(value_mm, UnitTypeId.Millimeters)
    except Exception as conv_e:
        print("# Error converting units: {}".format(conv_e))
        value_internal_units = None # Prevent proceeding

    filter_rule = None
    if value_internal_units is not None:
        try:
            # Create a "less than" rule for numeric values
            # Newer APIs (used here) do not need FilterNumericLessRuleValue
            filter_rule = ParameterFilterRuleFactory.CreateLessRule(param_id, value_internal_units)
        except ArgumentException as ae:
            print("# Error creating filter rule (ArgumentException): {} - Ensure parameter '{}' is valid for Ceilings.".format(ae.Message, "CEILING_HEIGHTABOVELEVEL_PARAM"))
        except Exception as e:
            print("# Error creating filter rule: {}".format(e))

    if filter_rule:
        filter_rules = List[FilterRule]() # Use the imported FilterRule base class
        filter_rules.Add(filter_rule)

        # --- Find Fill Pattern ---
        # Note: The exact name might vary in different Revit templates/projects.
        # Common names are "Diagonal crosshatch", "Crosshatch, diagonal". Adjust if needed.
        target_pattern_name = "Diagonal crosshatch"
        crosshatch_pattern_id = find_drafting_fill_pattern_by_name(doc, target_pattern_name)
        found_pattern_name = target_pattern_name # Store the name found

        if crosshatch_pattern_id == ElementId.InvalidElementId:
            # Attempt fallback name
            target_pattern_name_alt = "Crosshatch, diagonal"
            crosshatch_pattern_id = find_drafting_fill_pattern_by_name(doc, target_pattern_name_alt)
            if crosshatch_pattern_id != ElementId.InvalidElementId:
                 found_pattern_name = target_pattern_name_alt # Update found name
            else:
                 print("# Warning: Could not find a drafting fill pattern named '{}' or '{}'. Surface pattern override will not be applied.".format(target_pattern_name, target_pattern_name_alt))


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

                # Apply surface pattern override (if found)
                if crosshatch_pattern_id != ElementId.InvalidElementId:
                    ogs.SetSurfaceForegroundPatternVisible(True)
                    ogs.SetSurfaceForegroundPatternId(crosshatch_pattern_id)
                    # No color specified, keep default
                    # ogs.SetSurfaceForegroundPatternColor(Color(0,0,0)) # Example: Black
                    print("# Overrides will use surface pattern: '{}'".format(found_pattern_name))
                else:
                    ogs.SetSurfaceForegroundPatternVisible(False) # Ensure no pattern if not found


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
    elif value_internal_units is None:
         # Error message already printed during unit conversion
         pass
    else:
        # Error message already printed during rule creation attempt
        pass