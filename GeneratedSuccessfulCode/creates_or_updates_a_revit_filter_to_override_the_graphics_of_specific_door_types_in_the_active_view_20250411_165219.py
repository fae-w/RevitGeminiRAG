# Purpose: This script creates or updates a Revit filter to override the graphics of specific door types in the active view.

﻿# Imports
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    ElementType,
    ParameterFilterElement,
    ParameterFilterRuleFactory,
    FilterRule,
    BuiltInParameter,
    OverrideGraphicSettings,
    Color,
    View,
    ParameterFilterUtilities, # To check filterable parameters
    Category # To get category for checking filterability
)
from Autodesk.Revit.Exceptions import ArgumentException

# --- Configuration ---
filter_name = "Specific Door Type"
target_type_name = "DR_EXT_Double_Glass_1800x2100"
target_bic = BuiltInCategory.OST_Doors
override_color = Color(255, 0, 255) # Magenta
# Parameter used to identify the element's type
type_param_bip = BuiltInParameter.ELEM_TYPE_PARAM

# --- Find Target Door Type Element ID ---
target_type_id = ElementId.InvalidElementId
type_collector = FilteredElementCollector(doc).OfClass(ElementType)
# Using LINQ-like syntax available in IronPython with next()
target_type = next((t for t in type_collector if t.Name == target_type_name and isinstance(t, ElementType)), None) # Ensure it's an ElementType

if target_type:
    target_type_id = target_type.Id
    print("# Found target door type '{}' with ID: {}".format(target_type_name, target_type_id))
else:
    print("# Error: Door Type '{}' not found in the project.".format(target_type_name))

# --- Get Active View ---
active_view = doc.ActiveView
view_is_valid = False
if active_view and isinstance(active_view, View) and not active_view.IsTemplate:
    # Check if the view supports filters/overrides
    if active_view.AreGraphicsOverridesAllowed():
        view_is_valid = True
        print("# Found valid active view: '{}'".format(active_view.Name))
    else:
        print("# Error: Active view '{}' (Type: {}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
else:
    print("# Error: No active graphical view found, or it's a view template, or it's invalid.")

# --- Check Parameter Filterability ---
param_is_filterable = False
doors_category = Category.GetCategory(doc, target_bic)
if doors_category is None:
    print("# Error: Doors category (OST_Doors) not found.")
    target_category_id = ElementId.InvalidElementId
else:
    target_category_id = doors_category.Id
    type_param_id = ElementId(type_param_bip)
    categories_list_for_check = List[ElementId]([target_category_id])

    try:
        # Get filterable parameters common to the specified categories
        filterable_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories_list_for_check)
        if type_param_id in filterable_params:
            param_is_filterable = True
            print("# Parameter 'Type' (BuiltInParameter.ELEM_TYPE_PARAM) is filterable for Doors.")
        else:
            print("# Error: Parameter 'Type' (BuiltInParameter.ELEM_TYPE_PARAM, ID: {}) is not filterable for Doors category.".format(type_param_id))
    except Exception as filter_check_ex:
        print("# Error checking parameter filterability: {}".format(filter_check_ex))


