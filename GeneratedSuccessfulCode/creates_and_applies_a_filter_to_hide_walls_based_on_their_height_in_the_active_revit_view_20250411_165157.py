# Purpose: This script creates and applies a filter to hide walls based on their height in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View, Wall,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule,
    BuiltInParameter, OverrideGraphicSettings,
    UnitUtils
)
# Attempt to import newer unit classes, handle fallback
try:
    from Autodesk.Revit.DB import ForgeTypeId
    from Autodesk.Revit.DB import UnitTypeId
    use_forge_type_id = True
except ImportError:
    from Autodesk.Revit.DB import DisplayUnitType
    use_forge_type_id = False

from Autodesk.Revit.Exceptions import ArgumentException

# --- Configuration ---
filter_height_mm = 4000.0
# Filter name indicating what it SELECTS (walls <= 4000mm), action is applied in view settings
filter_name = "Walls <= {}mm Height".format(int(filter_height_mm))

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid project view or is a view template.")
else:
    # Check if view supports filters/overrides
    view_supports_filters = True
    try:
        # Attempt a harmless check like getting existing filters
        _ = active_view.GetFilters()
    except Exception as e:
         # Check specific error message indicating lack of support
         if "does not support Visibility/Graphics Overrides" in str(e) or \
            "doesn't support filters" in str(e): # Add potential variations
              print("# Error: The current view ('{}', type: {}) does not support Visibility/Graphics Overrides/Filters.".format(active_view.Name, active_view.ViewType))
              view_supports_filters = False # Prevent proceeding
         else:
              # Log unexpected error but attempt to continue
              print("# Warning: Unexpected error checking view capabilities: {}. Proceeding cautiously.".format(e))

    if view_supports_filters:
        # --- Filter Definition ---
        target_category_id = ElementId(BuiltInCategory.OST_Walls)
        categories = List[ElementId]()
        categories.Add(target_category_id)

        # Parameter: Unconnected Height (WALL_USER_HEIGHT_PARAM)
        # This parameter represents the 'Unconnected Height' property of a wall.
        # Ensure this is the correct parameter for the walls being filtered.
        param_id = ElementId(BuiltInParameter.WALL_USER_HEIGHT_PARAM)

        # Convert height threshold to internal units (feet)
        value_internal_units = None
        try:
            if use_forge_type_id:
                 value_internal_units = UnitUtils.ConvertToInternalUnits(filter_height_mm, UnitTypeId.Millimeters)
            else:
                 value_internal_units = UnitUtils.ConvertToInternalUnits(filter_height_mm, DisplayUnitType.DUT_MILLIMETERS)
        except Exception as conv_e:
            print("# Error converting units: {}".format(conv_e))
            # Set to None to prevent proceeding if conversion fails
            value_internal_units = None

        filter_rule = None
        if value_internal_units is not None:
            try:
                # Create a "less than or equal to" rule.
                # This filter will match walls that are NOT taller than the threshold.
                # We will then hide these matched elements in the view settings.
                filter_rule = ParameterFilterRuleFactory.CreateLessOrEqualRule(param_id, value_internal_units)
            except ArgumentException as ae:
                print("# Error creating filter rule (ArgumentException): {} - Ensure parameter '{}' exists and is applicable to Walls.".format(ae.Message, "WALL_USER_HEIGHT_PARAM"))
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
                # Transaction is handled externally by the C# wrapper
                if existing_filter:
                    print("# Filter named '{}' already exists. Updating and using existing filter.".format(filter_name))
                    new_filter_id = existing_filter.Id
                    # Update existing filter's rules/categories to ensure they match the request
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
                    # --- Apply Filter to Active View & Set Visibility ---
                    try:
                        # Check if filter is already applied to the view
                        applied_filters = active_view.GetFilters()
                        if new_filter_id not in applied_filters:
                            active_view.AddFilter(new_filter_id)
                            print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                        else:
                            print("# Filter '{}' was already present in view '{}'.".format(filter_name, active_view.Name))

                        # Set the filter to HIDE matching elements (walls <= threshold)
                        active_view.SetFilterVisibility(new_filter_id, False)

                        # Optional: Clear any graphic overrides to ensure only visibility is affected
                        active_view.SetFilterOverrides(new_filter_id, OverrideGraphicSettings())

                        print("# Set filter '{}' visibility to OFF (Hidden) in view '{}'.".format(filter_name, active_view.Name))
                        print("# Result: Walls matching the filter (<= {}mm) are hidden, effectively showing only walls TALLER than {}mm.".format(int(filter_height_mm), int(filter_height_mm)))

                    except Exception as apply_e:
                        print("# Error applying filter settings to view '{}': {}".format(active_view.Name, apply_e))
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