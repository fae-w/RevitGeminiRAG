# Purpose: This script creates or updates a Revit parameter filter based on door height.

﻿# Import necessary classes
import clr
clr.AddReference('System')
clr.AddReference('System.Collections')
clr.AddReference('RevitAPI')
# clr.AddReference('RevitAPIUI') # Not strictly needed for this specific script

from System.Collections.Generic import List
from System import String, Double, Exception as SystemException

# Using specific imports is generally preferred over 'import *'
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    Category,
    ParameterFilterRuleFactory,
    FilterRule, # Needed for List[FilterRule]
    ElementParameterFilter,
    BuiltInParameter
)

# --- Configuration ---
filter_name = "Non-Standard Door Height"
target_value_mm = 2134.0
target_category_bic = BuiltInCategory.OST_Doors
# Assuming 'Head Height' corresponds to INSTANCE_HEAD_HEIGHT_PARAM for doors
target_parameter_bip = BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM
epsilon = 0.001 # Tolerance for floating point comparison in feet (approx 0.3mm)

# --- Convert mm to feet (Revit Internal Units) ---
mm_to_feet = 1.0 / 304.8
target_value_feet = target_value_mm * mm_to_feet

# --- Get Category ID ---
category_ids = List[ElementId]()
category = Category.GetCategory(doc, target_category_bic)
category_found = False
if category is not None:
    category_ids.Add(category.Id)
    category_found = True
else:
    # If the category is essential and not found, script cannot proceed meaningfully.
    # Consider logging or raising an error if running interactively.
    # print("# Error: Category 'Doors' not found in the document.")
    pass # Allow script to finish if category not found, filter won't be created/updated

# Proceed only if the category was found
if category_found:
    # --- Get Parameter ID ---
    param_id = ElementId(target_parameter_bip)
    # Note: A robust check would involve finding a door instance and verifying the parameter exists.
    # We assume the BuiltInParameter exists for doors for this script.

    # --- Create Filter Rule ---
    try:
        # Create a "not equals" rule for a double value (length/height)
        filter_rule = ParameterFilterRuleFactory.CreateNotEqualsRule(param_id, target_value_feet, epsilon)

        rules = List[FilterRule]()
        rules.Add(filter_rule)

        # --- Create Element Filter ---
        # This filter contains the rule logic. The boolean 'inverted' = false means elements pass if rules match.
        # Since our rule is "NotEquals", elements that are *not* equal will pass the filter.
        element_filter = ElementParameterFilter(rules, False)

        # --- Find or Create/Update Filter Element ---
        filter_element = None
        # Use LINQ for potentially cleaner search if preferred, but loop is fine
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for existing_filter in collector:
            # Use GetName() method for ParameterFilterElement
            if existing_filter.Name == filter_name:
                filter_element = existing_filter
                break

        # Transaction should be handled by the calling C# code
        if filter_element is None:
            # Create the ParameterFilterElement
            try:
                filter_element = ParameterFilterElement.Create(
                    doc,
                    filter_name,
                    category_ids,
                    element_filter # Apply the rule-based filter
                )
            except SystemException as create_ex:
                # print("# Error creating filter '{{0}}': {{1}}".format(filter_name, create_ex.Message))
                filter_element = None # Ensure it's None if creation failed
        else:
            # Filter exists, update it
            try:
                # Update Categories if different
                current_cat_ids = List[ElementId](filter_element.GetCategories())
                ids_match = True
                if current_cat_ids.Count != category_ids.Count:
                     ids_match = False
                else:
                    # Basic check assuming single category ID matches
                    if current_cat_ids.Count > 0 and category_ids.Count > 0:
                       if current_cat_ids[0].IntegerValue != category_ids[0].IntegerValue:
                           ids_match = False
                    elif current_cat_ids.Count != category_ids.Count: # Handle empty lists if necessary
                        ids_match = False

                if not ids_match:
                    filter_element.SetCategories(category_ids)

                # Update Filter Definition (Rules)
                # It's often necessary to just set the filter again, as comparing complex filters is hard
                filter_element.SetElementFilter(element_filter)

            except SystemException as update_ex:
                # print("# Error updating existing filter '{{0}}': {{1}}".format(filter_name, update_ex.Message))
                pass # Swallow update error or handle as needed

    except SystemException as rule_ex:
        # print("# Error creating filter rule for parameter '{{0}}': {{1}}".format(target_parameter_bip.ToString(), rule_ex.Message))
        # This might happen if the parameter ID is invalid or the rule type doesn't match the parameter type.
        pass # Swallow rule creation error or handle as needed

# No EXPORT required for this task