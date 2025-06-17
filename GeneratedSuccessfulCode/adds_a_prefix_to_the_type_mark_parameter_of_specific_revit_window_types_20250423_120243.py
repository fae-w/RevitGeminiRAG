# Purpose: This script adds a prefix to the 'Type Mark' parameter of specific Revit window types.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String comparison and manipulation
from System import String, StringComparison, Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementType,
    FamilySymbol, # Window types are often FamilySymbols
    Family,
    Parameter,
    StorageType,
    BuiltInParameter,
    Element
)

# --- Configuration ---
family_name_substring = "Opening"
prefix_to_add = "o"
update_log = [] # To track successes and failures
target_parameter_bip = BuiltInParameter.ALL_MODEL_TYPE_MARK # 'Type Mark' built-in parameter

# --- Step 1: Collect Window Types ---
window_types = []
try:
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsElementType()
    window_types = list(collector)
except SystemException as col_ex:
    print("# Error collecting Window Types: {{}}".format(col_ex.Message))
    window_types = [] # Ensure loop doesn't run if collection failed

# --- Step 2: Iterate and Update Specific Window Types ---
if window_types:
    updated_count = 0
    processed_count = 0

    for wt_element in window_types:
        # Ensure it's an ElementType or derived class like FamilySymbol
        if not isinstance(wt_element, ElementType):
            continue

        try:
            # Get the Family object associated with this type
            family = wt_element.Family
            if family is None:
                update_log.append("# Info: Skipping Window Type ID: {{}} as it has no associated Family.".format(wt_element.Id))
                continue

            # Get the Family Name
            family_name = family.Name

            # Check if the family name contains the target substring (case-insensitive)
            # Using .NET String.Contains with StringComparison
            if family_name and family_name_substring and family_name.IndexOf(family_name_substring, StringComparison.OrdinalIgnoreCase) >= 0:
                processed_count += 1
                element_name = Element.Name.GetValue(wt_element) # Get type name for logging

                # Get the 'Type Mark' parameter
                type_mark_param = wt_element.get_Parameter(target_parameter_bip)

                if type_mark_param is None:
                    update_log.append("# Error: Window Type '{{}}' (Family: '{{}}', ID: {{}}) does not have the 'Type Mark' parameter.".format(element_name, family_name, wt_element.Id))
                elif type_mark_param.IsReadOnly:
                    update_log.append("# Error: 'Type Mark' parameter for Window Type '{{}}' (Family: '{{}}', ID: {{}}) is read-only.".format(element_name, family_name, wt_element.Id))
                elif type_mark_param.StorageType != StorageType.String:
                    update_log.append("# Error: 'Type Mark' parameter for Window Type '{{}}' (Family: '{{}}', ID: {{}}) is not a String type ({{}}).".format(element_name, family_name, wt_element.Id, type_mark_param.StorageType))
                else:
                    # Get the current value
                    current_value = type_mark_param.AsString()
                    if current_value is None:
                        current_value = "" # Treat null as empty string

                    # Construct the new value only if it doesn't already start with the prefix
                    if not current_value.startswith(prefix_to_add):
                        new_value = prefix_to_add + current_value

                        # Set the new value
                        set_result = type_mark_param.Set(new_value)
                        if set_result:
                            update_log.append("# Success: Updated 'Type Mark' for Type '{{}}' (Family: '{{}}', ID: {{}}) from '{{}}' to '{{}}'.".format(element_name, family_name, wt_element.Id, current_value, new_value))
                            updated_count += 1
                        else:
                            update_log.append("# Error: Failed to set 'Type Mark' for Type '{{}}' (Family: '{{}}', ID: {{}}). Parameter.Set returned False.".format(element_name, family_name, wt_element.Id))
                    else:
                         update_log.append("# Info: 'Type Mark' for Type '{{}}' (Family: '{{}}', ID: {{}}) already starts with '{{}}'. Value: '{{}}'.".format(element_name, family_name, wt_element.Id, prefix_to_add, current_value))

        except SystemException as param_ex:
            try:
                element_name_err = Element.Name.GetValue(wt_element) if wt_element else "Unknown Type"
                family_name_err = wt_element.Family.Name if wt_element and wt_element.Family else "Unknown Family"
                update_log.append("# Error processing Window Type '{{}}' (Family: '{{}}', ID: {{}}): {{}}".format(element_name_err, family_name_err, wt_element.Id if wt_element else "N/A", param_ex.Message))
            except:
                 update_log.append("# Error processing an unknown Window Type: {{}}".format(param_ex.Message))

# --- Final Feedback ---
if not window_types:
     print("# Info: No Window Types found in the document to process.")
elif processed_count == 0:
    print("# Info: No Window Types found with a Family Name containing '{{}}'.".format(family_name_substring))
else:
    # Print the collected log messages
    for log_entry in update_log:
        print(log_entry)
    print("# --- Update process finished. Found {{}} types with family name containing '{{}}'. Attempted update on {{}} of them. See log for details. ---".format(processed_count, family_name_substring, updated_count))