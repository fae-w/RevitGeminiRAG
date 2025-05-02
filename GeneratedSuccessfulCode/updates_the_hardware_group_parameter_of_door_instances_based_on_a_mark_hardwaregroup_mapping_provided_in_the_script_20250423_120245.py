# Purpose: This script updates the 'Hardware Group' parameter of door instances based on a Mark/HardwareGroup mapping provided in the script.

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
    FamilyInstance, # Doors are typically FamilyInstances
    Parameter,
    BuiltInParameter,
    StorageType,
    Element
)
from System.Collections.Generic import List
from System import String, Exception as SystemException

# --- Input Data ---
# Multi-line string containing the Mark/HardwareGroup mapping
# Format: Mark,HardwareGroup (header is ignored)
data_string = """Mark,HardwareGroup
D-L1-01,HG-01
D-L1-02,HG-02
D-L2-01,HG-03"""

# --- Parameter Name to Update ---
target_parameter_name = "Hardware Group" # Case-sensitive

# --- Parse Input Data ---
mark_to_param_map = {}
lines = data_string.strip().split('\n')
# Skip header line (index 0)
if len(lines) > 1:
    for line in lines[1:]:
        parts = line.strip().split(',', 1) # Split only on the first comma
        if len(parts) == 2:
            mark_value = parts[0].strip()
            param_value = parts[1].strip()
            if mark_value: # Ensure mark is not empty
                mark_to_param_map[mark_value] = param_value
            else:
                print("# Warning: Skipping line with empty Mark value: '{}'".format(line))
        else:
            print("# Warning: Skipping malformed line: '{}'".format(line))
else:
    print("# Error: Input data string seems empty or lacks header row.")

if not mark_to_param_map:
    print("# Error: No valid Mark/Parameter pairs found in the input data.")
