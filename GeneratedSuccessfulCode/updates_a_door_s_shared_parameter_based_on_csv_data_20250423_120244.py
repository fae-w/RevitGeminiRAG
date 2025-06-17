# Purpose: This script updates a door's shared parameter based on CSV data.

﻿# Ensure necessary assemblies are referenced
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Collections') # For List

# Import necessary namespaces and classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance, # Doors are often FamilyInstances
    Parameter,
    BuiltInParameter,
    StorageType,
    Element
)
from System import String, Boolean, Int32, Exception as SystemException
# GUID might be needed if direct lookup fails, but we'll try name first
# from System import Guid
# from Autodesk.Revit.DB import SharedParameterElement

# --- Input Data (CSV Format) ---
csv_data = """Mark,IsFireExit
D-EXIT-01,Yes
D-EXIT-02,Yes
D-CORR-01,No"""

# --- Target Shared Parameter Name ---
SHARED_PARAM_NAME = "Is Fire Exit Route"

# --- Parse CSV Data ---
parsed_data = {} # Dictionary: { Mark_Value: Boolean_Value }
lines = csv_data.strip().split('\n')
if len(lines) > 1:
    header = [h.strip() for h in lines[0].split(',')]
    # Expecting "Mark" and the shared param name or similar
    if len(header) == 2 and header[0].lower() == "mark": # Simple check
        mark_index = 0
        value_index = 1
        for line in lines[1:]:
            values = [v.strip() for v in line.split(',')]
            if len(values) == 2:
                mark_value = values[mark_index]
                yes_no_value_str = values[value_index]
                if mark_value:
                    # Convert Yes/No string to Boolean
                    bool_value = None
                    if yes_no_value_str.lower() == "yes":
                        bool_value = True
                    elif yes_no_value_str.lower() == "no":
                        bool_value = False
                    else:
                         print("# Warning: Skipping row with unrecognized Yes/No value: '{}'".format(line))
                         continue # Skip this row

                    parsed_data[mark_value] = bool_value
                else:
                    print("# Warning: Skipping row with empty Mark value: '{}'".format(line))
            else:
                print("# Warning: Skipping malformed CSV row: '{}'".format(line))
    else:
         print("# Error: CSV header not in expected format ('Mark,Value'). Found: '{}'".format(lines[0]))
         parsed_data = {} # Clear data on error
else:
    print("# Error: CSV data seems empty or lacks header row.")


# --- Collect Door Instances and Index by Mark ---
door_dict = {}
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()
doors = collector.ToElements()

for door in doors:
    # Ensure it's a FamilyInstance (most doors are) to access instance parameters easily
    if isinstance(door, FamilyInstance):
        mark_param = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if mark_param and mark_param.HasValue:
            mark_value = mark_param.AsString()
            if mark_value:
                if mark_value not in door_dict:
                    door_dict[mark_value] = []
                door_dict[mark_value].append(door)

# --- Counters for Summary ---
total_marks_in_csv = len(parsed_data)
marks_processed = 0
doors_updated_count = 0
updates_applied_count = 0
errors_count = 0
warnings_count = 0
skipped_mark_not_found = 0
skipped_param_not_found = 0
skipped_param_read_only = 0
skipped_param_wrong_type = 0
skipped_param_not_shared = 0 # Specific check for shared param

# --- Iterate through Parsed Data and Update Doors ---
if not parsed_data:
    print("# No valid data parsed from CSV.")
elif not door_dict:
    print("# No door instances found in the project.")
