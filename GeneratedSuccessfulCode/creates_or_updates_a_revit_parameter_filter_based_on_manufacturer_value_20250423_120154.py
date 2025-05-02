# Purpose: This script creates or updates a Revit parameter filter based on manufacturer value.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from System import String, Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    Category,
    ParameterFilterRuleFactory,
    FilterStringRule,
    FilterStringEquals,
    ElementParameterFilter,
    BuiltInParameter,
    SharedParameterElement # For checking if param exists as shared
)

# --- Configuration ---
filter_name = "Specific Manufacturer Doors/Windows"
manufacturer_value = "ACME Windows Inc."
target_categories_bic = [BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows]
target_parameter_bip = BuiltInParameter.ALL_MODEL_MANUFACTURER

# --- Get Category IDs ---
category_ids = List[ElementId]()
categories_found = True
for bic in target_categories_bic:
    category = Category.GetCategory(doc, bic)
    if category is None:
        print("# Error: Category '{0}' not found in the document.".format(bic.ToString()))
        categories_found = False
        break
    category_ids.Add(category.Id)

# Proceed only if all categories were found
if categories_found:
    # --- Get Parameter ID ---
    param_id = ElementId(target_parameter_bip)
    # Verify the parameter exists in the project - Check a sample element or shared params
    # Note: A comprehensive check would involve checking project/shared params,
    # but BuiltInParameter is usually reliable if it exists.
    # We'll assume the BuiltInParameter exists for simplicity.

    # --- Create Filter Rule ---
    try:
        # Using FilterStringEquals rule
        filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(param_id, manufacturer_value)
        rules = List[FilterRule]()
        rules.Add(filter_rule)

        # --- Create Element Filter ---
        # This filter contains the rule logic
        element_filter = ElementParameterFilter(rules, False) # False = Element passes if rule matches

        # --- Find or Create Filter Element ---
        filter_element = None
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for existing_filter in collector:
            if existing_filter.Name == filter_name:
                filter_element = existing_filter
                # print("# Using existing filter: '{0}'".format(filter_name)) # Debug
                break

        if filter_element is None:
            # print("# Creating new filter: '{0}'".format(filter_name)) # Debug
            try:
                # Create the ParameterFilterElement (Transaction managed externally)
                filter_element = ParameterFilterElement.Create(
                    doc,
                    filter_name,
                    category_ids,
                    element_filter # Apply the rule-based filter
                )
                # print("# Filter '{0}' created successfully.".format(filter_name)) # Debug
            except SystemException as create_ex:
                print("# Error creating filter '{0}': {1}".format(filter_name, create_ex.Message))
                filter_element = None
        else:
            # Filter exists, check and update if necessary
            # print("# Updating existing filter: '{0}'".format(filter_name)) # Debug
            try:
                # Update Categories if different
                current_cat_ids = set(filter_element.GetCategories())
                new_cat_ids = set(category_ids)
                if current_cat_ids != new_cat_ids:
                    filter_element.SetCategories(category_ids)
                    # print("# Updated categories for filter '{0}'.".format(filter_name)) # Debug

                # Update Filter Definition (Rules) if different
                # Comparing ElementFilters directly is complex. We'll just set it.
                # Note: This assumes the logic should always be the new logic defined above.
                filter_element.SetElementFilter(element_filter)
                # print("# Updated filter rules for filter '{0}'.".format(filter_name)) # Debug

            except SystemException as update_ex:
                print("# Error updating existing filter '{0}': {1}".format(filter_name, update_ex.Message))

    except SystemException as rule_ex:
        print("# Error creating filter rule for parameter '{0}': {1}".format(target_parameter_bip.ToString(), rule_ex.Message))
        # This might happen if the parameter ID is invalid or the rule type doesn't match the parameter type.

# else: Handled by the initial category check print statement