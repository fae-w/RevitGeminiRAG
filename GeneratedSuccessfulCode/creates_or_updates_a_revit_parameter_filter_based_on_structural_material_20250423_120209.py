# Purpose: This script creates or updates a Revit parameter filter based on structural material.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory, FilterStringRule, FilterStringContains,
    BuiltInParameter, ParameterValueProvider
)
# Import .NET List
from System.Collections.Generic import List

# --- Configuration ---
filter_name = "Concrete Structure"
target_categories_ids = [
    ElementId(BuiltInCategory.OST_StructuralColumns),
    ElementId(BuiltInCategory.OST_StructuralFraming)
]
parameter_to_filter_on_id = ElementId(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
filter_string_value = "Concrete" # The text to search for in the Structural Material parameter

# --- Prepare Categories List ---
categories = List[ElementId]()
for cat_id in target_categories_ids:
    categories.Add(cat_id)

# --- Define Filter Rule ---
# Create the filter rule: Structural Material parameter contains "Concrete" (case-insensitive by default)
try:
    # Modern approach (Revit 2019+)
    filter_rule = ParameterFilterRuleFactory.CreateContainsRule(parameter_to_filter_on_id, filter_string_value)
except AttributeError:
    # Fallback for potentially older API versions if ParameterFilterRuleFactory is missing CreateContainsRule
    # This assumes FilterStringRule exists and takes evaluator, value, case_sensitive args
    evaluator = FilterStringContains()
    case_sensitive = False # Default for CreateContainsRule is case-insensitive
    param_provider = ParameterValueProvider(parameter_to_filter_on_id)
    filter_rule = FilterStringRule(param_provider, evaluator, filter_string_value, case_sensitive)
except Exception as rule_ex:
     print("# Error creating filter rule: {}".format(rule_ex))
     filter_rule = None

# Check if rule creation was successful before proceeding
if filter_rule:
    # Create the ElementParameterFilter from the rule(s)
    # For multiple rules, use List<FilterRule> and ElementParameterFilter constructor taking List<FilterRule>
    element_filter_rules = List[FilterRule]()
    element_filter_rules.Add(filter_rule)
    element_filter = ElementParameterFilter(element_filter_rules) # Use constructor taking List<FilterRule>

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
        # try:
        #     existing_filter.SetCategories(categories)
        #     existing_filter.SetElementFilter(element_filter)
        #     print("# Updated existing filter: {}".format(filter_name)) # Optional
        # except Exception as update_err:
        #     print("# Warning: Failed to update existing filter '{}': {}".format(filter_name, update_err))
        pass # Filter already exists, nothing more to do based on prompt
        # print("# Filter '{}' already exists.".format(filter_name)) # Optional info message
    else:
        # --- Create New Filter ---
        # IMPORTANT: This creation requires a Transaction, which is assumed to be handled externally.
        try:
            # Check if filter name is valid for creation
            if ParameterFilterElement.IsNameUnique(doc, filter_name):
                parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                # print("# Created new filter: {}".format(filter_name)) # Optional success message
            else:
                 # This case should ideally be caught by the existence check, but added for safety
                 print("# Error: Filter name '{}' is already in use (but wasn't found directly).".format(filter_name))
        except Exception as e:
            print("# Error creating filter '{}': {}".format(filter_name, e))

    # Note: The filter is created in the document. Applying it to a view is a separate step
    # and was not requested in the prompt. If application to the active view is needed,
    # add code here similar to the dynamic examples (GetActiveView, AddFilter, SetFilterOverrides).

elif not filter_rule:
    print("# Filter creation skipped because the rule could not be created.")