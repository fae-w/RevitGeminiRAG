# Purpose: This script updates Revit window type marks based on a provided mapping.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String operations and Exception handling
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

# --- Input Data ---
# Format: TypeName,TypeMark (one entry per line)
input_data_string = """AW-01 Double Hung,W-DH-01
AW-02 Casement,W-C-02"""

# --- Initialization ---
type_mark_map = {}
update_log = [] # To track successes and failures

# --- Step 1: Parse the input data ---
try:
    lines = input_data_string.strip().split('\n')
    for line in lines:
        if ',' in line:
            parts = line.split(',', 1) # Split only on the first comma
            type_name = parts[0].strip()
            type_mark = parts[1].strip()
            if type_name: # Ensure type name is not empty
                type_mark_map[type_name] = type_mark
        else:
            update_log.append("# Warning: Skipping invalid line in input data: '{}'".format(line))
except Exception as parse_ex:
    print("# Error: Failed to parse input data string: {}".format(parse_ex))
    # Stop execution if parsing fails fundamentally
    type_mark_map = {} # Clear the map to prevent incorrect updates

# --- Step 2: Collect Window Types ---
window_types = []
if type_mark_map: # Proceed only if parsing was successful and yielded data
    try:
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsElementType()
        window_types = list(collector)
    except SystemException as col_ex:
        print("# Error collecting Window Types: {}".format(col_ex.Message))
        window_types = [] # Ensure loop doesn't run if collection failed

# --- Step 3: Iterate and Update Window Types ---
if window_types and type_mark_map:
    updated_count = 0
    target_parameter_bip = BuiltInParameter.ALL_MODEL_TYPE_MARK # 'Type Mark' built-in parameter

    for wt_element in window_types:
        # Ensure it's an ElementType or derived class
        if not isinstance(wt_element, ElementType):
            continue

        try:
            # Get the type name
            element_name = Element.Name.GetValue(wt_element)

            # Check if this type name is in our map
            if element_name in type_mark_map:
                target_type_mark = type_mark_map[element_name]

                # Get the 'Type Mark' parameter
                type_mark_param = wt_element.get_Parameter(target_parameter_bip)

                if type_mark_param is None:
                    update_log.append("# Error: Window Type '{}' (ID: {}) does not have the 'Type Mark' parameter.".format(element_name, wt_element.Id))
                elif type_mark_param.IsReadOnly:
                    update_log.append("# Error: 'Type Mark' parameter for Window Type '{}' (ID: {}) is read-only.".format(element_name, wt_element.Id))
                elif type_mark_param.StorageType != StorageType.String:
                    update_log.append("# Error: 'Type Mark' parameter for Window Type '{}' (ID: {}) is not a String type ({}).".format(element_name, wt_element.Id, type_mark_param.StorageType))
                else:
                    # Set the new value
                    current_value = type_mark_param.AsString()
                    if current_value != target_type_mark:
                         set_result = type_mark_param.Set(target_type_mark)
                         if set_result:
                             update_log.append("# Success: Updated 'Type Mark' for '{}' (ID: {}) to '{}'.".format(element_name, wt_element.Id, target_type_mark))
                             updated_count += 1
                         else:
                             update_log.append("# Error: Failed to set 'Type Mark' for '{}' (ID: {}). Parameter.Set returned False.".format(element_name, wt_element.Id))
                    else:
                         update_log.append("# Info: 'Type Mark' for '{}' (ID: {}) is already '{}'.".format(element_name, wt_element.Id, target_type_mark))


        except SystemException as param_ex:
            try:
                element_name_err = Element.Name.GetValue(wt_element) if wt_element else "Unknown Type"
                update_log.append("# Error accessing/setting parameter for Window Type '{}' (ID: {}): {}".format(element_name_err, wt_element.Id if wt_element else "N/A", param_ex.Message))
            except:
                 update_log.append("# Error processing an unknown Window Type: {}".format(param_ex.Message))


# --- Final Feedback ---
if not type_mark_map and not update_log:
     print("# Error: Input data parsing failed or resulted in no valid entries.")
elif not window_types and type_mark_map:
     print("# Info: No Window Types found in the document to process.")
elif not update_log and window_types and type_mark_map:
     print("# Info: No Window Types matching the provided names were found or needed updating.")
else:
    # Print the collected log messages
    for log_entry in update_log:
        print(log_entry)
    print("# --- Update process finished. ---")