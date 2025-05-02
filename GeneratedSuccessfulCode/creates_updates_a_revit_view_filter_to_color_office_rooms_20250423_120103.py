# Purpose: This script creates/updates a Revit view filter to color 'Office' rooms.

﻿# Purpose: Create or update a view filter to apply a solid green surface pattern fill to Rooms whose Name parameter includes 'Office'.

import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory, FilterStringRule, FilterStringContains, # Using FilterStringRule for text matching
    OverrideGraphicSettings, Color, View, BuiltInParameter, ParameterFilterUtilities,
    FillPatternElement, FillPatternTarget # Needed for fill patterns
)
# Import .NET List
from System.Collections.Generic import List

# --- Configuration ---
filter_name = "Office Rooms - Fill"
target_category_id = ElementId(BuiltInCategory.OST_Rooms)
parameter_to_check = BuiltInParameter.ROOM_NAME # Parameter to filter by
filter_string_value = "Office" # The text to search for in the Room Name
override_color = Color(0, 255, 0) # Green color
solid_fill_pattern_name = "<Solid fill>" # Revit's default name for the solid fill pattern

# --- Helper function to find Solid Fill Pattern ---
def find_solid_fill_pattern_id(doc_param):
    """Finds the ElementId of the 'Solid fill' pattern."""
    solid_pattern_id = ElementId.InvalidElementId
    # Collector for FillPatternElement
    collector = FilteredElementCollector(doc_param).OfClass(FillPatternElement)
    for pattern_elem in collector:
        try:
            # Get the FillPattern associated with the element
            pattern = pattern_elem.GetFillPattern()
            # Check if it's a solid fill pattern
            if pattern and pattern.IsSolidFill:
                 # Also check the target, often useful for distinguishing drafting/model
                 if pattern.Target == FillPatternTarget.Drafting: # Solid fill is usually a drafting pattern
                     solid_pattern_id = pattern_elem.Id
                     break
                 # Fallback if drafting solid fill not found, check any solid fill
                 elif solid_pattern_id == ElementId.InvalidElementId:
                      solid_pattern_id = pattern_elem.Id
                      # Don't break yet, prefer Drafting type if found later

        except Exception as e:
            # print("# Debug: Error accessing pattern info for element {}: {}".format(pattern_elem.Id, e)) # Escaped Optional
            pass # Ignore elements that might cause issues

    # Fallback: Try finding by exact name if the property check failed
    if solid_pattern_id == ElementId.InvalidElementId:
         pattern_elem_by_name = FilteredElementCollector(doc_param)\
                                 .OfClass(FillPatternElement)\
                                 .Where(lambda p: p.Name == solid_fill_pattern_name)\
                                 .FirstOrDefault()
         if pattern_elem_by_name:
             solid_pattern_id = pattern_elem_by_name.Id

    return solid_pattern_id

# --- Get Active View ---
active_view = doc.ActiveView

