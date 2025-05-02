# Purpose: This script adds a prefix to the 'Type Mark' parameter of specific Revit window types.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String comparison and manipulation
from System import String, Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementType,
    FamilySymbol, # Window types are often FamilySymbols
    Parameter,
    StorageType,
    BuiltInParameter,
    Element
)

# --- Configuration ---
target_type_name = "Schematic Opening Cut"
prefix_to_add = "o"
update_log = [] # To track successes and failures
target_parameter_bip = BuiltInParameter.ALL_MODEL_TYPE_MARK # 'Type Mark' built-in parameter

# --- Step 1: Collect Window Types ---
window_types = []
try:
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsElementType()
    window_types = list(collector)
except SystemException as col_ex:
    print("# Error collecting Window Types: {}".format(col_ex.Message))
    window_types = [] # Ensure loop doesn't run if collection failed

# --- Step 2: Iterate and Update Specific Window Types ---
if window_types:
    updated_count = 0
    processed_count = 0

    for wt_element in window_types:
        # Ensure it's an ElementType or derived class
        if not isinstance(wt_element, ElementType):
            continue

        try:
            # Get the type name
            element_name = Element.Name.GetValue(wt_element)

            # Check if this type name matches our target
            if String.Equals(element_name, target_type_name, StringComparison.OrdinalIgnoreCase): # Case-insensitive comparison might be safer
                processed_count += 1
                # Get the 'Type Mark' parameter
                type_mark_param = wt_element.get_Parameter(target_parameter_bip)

                if type_mark_param is None:
                    update_log.append("# Error: Window Type '{}' (ID: {}) does not have the 'Type Mark' parameter.".format(element_name, wt_element.Id))
                elif type_mark_param.IsReadOnly:
                    update_log.append("# Error: 'Type Mark' parameter for Window Type '{}' (ID: {}) is read-only.".format(element_name, wt_element.Id))
                elif type_mark_param.StorageType != StorageType.String:
                    update_log.append("# Error: 'Type Mark' parameter for Window Type '{}' (ID: {}) is not a String type ({}).".format(element_name, wt_element.Id, type_mark_param.StorageType))
                else:
                    # Get the current value
                    current_value = type_mark_param.AsString()
                    if current_value is None:
                        current_value = "" # Treat null as empty string

                    # Construct the new value
                    new_value = prefix_to_add + current_value

                    # Only update if the value actually changes
                    if current_value != new_value:
                        # Set the new value
                        set_result = type_mark_param.Set(new_value)
                        if set_result:
                            update_log.append("# Success: Updated 'Type Mark' for '{}' (ID: {}) from '{}' to '{}'.".format(element_name, wt_element.Id, current_value, new_value))
                            updated_count += 1
                        else:
                            update_log.append("# Error: Failed to set 'Type Mark' for '{}' (ID: {}). Parameter.Set returned False.".format(element_name, wt_element.Id))
                    else:
                         update_log.append("# Info: 'Type Mark' for '{}' (ID: {}) already starts with '{}' or prefix is redundant.".format(element_name, wt_element.Id, prefix_to_add))

        except SystemException as param_ex:
            try:
                element_name_err = Element.Name.GetValue(wt_element) if wt_element else "Unknown Type"
                update_log.append("# Error accessing/setting parameter for Window Type '{}' (ID: {}): {}".format(element_name_err, wt_element.Id if wt_element else "N/A", param_ex.Message))
            except:
                 update_log.append("# Error processing an unknown Window Type: {}".format(param_ex.Message))

# --- Final Feedback ---
if not window_types:
     print("# Info: No Window Types found in the document to process.")
elif processed_count == 0:
    print("# Info: No Window Types found with the name '{}'.".format(target_type_name))
else:
    # Print the collected log messages
    for log_entry in update_log:
        print(log_entry)
    print("# --- Update process finished. Found {} types named '{}'. Updated {} of them. ---".format(processed_count, target_type_name, updated_count))