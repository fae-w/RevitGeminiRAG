# Purpose: This script modifies a Revit parameter filter's rule targeting element type names.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List/ISet

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory, FilterStringRule, FilterStringEquals, FilterStringContains, # Rule types
    OverrideGraphicSettings, Color, View, BuiltInParameter, ParameterFilterUtilities,
    LogicalAndFilter, LogicalOrFilter # For potentially complex filters
)
# Import .NET List/ISet
from System.Collections.Generic import List, ISet, IList

# --- Configuration ---
original_filter_name = "Wall Type A Filter"
new_filter_name = "Wall Type B Filter"
new_type_name_value = "Wall Type B" # The value the new filter should target

# --- Find the original filter ---
original_filter = None
filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
for f in filter_collector:
    if f.Name == original_filter_name:
        original_filter = f
        break

if not original_filter:
    print("# Error: Original filter '{}' not found.".format(original_filter_name))
else:
    # --- Get properties from the original filter ---
    try:
        original_categories = original_filter.GetCategories()
        original_element_filter = original_filter.GetElementFilter()

        if not original_categories or original_categories.Count == 0:
             print("# Error: Original filter '{}' has no categories defined.".format(original_filter_name))
             original_element_filter = None # Prevent further processing

        if not original_element_filter:
             print("# Error: Could not retrieve the element filter (rules) from '{}'.".format(original_filter_name))

    except Exception as e:
        print("# Error accessing properties of original filter '{}': {}".format(original_filter_name, e))
        original_element_filter = None # Ensure we don't proceed

    # --- Process and modify the filter rules (assuming ElementParameterFilter) ---
    new_element_filter = None
    if original_element_filter and isinstance(original_element_filter, ElementParameterFilter):
        element_param_filter = original_element_filter # Cast for clarity
        original_rules = element_param_filter.GetRules() # Gets IList<FilterRule>

        if original_rules and original_rules.Count > 0:
            # --- Assumption: Modify the FIRST rule found targeting ALL_MODEL_TYPE_NAME ---
            # More complex logic would be needed for filters with multiple rules or different parameters
            new_rules = List[FilterRule]()
            rule_modified = False
            param_id_to_modify = ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME) # Assume this is the target parameter

            for rule in original_rules:
                try:
                    # Check if the rule uses a ParameterValueProvider (most parameter rules do)
                    pvp = rule.GetParameterValueProvider()
                    if pvp and pvp.ParameterId == param_id_to_modify and not rule_modified:
                        # Create a new rule with the new value, trying 'Equals' first, then 'Contains'
                        new_rule = None
                        try:
                            # Attempt to create an 'Equals' rule
                             new_rule = ParameterFilterRuleFactory.CreateEqualsRule(param_id_to_modify, new_type_name_value)
                             # print("# Debug: Created new 'Equals' rule for '{}'".format(new_type_name_value)) # Optional Debug
                        except:
                             # Fallback: Attempt to create a 'Contains' rule if 'Equals' failed or isn't desired
                             try:
                                 new_rule = ParameterFilterRuleFactory.CreateContainsRule(param_id_to_modify, new_type_name_value)
                                 # print("# Debug: Created new 'Contains' rule for '{}'".format(new_type_name_value)) # Optional Debug
                             except Exception as rule_create_err:
                                 print("# Warning: Failed to create new rule for parameter {}: {}".format(param_id_to_modify, rule_create_err))


                        if new_rule:
                            new_rules.Add(new_rule)
                            rule_modified = True
                            # print("# Debug: Replaced rule for parameter {} with new value.".format(param_id_to_modify)) # Optional Debug
                        else:
                            # Failed to create a new rule, keep the original one
                            new_rules.Add(rule)
                            print("# Warning: Could not create replacement rule. Keeping original rule for parameter {}.".format(param_id_to_modify))
                    else:
                        # Keep other rules as they are
                        new_rules.Add(rule)
                except Exception as rule_proc_err:
                     print("# Warning: Error processing rule: {}. Skipping modification for this rule.".format(rule_proc_err))
                     new_rules.Add(rule) # Keep original if error


            if rule_modified:
                # Create the new ElementParameterFilter using the modified rules
                try:
                    new_element_filter = ElementParameterFilter(new_rules)
                except Exception as filter_create_err:
                     print("# Error: Failed to create new ElementParameterFilter from modified rules: {}".format(filter_create_err))
            else:
                print("# Warning: No rule targeting Type Name (ALL_MODEL_TYPE_NAME) was found or modified in the original filter.")
                # Decide behaviour: either stop, or create a copy with original rules
                # Let's stop for safety, as the request implies modification
                print("# Error: Could not modify rules as requested. Aborting duplication.")
                new_element_filter = None # Prevent creation


        else:
            print("# Error: Original filter '{}' has no rules defined within its ElementParameterFilter.".format(original_filter_name))
    elif original_element_filter:
        # Handle cases where the filter is not a simple ElementParameterFilter (e.g., LogicalAnd/Or)
        # This script currently doesn't support duplicating/modifying complex filter structures.
        print("# Error: Original filter '{}' uses a complex structure (e.g., LogicalAndFilter/LogicalOrFilter) which is not supported by this script for duplication.".format(original_filter_name))
        # Set new_element_filter to None to prevent creation attempt
        new_element_filter = None


    # --- Create the new filter if rules were successfully prepared ---
    if new_element_filter and original_categories:
        # Check if the new name is unique
        if ParameterFilterElement.IsNameUnique(doc, new_filter_name):
            try:
                # IMPORTANT: Creation requires a Transaction (handled externally)
                new_filter = ParameterFilterElement.Create(doc, new_filter_name, original_categories, new_element_filter)
                # print("# Successfully created new filter '{}' based on '{}'.".format(new_filter_name, original_filter_name)) # Optional Success Message
            except Exception as e:
                print("# Error creating new filter '{}': {}".format(new_filter_name, e))
        else:
            print("# Error: A filter with the name '{}' already exists.".format(new_filter_name))
    elif original_element_filter and not new_element_filter:
         # This case means rule processing failed or wasn't applicable
         print("# Filter duplication aborted due to issues processing/modifying rules.")
    # else: Filter not found or initial property access failed - error already printed