# Validate active view
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Requires an active, non-template graphical view.")
else:
    # --- Find Solid Fill Pattern ---
    solid_fill_id = find_solid_fill_pattern_id(doc)

    if solid_fill_id == ElementId.InvalidElementId:
        print("# Error: Could not find the 'Solid fill' pattern.")
    else:
        # --- Define Categories ---
        categories = List[ElementId]()
        categories.Add(target_category_id)

        # --- Define Filter Rule ---
        # Get the parameter ElementId for Room Name
        room_name_param_id = ElementId(parameter_to_check)

        # Check if the parameter ID is valid for the category
        valid_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories)
        if room_name_param_id not in valid_params:
             print("# Error: Parameter 'Room Name' (BuiltInParameter.ROOM_NAME) is not filterable for the 'Rooms' category.")
        else:
            # Create the filter rule: Room Name contains "Office" (case-insensitive by default)
            try:
                # Modern approach (Revit 2019+)
                filter_rule = ParameterFilterRuleFactory.CreateContainsRule(room_name_param_id, filter_string_value)
            except AttributeError:
                # Fallback for potentially older API versions if ParameterFilterRuleFactory is missing CreateContainsRule
                evaluator = FilterStringContains()
                case_sensitive = False # Default for CreateContainsRule is case-insensitive
                filter_rule = FilterStringRule(ParameterValueProvider(room_name_param_id), evaluator, filter_string_value, case_sensitive)

            # Create the ElementParameterFilter from the rule
            element_filter = ElementParameterFilter(filter_rule)

            # --- Check for Existing Filter ---
            existing_filter = None
            filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
            for f in filter_collector:
                if f.Name == filter_name:
                    existing_filter = f
                    break

            parameter_filter = None
            if existing_filter:
                parameter_filter = existing_filter
                # Optional: Update existing filter's categories and rules if needed (requires transaction)
                try:
                    existing_filter.SetCategories(categories)
                    existing_filter.SetElementFilter(element_filter)
                    # print("# Updated existing filter: {}".format(filter_name)) # Escaped Optional
                except Exception as update_err:
                    print("# Warning: Failed to update existing filter '{}': {}".format(filter_name, update_err)) # Escaped
            else:
                # --- Create New Filter ---
                # IMPORTANT: This creation requires a Transaction, which is assumed to be handled externally.
                try:
                    # Check if filter name is valid for creation
                     if ParameterFilterElement.IsNameUnique(doc, filter_name):
                         parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                         # print("# Created new filter: {}".format(filter_name)) # Escaped Optional
                     else:
                         # This case should ideally be caught by the existence check, but added for safety
                         print("# Error: Filter name '{}' is already in use (but wasn't found directly).".format(filter_name)) # Escaped
                except Exception as e:
                    print("# Error creating filter '{}': {}".format(filter_name, e)) # Escaped

            # --- Apply Filter and Overrides to View ---
            if parameter_filter:
                # Define Override Graphic Settings
                override_settings = OverrideGraphicSettings()
                override_settings.SetSurfaceForegroundPatternId(solid_fill_id)
                override_settings.SetSurfaceForegroundPatternColor(override_color)
                # Optional: Ensure surface patterns are visible if they were hidden globally
                # override_settings.SetSurfaceForegroundPatternVisible(True)

                # Apply the filter to the active view
                # IMPORTANT: Adding/modifying filters requires a Transaction, assumed to be handled externally.
                try:
                    # Check if the filter is already applied to the view
                    applied_filters = active_view.GetFilters()
                    if parameter_filter.Id not in applied_filters:
                        active_view.AddFilter(parameter_filter.Id)
                        # print("# Added filter '{}' to view '{}'".format(filter_name, active_view.Name)) # Escaped Optional

                    # Set the overrides for the filter in the view
                    active_view.SetFilterOverrides(parameter_filter.Id, override_settings)

                    # Ensure the filter is enabled (might be added but disabled)
                    if not active_view.GetFilterVisibility(parameter_filter.Id):
                         # Note: SetFilterVisibility controls hide/show, not enable/disable overrides
                         # It's often kept true unless explicitly hiding filtered elements.
                         # active_view.SetFilterVisibility(parameter_filter.Id, True)
                         pass # Assume visibility should be on unless specified otherwise

                    if not active_view.IsFilterEnabled(parameter_filter.Id): # Check if filter overrides are enabled
                         active_view.SetIsFilterEnabled(parameter_filter.Id, True) # Enable filter overrides

                    # print("# Applied overrides for filter '{}' in view '{}'".format(filter_name, active_view.Name)) # Escaped Optional

                except Exception as e:
                    print("# Error applying filter or overrides to the view '{}': {}".format(active_view.Name, e)) # Escaped
            elif not existing_filter:
                # This case means creation failed and it didn't exist before
                print("# Filter '{}' could not be found or created.".format(filter_name)) # Escaped