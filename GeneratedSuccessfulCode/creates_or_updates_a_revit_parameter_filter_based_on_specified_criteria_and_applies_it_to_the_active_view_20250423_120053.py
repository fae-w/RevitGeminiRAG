# Purpose: This script creates or updates a Revit parameter filter based on specified criteria and applies it to the active view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List, ICollection, IList # Adjusted imports
import System # For exception handling

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    Category,
    ElementParameterFilter,
    FilterRule,
    ParameterFilterRuleFactory,
    FilterStringRule,
    FilterStringContains, # Needed for older API approach or direct use
    ParameterValueProvider, # Needed for older API approach
    BuiltInParameter,
    ParameterFilterUtilities,
    View
)

# --- Configuration ---
filter_name = "Owner Furnishings"
target_category_bics = [BuiltInCategory.OST_Furniture, BuiltInCategory.OST_Casework]
parameter_to_check = BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
filter_string_value = "O.F.C.I."
case_sensitive = False # Typically, contains checks are case-insensitive

# --- Get Category IDs ---
category_ids = List[ElementId]()
categories_found = True
for bic in target_category_bics:
    category = Category.GetCategory(doc, bic)
    if category is not None:
        category_ids.Add(category.Id)
    else:
        print("# Error: Category '{}' not found in the document.".format(bic.ToString()))
        categories_found = False
        break # Stop if any category is missing

# Proceed only if all categories were found
if categories_found:
    # --- Define Filter Rule ---
    # Get the parameter ElementId for Comments
    comments_param_id = ElementId(parameter_to_check)

    # Check if the parameter ID is valid for the selected categories
    valid_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, category_ids)
    if comments_param_id not in valid_params:
        print("# Error: Parameter 'Comments' (BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) is not filterable for the selected categories (Furniture, Casework).")
        element_filter = None # Mark as None
    else:
        # Create the filter rule: Comments contains "O.F.C.I."
        try:
            # Modern approach (Revit 2019+) - Handles case sensitivity implicitly (usually insensitive for Contains)
            # Note: CreateContainsRule might not have explicit case sensitivity control, it defaults to Revit's behavior.
            # If strict case sensitivity needed, FilterStringRule is more explicit.
            filter_rule = ParameterFilterRuleFactory.CreateContainsRule(comments_param_id, filter_string_value)
        except AttributeError:
             # Fallback for potentially older API versions or if explicit case control is needed
             print("# Warning: Using fallback method for creating filter rule (might indicate older Revit API).")
             evaluator = FilterStringContains()
             filter_rule = FilterStringRule(ParameterValueProvider(comments_param_id), evaluator, filter_string_value, case_sensitive) # Using configured case sensitivity
        except Exception as rule_ex:
            print("# Error creating filter rule: {}".format(rule_ex))
            filter_rule = None

        if filter_rule:
             # Create the ElementParameterFilter from the rule
             rules = List[FilterRule]()
             rules.Add(filter_rule)
             element_filter = ElementParameterFilter(rules) # Use constructor taking IList<FilterRule>
        else:
             element_filter = None # Ensure it's None if rule creation failed

    # --- Find or Create Filter Element ---
    if element_filter is not None:
        parameter_filter = None
        # Check for existing filter
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        existing_filter = None
        for f in collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        if existing_filter:
            parameter_filter = existing_filter
            # print("# Using existing filter: '{}'".format(filter_name)) # Debug
            try:
                # Ensure the categories and rules are updated
                current_cats = set(existing_filter.GetCategories())
                new_cats = set(category_ids)
                if current_cats != new_cats:
                     existing_filter.SetCategories(category_ids)
                     # print("# Updated categories for filter '{}'".format(filter_name)) # Debug
                # Check if rules need update (simple check based on rule count and type for now)
                # More robust check would involve inspecting individual rules.
                existing_rules = existing_filter.GetRules()
                if existing_rules.Count != 1: # Simple check, adjust if more complex logic needed
                     existing_filter.SetElementFilter(element_filter)
                     # print("# Updated rules for filter '{}'".format(filter_name)) # Debug
            except Exception as update_ex:
                print("# Warning: Failed to verify/update existing filter '{}': {}".format(filter_name, update_ex))
                # Proceeding with existing filter, but it might not be fully up-to-date.
        else:
            # print("# Creating new filter: '{}'".format(filter_name)) # Debug
            try:
                # Create the ParameterFilterElement (Transaction managed externally)
                if ParameterFilterElement.IsNameUnique(doc, filter_name):
                    parameter_filter = ParameterFilterElement.Create(
                        doc,
                        filter_name,
                        category_ids,
                        element_filter
                    )
                    # print("# Filter '{}' created successfully.".format(filter_name)) # Debug
                else:
                     print("# Error: Filter name '{}' is already in use (but wasn't found directly).".format(filter_name)) # Should be caught above
            except System.Exception as create_ex:
                print("# Error creating filter '{}': {}".format(filter_name, create_ex))
                parameter_filter = None # Ensure parameter_filter is None if creation failed

        # --- Apply Filter to Active View (Optional, but common pattern) ---
        if parameter_filter is not None:
            active_view = doc.ActiveView
            if active_view is None or not active_view.IsValidObject:
                print("# Info: No active view found or active view is invalid. Filter created but not applied to a view.")
            elif not isinstance(active_view, View) or active_view.IsTemplate:
                print("# Info: Active view '{}' is not a graphical view or is a template. Filter created but not applied.".format(active_view.Name))
            elif not active_view.AreGraphicsOverridesAllowed():
                print("# Info: Active view '{}' (Type: {}) does not support graphic overrides/filters. Filter created but not applied.".format(active_view.Name, active_view.ViewType))
            else:
                filter_id = parameter_filter.Id
                try:
                    # Check if the filter is already added to the view
                    applied_filter_ids = active_view.GetFilters()
                    if filter_id not in applied_filter_ids:
                        active_view.AddFilter(filter_id)
                        # print("# Filter '{}' added to view '{}'.".format(filter_name, active_view.Name)) # Debug

                    # Ensure the filter is enabled (overrides active) in the view
                    if not active_view.IsFilterEnabled(filter_id):
                         active_view.SetIsFilterEnabled(filter_id, True)
                         # print("# Filter '{}' enabled in view '{}'.".format(filter_name, active_view.Name)) # Debug

                    # Ensure the filter is visible (elements matching are not hidden by filter)
                    if not active_view.GetFilterVisibility(filter_id):
                         active_view.SetFilterVisibility(filter_id, True)
                         # print("# Filter '{}' set to visible in view '{}'.".format(filter_name, active_view.Name)) # Debug

                    # No specific overrides requested, so we just add and enable it.

                except System.Exception as view_ex:
                    print("# Error applying filter to view '{}': {}".format(active_view.Name, view_ex))

        elif existing_filter is None: # Only print if creation failed and it didn't exist
             print("# Filter '{}' could not be found or created. Cannot apply to view.".format(filter_name))
    else:
        # This branch is reached if filter rule creation failed or parameter wasn't filterable
         print("# Filter '{}' could not be created due to rule/parameter issues.".format(filter_name))

# else: Handled by the initial categories_found check