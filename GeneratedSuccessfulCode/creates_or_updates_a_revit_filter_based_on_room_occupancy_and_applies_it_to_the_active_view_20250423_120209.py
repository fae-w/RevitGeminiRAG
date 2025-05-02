# Purpose: This script creates or updates a Revit filter based on room occupancy and applies it to the active view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory, FilterStringRule, FilterStringEquals,
    OverrideGraphicSettings, View, BuiltInParameter, ParameterFilterUtilities
)
# Import .NET List
from System.Collections.Generic import List
import System # For exception handling

# --- Configuration ---
filter_name = "Assembly Occupancy Rooms"
target_category_id = ElementId(BuiltInCategory.OST_Rooms)
# Assuming 'Occupancy' corresponds to the standard Room Occupancy parameter
parameter_to_check_bip = BuiltInParameter.ROOM_OCCUPANCY
parameter_name_if_not_builtin = "Occupancy" # Fallback name if BuiltInParameter fails
filter_string_value = "Assembly Area" # The exact text value to match

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate or not active_view.AreGraphicsOverridesAllowed():
    print("# Error: Requires an active, non-template graphical view that supports filters.")
    active_view = None # Prevent further processing

# Proceed only if the view is valid
if active_view:
    # --- Define Categories ---
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # --- Find Parameter ID and Validate ---
    occupancy_param_id = ElementId.InvalidElementId
    param_found_by_name = False

    # Try BuiltInParameter first
    try:
        test_param_id = ElementId(parameter_to_check_bip)
        valid_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories)
        if test_param_id in valid_params:
            occupancy_param_id = test_param_id
            # print("# Debug: Found filterable parameter using BuiltInParameter.ROOM_OCCUPANCY") # Escaped Optional
        else:
             # print("# Debug: BuiltInParameter.ROOM_OCCUPANCY is not filterable for Rooms.") # Escaped Optional
             pass
    except Exception as bip_ex:
        # print("# Debug: Exception checking BuiltInParameter: {{}}".format(bip_ex)) # Escaped Optional
        pass

    # If BuiltInParameter didn't work, try searching by name (less reliable)
    if occupancy_param_id == ElementId.InvalidElementId:
        # print("# Debug: Trying to find parameter by name '{{}}'".format(parameter_name_if_not_builtin)) # Escaped Optional
        valid_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories)
        for param_id in valid_params:
            try:
                param_def = doc.GetElement(param_id)
                if param_def and hasattr(param_def, 'Name') and param_def.Name == parameter_name_if_not_builtin:
                    occupancy_param_id = param_id
                    param_found_by_name = True
                    # print("# Debug: Found filterable parameter by name '{{}}'".format(parameter_name_if_not_builtin)) # Escaped Optional
                    break
            except Exception as name_ex:
                 # print("# Debug: Error checking parameter {{}}: {{}}".format(param_id, name_ex)) # Escaped Optional
                 pass

    # Check if parameter was found
    if occupancy_param_id == ElementId.InvalidElementId:
         print("# Error: Could not find a filterable parameter 'Occupancy' (tried BuiltInParameter and by name) for the 'Rooms' category.")
    else:
        # --- Define Filter Rule ---
        try:
            # Create the filter rule: Parameter equals filter_string_value (case-sensitive)
            # Note: ParameterFilterRuleFactory.CreateEqualsRule uses case-sensitive comparison for strings.
            filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(occupancy_param_id, filter_string_value)
        except AttributeError:
            # Fallback for older API versions if ParameterFilterRuleFactory is missing CreateEqualsRule
            evaluator = FilterStringEquals()
            case_sensitive = True # Default for CreateEqualsRule IS case-sensitive
            filter_rule = FilterStringRule(ParameterValueProvider(occupancy_param_id), evaluator, filter_string_value, case_sensitive)
        except System.Exception as rule_ex:
             print("# Error creating filter rule: {}".format(rule_ex)) # Escaped
             filter_rule = None

        if filter_rule:
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
                # Optional: Update existing filter's categories and rules if needed
                try:
                    existing_filter.SetCategories(categories)
                    existing_filter.SetElementFilter(element_filter)
                    # print("# Updated existing filter: '{{}}'".format(filter_name)) # Escaped Optional
                except Exception as update_err:
                    print("# Warning: Failed to update existing filter '{{}}': {{}}".format(filter_name, update_err)) # Escaped
            else:
                # --- Create New Filter ---
                # IMPORTANT: This creation requires a Transaction, which is assumed to be handled externally.
                try:
                    if ParameterFilterElement.IsNameUnique(doc, filter_name):
                        parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                        # print("# Created new filter: '{{}}'".format(filter_name)) # Escaped Optional
                    else:
                        print("# Error: Filter name '{{}}' is already in use (but wasn't found directly).".format(filter_name)) # Escaped
                except System.Exception as create_ex:
                    print("# Error creating filter '{{}}': {{}}".format(filter_name, create_ex)) # Escaped

            # --- Apply Filter to Active View ---
            if parameter_filter:
                filter_id = parameter_filter.Id
                try:
                    # Check if the filter is already added to the view
                    applied_filter_ids = active_view.GetFilters()
                    if filter_id not in applied_filter_ids:
                        active_view.AddFilter(filter_id)
                        # print("# Added filter '{{}}' to view '{{}}'".format(filter_name, active_view.Name)) # Escaped Optional

                    # No specific overrides requested, but ensure the filter is enabled
                    if not active_view.IsFilterEnabled(filter_id):
                         active_view.SetIsFilterEnabled(filter_id, True) # Enable filter overrides
                         # print("# Enabled filter '{{}}' in view '{{}}'".format(filter_name, active_view.Name)) # Escaped Optional

                    # Optional: Set default overrides (e.g., if you want to explicitly clear any existing)
                    # default_overrides = OverrideGraphicSettings() # Create empty settings
                    # active_view.SetFilterOverrides(filter_id, default_overrides)

                except System.Exception as view_ex:
                    print("# Error applying filter '{{}}' to view '{{}}': {{}}".format(filter_name, active_view.Name, view_ex)) # Escaped
            elif not existing_filter:
                # This case means creation failed and it didn't exist before
                print("# Filter '{{}}' could not be found or created.".format(filter_name)) # Escaped

# else: Handled by initial view check message