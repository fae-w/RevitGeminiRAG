# Purpose: This script updates the 'Size Description' parameter of Revit windows based on a provided Mark, Width, and Height input.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception handling and Dictionary
from System import Exception as SystemException
from System.Collections.Generic import Dictionary

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance, # Windows are typically FamilyInstances
    Element,
    ElementId,
    BuiltInParameter,
    Parameter,
    StorageType # To check parameter type before setting
)

# --- Configuration ---
# Input data provided in the prompt
input_data_string = """Mark,Width,Height
W-301,950,1800
W-302,1500,1800"""

# Name of the target parameter to set
target_parameter_name = "Size Description"
# BuiltInParameter for 'Mark' value on instances
mark_bip = BuiltInParameter.ALL_MODEL_MARK

# --- Initialization ---
target_sizes = Dictionary[str, str]() # Map Mark (string) to Size Description (string)
updated_count = 0
skipped_mark_not_found = 0
skipped_no_mark_param = 0
skipped_no_target_param = 0
skipped_target_read_only = 0
skipped_target_wrong_type = 0
skipped_input_parse_error = 0
error_count = 0

# --- Step 1: Parse Input Data ---
lines = input_data_string.strip().split('\n')
if len(lines) > 1: # Check if there is data beyond the header
    for i, line in enumerate(lines[1:]): # Skip header line
        parts = line.split(',')
        if len(parts) == 3:
            mark = parts[0].strip()
            width_str = parts[1].strip()
            height_str = parts[2].strip()

            if not mark:
                print("# Warning: Skipping line {} due to empty Mark value: '{}'".format(i + 2, line))
                skipped_input_parse_error += 1
                continue

            try:
                # Validate width and height are integers or floats that can be represented as integers for the string
                int(width_str)
                int(height_str)
                size_description_value = "{}x{}".format(width_str, height_str)

                if mark in target_sizes:
                     print("# Warning: Duplicate Mark value '{}' found in input. Using the last value ('{}').".format(mark, size_description_value))
                target_sizes[mark] = size_description_value
            except ValueError:
                 print("# Warning: Skipping line {} due to non-numeric width/height value(s) '{}', '{}': '{}'".format(i + 2, width_str, height_str, line))
                 skipped_input_parse_error += 1
        else:
            print("# Warning: Skipping malformed line {}: '{}'".format(i + 2, line))
            skipped_input_parse_error += 1
else:
    print("# Error: Input data string does not contain valid data rows.")
    # Stop processing if no valid data to use
    target_sizes = None # Flag that we cannot proceed

# --- Step 2: Collect Windows and Update ---
if target_sizes is not None and target_sizes.Count > 0:
    window_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()
    windows_processed_count = 0

    for window in window_collector:
        windows_processed_count += 1
        if not isinstance(window, FamilyInstance):
            continue # Should not happen with this filter, but good practice

        try:
            # Get the Mark parameter
            mark_param = window.get_Parameter(mark_bip)
            if mark_param is None or not mark_param.HasValue:
                skipped_no_mark_param += 1
                continue

            window_mark = mark_param.AsString()
            if window_mark is None or not window_mark: # Check for empty Mark value
                 skipped_no_mark_param += 1
                 continue

            # Check if this window's mark is in our target list
            if window_mark in target_sizes:
                # Find the target parameter ('Size Description')
                target_param = window.LookupParameter(target_parameter_name)

                if target_param is None:
                    skipped_no_target_param += 1
                    # print("# Info: Window Mark '{}' (ID {}) has no '{}' parameter.".format(window_mark, window.Id, target_parameter_name)) # Debug
                    continue

                if target_param.IsReadOnly:
                    skipped_target_read_only += 1
                    # print("# Info: '{}' parameter for Window Mark '{}' (ID {}) is read-only.".format(target_parameter_name, window_mark, window.Id)) # Debug
                    continue

                # Check parameter storage type - must be String
                if target_param.StorageType != StorageType.String:
                    skipped_target_wrong_type += 1
                    # print("# Info: '{}' parameter for Window Mark '{}' (ID {}) is not a Text parameter (Type: {}).".format(target_parameter_name, window_mark, window.Id, target_param.StorageType)) # Debug
                    continue

                # Get the target value from our dictionary
                target_value = target_sizes[window_mark]

                # Set the new value
                set_result = target_param.Set(target_value)
                if set_result:
                    updated_count += 1
                    # print("# Updated '{}' for Window Mark '{}' (ID {}) to '{}'".format(target_parameter_name, window_mark, window.Id, target_value)) # Debug
                else:
                    error_count += 1
                    print("# Error: Failed to set '{}' for Window Mark '{}' (ID {}) to '{}'. Parameter.Set returned False.".format(target_parameter_name, window_mark, window.Id, target_value))

            else:
                # This window's mark was not in the input data list
                skipped_mark_not_found += 1

        except SystemException as proc_ex:
            error_count += 1
            window_id_str = "Unknown ID"
            try:
                 window_id_str = window.Id.ToString() # Try to get ID for error message
            except:
                 pass
            print("# Error processing Window ID {}: {}".format(window_id_str, proc_ex))

    # --- Final Summary ---
    print("# --- Window '{}' Update Summary ---".format(target_parameter_name))
    print("# Target Marks Parsed: {}".format(target_sizes.Count))
    print("# Windows Checked: {}".format(windows_processed_count))
    print("# Successfully Updated: {}".format(updated_count))
    print("# Skipped (Mark not in input list): {}".format(skipped_mark_not_found))
    print("# Skipped (Window has no Mark value): {}".format(skipped_no_mark_param))
    print("# Skipped (Window has no '{}' param): {}".format(target_parameter_name, skipped_no_target_param))
    print("# Skipped ('{}' param read-only): {}".format(target_parameter_name, skipped_target_read_only))
    print("# Skipped ('{}' param not Text type): {}".format(target_parameter_name, skipped_target_wrong_type))
    print("# Skipped (Input data parsing issues): {}".format(skipped_input_parse_error))
    print("# Errors Encountered: {}".format(error_count))
    if error_count > 0:
        print("# Review errors printed above for details.")

elif target_sizes is None:
    print("# Script aborted due to errors during input data parsing.")
else: # target_sizes.Count == 0
     print("# Script finished. No valid Mark/Width/Height combinations found in the input data.")