else:
    # --- Collect Door Instances and Index by Mark ---
    door_dict = {}
    collection_failed = False
    doors_found_count = 0
    try:
        door_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()
        # Using ToElements() is generally safer than direct iteration/casting
        doors = door_collector.ToElements()
        doors_found_count = len(doors) if doors else 0

        # Index doors by Mark for efficient lookup
        for door in doors:
            if isinstance(door, FamilyInstance): # Ensure it's an instance
                mark_param = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                if mark_param and mark_param.HasValue:
                    mark_value = mark_param.AsString()
                    if mark_value:
                        if mark_value not in door_dict:
                            door_dict[mark_value] = []
                        door_dict[mark_value].append(door)

    except SystemException as e:
        print("# Error collecting doors: {}".format(e.Message))
        collection_failed = True # Mark collection as failed
        doors = [] # Ensure doors is an empty list

    # --- Counters for Summary ---
    processed_marks_count = 0
    doors_updated_count = 0 # Count unique door elements updated
    parameter_updates_count = 0 # Count total successful set operations
    skipped_mark_not_found_in_model = 0
    skipped_no_param = 0
    skipped_param_read_only = 0
    skipped_param_wrong_type = 0
    error_count = 0

    if doors and not collection_failed:
        print("# Found {} door instances in the model.".format(doors_found_count))
        print("# Processing {} Mark/Value pairs from input data.".format(len(mark_to_param_map)))
        print("# Looking for Marks: {}".format(", ".join(mark_to_param_map.keys())))

        # --- Iterate through parsed data and update doors ---
        # Transaction is handled externally by the C# wrapper
        for mark_value, target_param_value in mark_to_param_map.items():
            processed_marks_count += 1
            if mark_value in door_dict:
                target_doors = door_dict[mark_value]
                # print("# Found {} door(s) with Mark '{}'".format(len(target_doors), mark_value)) # Verbose

                for door_instance in target_doors:
                    door_info = "Door Mark '{}', ID {}".format(mark_value, door_instance.Id)
                    parameter_updated_for_this_door = False

                    try:
                        # Get the target INSTANCE parameter using LookupParameter
                        # This is crucial for shared/project parameters applied to instances.
                        param = door_instance.LookupParameter(target_parameter_name)

                        if param is None:
                            # Fallback: Check if it's a built-in param (unlikely for "Hardware Group")
                            # This section can be removed if "Hardware Group" is definitely not a BIP
                            # for b_param_enum in BuiltInParameter.GetValues(BuiltInParameter):
                            #     try:
                            #        b_param_def = Parameter.GetDefinition(b_param_enum)
                            #        if b_param_def and b_param_def.Name == target_parameter_name:
                            #             param = door_instance.get_Parameter(b_param_enum)
                            #             if param: break # Found a match
                            #     except: pass # Ignore errors during fallback check

                            if param is None: # Still not found after fallback
                                skipped_no_param += 1
                                # print("# Skipping {} - Parameter '{}' not found.".format(door_info, target_parameter_name)) # Verbose
                                continue # Skip to the next door instance

                        # Check if parameter is read-only
                        if param.IsReadOnly:
                            skipped_param_read_only += 1
                            # print("# Skipping {} - Parameter '{}' is read-only.".format(door_info, target_parameter_name)) # Verbose
                            continue

                        # Check storage type (assuming String for "Hardware Group")
                        if param.StorageType != StorageType.String:
                            skipped_param_wrong_type += 1
                            print("# Skipping {} - Parameter '{}' is not a String type (Type: {}).".format(door_info, target_parameter_name, param.StorageType))
                            continue

                        # Get current value and compare
                        current_value = param.AsString()
                        if current_value != target_param_value:
                            # Set the parameter value (Transaction must be active outside this script)
                            try:
                                # Transaction must be started BEFORE this call by the external host
                                set_result = param.Set(target_param_value)
                                if set_result:
                                    parameter_updates_count += 1
                                    parameter_updated_for_this_door = True
                                    # print("# Updated {} Parameter '{}' to '{}'".format(door_info, target_parameter_name, target_param_value)) # Verbose success
                                else:
                                    error_count += 1
                                    print("# Error setting Parameter '{}' for {}. Set method returned false.".format(target_parameter_name, door_info))
                            except SystemException as set_ex:
                                error_count += 1
                                print("# Error setting Parameter '{}' for {}: {}".format(target_parameter_name, door_info, set_ex.Message))
                        # else: # Value is already correct
                            # print("# Info: {} Parameter '{}' already set to '{}'".format(door_info, target_parameter_name, target_param_value)) # Verbose

                    except SystemException as proc_ex:
                        error_count += 1
                        print("# Error processing {}: {}".format(door_info, proc_ex.Message))

                    # Increment unique door update count only once per door
                    if parameter_updated_for_this_door:
                        doors_updated_count +=1

            else:
                # Mark from input data not found among door instances in the model
                skipped_mark_not_found_in_model += 1
                # print("# Skipping Mark '{}' - No matching door instance found in the model.".format(mark_value)) # Verbose
        # End of loop

    elif collection_failed:
         print("# Door collection failed. Cannot process.")
    else:
         print("# No door instances found in the project (Category OST_Doors) to process.")

    # --- Summary ---
    print("--- Door Parameter Update Summary ---")
    print("Target Parameter: '{}'".format(target_parameter_name))
    print("Input Mark/Value Pairs Parsed: {}".format(len(mark_to_param_map)))
    print("Total Door Instances Found: {}".format(doors_found_count))
    print("Marks Processed from Input: {}".format(processed_marks_count))
    print("Total Parameter Updates Applied: {}".format(parameter_updates_count))
    print("Unique Door Elements Updated: {}".format(doors_updated_count)) # Count of distinct doors modified
    print("--- Issues Encountered ---")
    print("Skipped Marks (Not Found in Model): {}".format(skipped_mark_not_found_in_model))
    print("Skipped Updates (Parameter Not Found): {}".format(skipped_no_param))
    print("Skipped Updates (Parameter Read-Only): {}".format(skipped_param_read_only))
    print("Skipped Updates (Parameter Wrong Type): {}".format(skipped_param_wrong_type))
    print("Errors During Update: {}".format(error_count))
    print("--- Script Finished ---")