# Purpose: This script updates a specified text parameter of Revit elements based on provided IDs and names, converting the names to uppercase.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    ElementId,
    Parameter,
    StorageType,
    Element # Import Element base class for type checking/getting name
)
# No specific .NET types needed beyond Revit API and standard Python types

# --- Input Data ---
# Format: ID,ElementName (Element name to be uppercased and set)
input_data = """ID,ElementName
555,Stair No 1
666,Main Entrance Door"""

# --- Configuration ---
target_parameter_name = "Element Name Upper"

# --- Processing ---
lines = input_data.strip().split('\n')
header = lines[0]
data_lines = lines[1:]

print("# Starting parameter update for '{}'...".format(target_parameter_name))
updated_count = 0
error_count = 0
skipped_count = 0

for line in data_lines:
    try:
        parts = line.strip().split(',', 1) # Split only once to handle names with commas
        if len(parts) != 2:
            print("# Warning: Skipping invalid line format: {}".format(line))
            skipped_count += 1
            continue

        element_id_int = int(parts[0])
        element_name_to_set_upper = parts[1]

        # Convert name to uppercase
        uppercase_name = element_name_to_set_upper.upper()

        target_element_id = ElementId(element_id_int)
        element = doc.GetElement(target_element_id)

        # --- Validate Element ---
        if element is None:
            print("# Error: Element ID {} not found. Skipping.".format(element_id_int))
            error_count += 1
            continue

        print("# Processing Element ID: {}".format(element_id_int))

        # --- Find and Update Parameter ---
        target_param = element.LookupParameter(target_parameter_name)

        if target_param is None:
            print("  - Error: Parameter '{}' not found on element ID {}.".format(target_parameter_name, element_id_int))
            error_count += 1
            continue

        if target_param.IsReadOnly:
            print("  - Error: Parameter '{}' on element ID {} is read-only.".format(target_parameter_name, element_id_int))
            error_count += 1
            continue

        if target_param.StorageType != StorageType.String:
            print("  - Error: Parameter '{}' on element ID {} is not a Text parameter (Type: {}).".format(target_parameter_name, element_id_int, target_param.StorageType))
            error_count += 1
            continue

        try:
            current_value = target_param.AsString()
            if current_value != uppercase_name:
                # --- Modification Start (Requires Transaction - handled externally) ---
                set_success = target_param.Set(uppercase_name)
                # --- Modification End ---
                if set_success:
                    print("  + Success: Set '{}' to '{}'.".format(target_parameter_name, uppercase_name))
                    updated_count += 1
                else:
                     print("  - Error: Failed to set '{}' using Set().".format(target_parameter_name))
                     error_count += 1
            else:
                print("  = Skipped: Parameter '{}' already has value '{}'.".format(target_parameter_name, uppercase_name))
                skipped_count += 1

        except Exception as set_ex:
            print("  - Error: Exception setting parameter '{}' on element ID {}: {}".format(target_parameter_name, element_id_int, set_ex))
            error_count += 1

    except ValueError as ve:
        print("# Error: Could not parse Element ID in line: '{}'. Error: {}".format(line, ve))
        error_count += 1
    except Exception as e:
        print("# Error: Unexpected error processing line '{}': {}".format(line, e))
        error_count += 1

print("# Parameter update finished.")
print("# Summary: Updated: {}, Errors: {}, Skipped/No Change: {}".format(updated_count, error_count, skipped_count))