# --- Proceed only if type, view, and parameter are valid ---
if target_type_id != ElementId.InvalidElementId and view_is_valid and param_is_filterable:

    # Define categories list for the filter
    categories = List[ElementId]()
    categories.Add(target_category_id)

    # Create the filter rule: Type parameter equals target_type_id
    filter_rule = None
    try:
        # Rule: ELEM_TYPE_PARAM == target_type_id
        type_param_id = ElementId(type_param_bip) # Get ElementId for the Type parameter
        # Create an 'equals' rule comparing the instance's type parameter to the target type ID
        filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(type_param_id, target_type_id)
    except ArgumentException as arg_ex:
         print("# Error creating filter rule (ArgumentException): {} - Ensure parameter 'Type' exists and is applicable.".format(arg_ex.Message))
    except Exception as rule_ex:
        print("# Error creating filter rule: {}".format(rule_ex))

    if filter_rule:
        filter_rules = List[FilterRule]()
        filter_rules.Add(filter_rule)

        # Check if filter already exists by name
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        filter_element_id = ElementId.InvalidElementId
        try:
            # Transaction is managed externally by the C# wrapper

            if existing_filter:
                print("# Filter '{}' already exists. Using existing filter.".format(filter_name))
                filter_element_id = existing_filter.Id
                # Optional: Update existing filter rules/categories if they differ
                try:
                    # Check and update categories
                    current_categories = existing_filter.GetCategories()
                    needs_cat_update = True
                    if len(current_categories) == len(categories) and target_category_id in current_categories:
                        needs_cat_update = False # Assume simple case: only one category needed

                    if needs_cat_update:
                         # Convert ICollection to List for modification if needed, or just create new
                         new_cat_list = List[ElementId](categories) # Use the desired list
                         existing_filter.SetCategories(new_cat_list)
                         print("# Updated categories for existing filter '{}'.".format(filter_name))

                    # Check and update rules (basic check by count, deep comparison is complex)
                    current_rules = existing_filter.GetRules()
                    if len(current_rules) != len(filter_rules): # Add more detailed rule comparison if needed
                        existing_filter.SetRules(filter_rules)
                        print("# Updated rules for existing filter '{}'.".format(filter_name))
                    else:
                        # Basic rule check: compare the target value (more robust needed for complex rules)
                        # This is a simplified check assuming one 'Equals' rule
                        if len(current_rules) == 1 and len(filter_rules) == 1:
                             # Attempt to compare rule details if possible (may fail depending on rule type)
                             try:
                                 current_equals_rule = current_rules[0]
                                 new_equals_rule = filter_rules[0]
                                 # Check if parameter and value match (ValueAsElementId for EqualsRule with ElementId)
                                 if (current_equals_rule.Parameter != new_equals_rule.Parameter or
                                     current_equals_rule.RuleValue != new_equals_rule.RuleValue): # RuleValue works for ElementId in EqualsRule
                                      existing_filter.SetRules(filter_rules)
                                      print("# Updated rules for existing filter '{}' (value mismatch).".format(filter_name))
                             except AttributeError: # If rule properties don't match expectations
                                 existing_filter.SetRules(filter_rules) # Fallback to update if comparison fails
                                 print("# Updated rules for existing filter '{}' (comparison fallback).".format(filter_name))


                except Exception as update_ex:
                    print("# Error updating existing filter '{}': {}".format(filter_name, update_ex))
                    filter_element_id = ElementId.InvalidElementId # Don't proceed if update fails

            else:
                # Create the Parameter Filter Element if it doesn't exist
                try:
                    new_filter = ParameterFilterElement.Create(doc, filter_name, categories, filter_rules)
                    filter_element_id = new_filter.Id
                    print("# Created new filter: '{}'".format(filter_name))
                except Exception as create_ex:
                    print("# Error creating ParameterFilterElement '{}': {}".format(filter_name, create_ex))

            # Proceed to apply to view only if we have a valid filter ID
            if filter_element_id != ElementId.InvalidElementId:
                # Define Override Settings for magenta lines
                ogs = OverrideGraphicSettings()
                ogs.SetProjectionLineColor(override_color)
                ogs.SetCutLineColor(override_color)
                # Note: Patterns, transparency, halftones etc. are not set here

                # Apply Filter and Overrides to the Active View
                try:
                    # Check if the filter is already applied to the view
                    applied_filters = active_view.GetFilters()
                    if filter_element_id not in applied_filters:
                        active_view.AddFilter(filter_element_id)
                        print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                    else:
                        print("# Filter '{}' was already present in view '{}'.".format(filter_name, active_view.Name))

                    # Set the graphic overrides for this filter in the view
                    active_view.SetFilterOverrides(filter_element_id, ogs)
                    # Ensure the filter is enabled (visible) in the view's V/G settings
                    active_view.SetFilterVisibility(filter_element_id, True)
                    print("# Applied magenta line color override for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

                except Exception as apply_ex:
                    print("# Error applying filter or overrides for '{}' to view '{}': {}".format(filter_name, active_view.Name, apply_ex))

        except Exception as outer_ex:
            # Catch errors during the find/create/apply process
            print("# An error occurred during filter processing: {}".format(outer_ex))

    else:
        # Rule creation failed, message should have been printed already
        print("# Cannot proceed because the filter rule could not be created.")

# Final status messages if initial checks failed
elif target_type_id == ElementId.InvalidElementId:
    print("# Cannot proceed: Target door type '{}' was not found.".format(target_type_name))
elif not view_is_valid:
    print("# Cannot proceed: Active view is not valid or does not support overrides.")
elif not param_is_filterable:
    print("# Cannot proceed: The 'Type' parameter (BuiltInParameter.ELEM_TYPE_PARAM) is not filterable for Doors.")
else:
     print("# Cannot proceed due to an unspecified initial error condition.")