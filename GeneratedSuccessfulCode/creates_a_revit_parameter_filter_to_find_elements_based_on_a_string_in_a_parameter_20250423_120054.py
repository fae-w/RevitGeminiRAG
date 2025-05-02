# Purpose: This script creates a Revit parameter filter to find elements based on a string in a parameter.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Required for List<T>
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    BuiltInCategory,
    ElementId,
    ParameterFilterElement,
    ParameterFilterRuleFactory,
    FilterStringRule,
    FilterStringContains, # Specific rule type
    ElementParameterFilter,
    FilterRule,
    BuiltInParameter,
    ParameterFilterUtilities # To verify parameter filterability (optional but good practice)
)

# Define filter properties
filter_name = "Hide Inactive Doors"
target_category = BuiltInCategory.OST_Doors
target_parameter_id = ElementId(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
target_value = "Inactive"
case_sensitive = False # Typically more user-friendly

# --- Parameter Filterability Check (Optional but recommended) ---
# Create a list containing just the Door category ID
temp_categories_for_check = List[ElementId]()
temp_categories_for_check.Add(ElementId(target_category))

# Get filterable parameters common to the specified categories
filterable_parameters = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, temp_categories_for_check)

# Check if the desired parameter is filterable for the Door category
is_param_filterable = False
for param_id in filterable_parameters:
    if param_id == target_parameter_id:
        is_param_filterable = True
        break

if not is_param_filterable:
    print("# Error: The 'Comments' parameter (BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) is not filterable for the 'Doors' category.")
else:
    # --- Proceed with filter creation ---

    # Get the category ElementId
    door_category_id = ElementId(target_category)
    categories = List[ElementId]()
    categories.Add(door_category_id)

    # Create the filter rule: Comments contains "Inactive" (case-insensitive)
    # Note: ParameterFilterRuleFactory.CreateContainsRule takes ElementId, string value, case sensitivity bool
    try:
        filter_rule = ParameterFilterRuleFactory.CreateContainsRule(target_parameter_id, target_value, case_sensitive)
    except Exception as rule_ex:
         # Handle potential issues like invalid parameter ID for rule creation if check above was skipped
         print("# Error creating filter rule: {}".format(rule_ex))
         filter_rule = None

    if filter_rule:
        # Create a list of rules (even if only one)
        rules = List[FilterRule]()
        rules.Add(filter_rule)

        # Create the ElementParameterFilter from the rule(s)
        element_filter = ElementParameterFilter(rules)

        # Create the ParameterFilterElement
        # The transaction is handled by the external C# wrapper
        try:
            # Check if filter with the same name already exists (optional, Create might overwrite or throw)
            # existing_filter = FilteredElementCollector(doc).OfClass(ParameterFilterElement).Where(lambda f: f.Name == filter_name).FirstOrDefault()
            # if existing_filter:
            #     print("# Info: Filter '{}' already exists. Skipping creation.".format(filter_name))
            # else:
            parameter_filter_element = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
            # print("# Successfully created filter: '{}' (ID: {})".format(filter_name, parameter_filter_element.Id)) # Optional success message
        except Exception as ex:
            # Catch potential errors during creation (e.g., name collision if not handled above)
            print("# Error creating ParameterFilterElement: {}".format(ex))