else:
    print("# Starting door parameter update process for parameter '{}'...".format(SHARED_PARAM_NAME))
    for mark_to_find, bool_value_to_set in parsed_data.items():
        marks_processed += 1
        # Convert boolean value to integer (1 for True/Yes, 0 for False/No)
        int_value_to_set = 1 if bool_value_to_set else 0

        if mark_to_find in door_dict:
            target_doors = door_dict[mark_to_find]
            # print("# Found {} door(s) with Mark '{}'".format(len(target_doors), mark_to_find)) # Debug

            for door_instance in target_doors:
                door_updated_in_this_row = False # Flag if any param was set for this specific door element
                door_info = "Door Mark '{}', ID {}".format(mark_to_find, door_instance.Id)

                param = None
                try:
                    # Attempt to get the parameter by name
                    param = door_instance.LookupParameter(SHARED_PARAM_NAME)

                    if param:
                        # Verify it's a shared parameter
                        if not param.IsShared:
                            # print("# Warning: Parameter '{}' on {} is not a Shared Parameter. Skipping.".format(SHARED_PARAM_NAME, door_info)) # Verbose
                            warnings_count += 1
                            skipped_param_not_shared += 1
                        elif param.IsReadOnly:
                            # print("# Warning: Parameter '{}' on {} is read-only. Skipping.".format(SHARED_PARAM_NAME, door_info)) # Verbose
                            warnings_count += 1
                            skipped_param_read_only += 1
                        # Yes/No parameters have StorageType Integer
                        elif param.StorageType != StorageType.Integer:
                            print("# Warning: Parameter '{}' on {} has wrong storage type (Expected: Integer for Yes/No, Actual: {}). Skipping.".format(SHARED_PARAM_NAME, door_info, param.StorageType))
                            warnings_count += 1
                            skipped_param_wrong_type += 1
                        else:
                            # Attempt to set the value (as integer 0 or 1)
                            current_value = param.AsInteger()

                            # Only update if the value is different
                            if current_value != int_value_to_set:
                                try:
                                    set_result = param.Set(int_value_to_set)
                                    if set_result:
                                        updates_applied_count += 1
                                        door_updated_in_this_row = True
                                        # print("# Success: Updated '{}' to '{}' for {}".format(SHARED_PARAM_NAME, "Yes" if int_value_to_set == 1 else "No", door_info)) # Verbose
                                    else:
                                        # Check if read-only again
                                        if param.IsReadOnly:
                                             # print("# Info: Parameter '{}' ({}) became read-only before update.".format(SHARED_PARAM_NAME, door_info)) # Verbose
                                             warnings_count += 1
                                             skipped_param_read_only +=1
                                        else:
                                             print("# Error: Failed to set parameter '{}' to '{}' for {} (Set method returned false).".format(SHARED_PARAM_NAME, "Yes" if int_value_to_set == 1 else "No", door_info))
                                             errors_count += 1
                                except SystemException as set_ex:
                                    print("# Error setting parameter '{}' for {}: {}".format(SHARED_PARAM_NAME, door_info, set_ex.Message))
                                    errors_count += 1
                            # else: # Value is already correct - uncomment for verbose logging
                                # print("# Info: Parameter '{}' already set to '{}' for {}".format(SHARED_PARAM_NAME, "Yes" if int_value_to_set == 1 else "No", door_info))
                    else:
                        # Parameter not found on the instance using LookupParameter
                        # print("# Warning: Instance parameter '{}' not found for {}. Skipping.".format(SHARED_PARAM_NAME, door_info)) # Verbose
                        warnings_count += 1
                        skipped_param_not_found += 1

                except SystemException as param_ex:
                    print("# Error processing parameter '{}' for {}: {}".format(SHARED_PARAM_NAME, door_info, param_ex.Message))
                    errors_count += 1

                if door_updated_in_this_row:
                    doors_updated_count += 1 # Count unique doors that had at least one parameter updated

        else:
            # Mark from CSV not found in project doors
            # print("# Warning: Door with Mark '{}' specified in CSV not found in the project. Skipping row.".format(mark_to_find)) # Verbose
            warnings_count += 1
            skipped_mark_not_found += 1

# --- Final Summary ---
print("--- Door Shared Parameter ('{}') Update Summary ---".format(SHARED_PARAM_NAME))
print("Total Unique Marks in CSV: {}".format(total_marks_in_csv))
print("Marks Processed: {}".format(marks_processed))
print("Total Door Elements Found (Category OST_Doors, Instances): {}".format(len(doors)))
print("Unique Door Elements Updated: {}".format(doors_updated_count))
print("Total Parameter Updates Applied: {}".format(updates_applied_count))
print("--- Issues Encountered ---")
print("Skipped Rows (Mark Not Found in Project): {}".format(skipped_mark_not_found))
print("Skipped Updates (Parameter '{}' Not Found on Instance): {}".format(SHARED_PARAM_NAME, skipped_param_not_found))
print("Skipped Updates (Parameter Not Shared): {}".format(skipped_param_not_shared))
print("Skipped Updates (Parameter Read-Only): {}".format(skipped_param_read_only))
print("Skipped Updates (Parameter Wrong Type - Expected Integer): {}".format(skipped_param_wrong_type))
print("Other Warnings (e.g., bad CSV format/values): {}".format(warnings_count - skipped_mark_not_found - skipped_param_not_found - skipped_param_read_only - skipped_param_wrong_type - skipped_param_not_shared))
print("Errors During Update: {}".format(errors_count))
print("--- Script Finished ---")