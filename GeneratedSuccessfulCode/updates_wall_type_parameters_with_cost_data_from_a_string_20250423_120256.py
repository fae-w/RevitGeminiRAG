# Purpose: This script updates wall type parameters with cost data from a string.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallType,
    Parameter,
    BuiltInParameter # Often useful for type names
)
clr.AddReference('System') # Required for Double.TryParse
from System import Double # Required for Double.TryParse

# --- Input Data ---
# Format: TypeName,Cost
data_string = """TypeName,Cost
EXT-CurtainWall,450
INT-GlazedPartition,300
EXT-BrickOnCMU, 180.50
INT-Stud-NotFound, 90
EXT-ReadOnlyParamType, 200 # Simulate type where param is read-only
INT-ParamNotFoundType, 150 # Simulate type missing the parameter
INT-InvalidCostType, ABC # Simulate non-numeric cost
"""

# --- Configuration ---
target_parameter_name = "Rough Cost per Sq M"

# --- Helper Functions ---
def parse_data(data_str):
    """Parses the input data string into a list of dictionaries."""
    lines = data_str.strip().split('\n')
    parsed_data = []
    if not lines or len(lines) < 2:
        print("# Warning: Input data string is empty or missing header.")
        return parsed_data

    header = [h.strip() for h in lines[0].split(',')]
    required_headers = ['TypeName', 'Cost']
    if not all(h in header for h in required_headers):
        print("# Error: Input data header is missing required columns. Expected: {}".format(", ".join(required_headers)))
        return parsed_data # Return empty list on header error

    for i, line in enumerate(lines[1:], 1):
        values = [v.strip() for v in line.split(',')]
        if len(values) == len(header):
            row_dict = dict(zip(header, values))
            # Basic validation
            if not row_dict.get('TypeName') or row_dict.get('Cost') is None: # Cost can be empty string initially
                 print("# Warning: Skipping malformed or incomplete data line {}: {}".format(i + 1, line))
                 continue
            parsed_data.append(row_dict)
        else:
            print("# Warning: Skipping malformed data line {}: {}".format(i + 1, line))
    return parsed_data

# --- Script Core Logic ---

input_rows = parse_data(data_string)

if not input_rows:
    print("# No valid data rows parsed from input string. Script terminated.")
else:
    # Collect all WallType elements in the document and create a lookup map
    wall_type_collector = FilteredElementCollector(doc).OfClass(WallType)
    # Use element.Name for WallType name retrieval (ElementType.Name often works too)
    wall_type_map = {wt.Name: wt for wt in wall_type_collector}

    # Initialize Counters & Logs
    total_rows_processed = 0
    types_processed_count = 0
    types_updated_count = 0
    rows_skipped_type_not_found = 0
    rows_skipped_invalid_cost = 0
    param_update_errors = 0
    param_not_found_count = 0
    param_read_only_count = 0
    param_not_found_types = set()
    param_read_only_types = set()
    updated_type_names = []

    # Iterate through parsed data rows
    for row_data in input_rows:
        total_rows_processed += 1
        type_name = row_data['TypeName']
        cost_str = row_data['Cost']

        # Find the WallType
        wall_type = wall_type_map.get(type_name)

        if not wall_type:
            # print("# Info: WallType '{}' not found in the project. Skipping row.".format(type_name)) # Optional info
            rows_skipped_type_not_found += 1
            continue

        types_processed_count += 1

        # Validate and parse the cost value
        cost_double_ref = clr.Reference[Double]() # Create the reference for the out parameter
        parse_success = Double.TryParse(cost_str, cost_double_ref)

        if not parse_success:
            print("# Warning: Invalid cost value '{}' for WallType '{}'. Skipping update.".format(cost_str, type_name))
            rows_skipped_invalid_cost += 1
            continue

        target_cost_value = cost_double_ref.Value # Access the parsed double value

        try:
            # Find the target parameter by name on the WallType
            param = wall_type.LookupParameter(target_parameter_name)

            if param:
                if not param.IsReadOnly:
                    # Get current value to avoid unnecessary updates (optional, but good practice)
                    current_value = None
                    try:
                        current_value = param.AsDouble()
                    except: # Handle cases where AsDouble might fail if param stores text unexpectedly
                         pass

                    # Only update if the value is actually different
                    # Use a small tolerance for floating-point comparison
                    tolerance = 0.0001
                    if current_value is None or abs(current_value - target_cost_value) > tolerance:
                        try:
                            # Transaction is handled externally by C# wrapper
                            param.Set(target_cost_value)
                            types_updated_count += 1
                            updated_type_names.append(type_name)
                        except Exception as set_err:
                            print("# Error setting parameter '{}' for WallType '{}': {}".format(target_parameter_name, type_name, repr(set_err)))
                            param_update_errors += 1
                    # else: # Value is already correct, no action needed
                    #    pass
                else:
                    # Parameter is read-only for this wall type
                    # Only count as read-only if we intended to change it (check if value differs)
                    current_value = None
                    try:
                        current_value = param.AsDouble()
                    except:
                         pass
                    if current_value is None or abs(current_value - target_cost_value) > 0.0001:
                        param_read_only_count += 1
                        param_read_only_types.add(type_name)
                        # print("# Info: Parameter '{}' on WallType '{}' is read-only. Cannot update.".format(target_parameter_name, type_name)) # Optional
            else:
                # Parameter not found on this wall type
                param_not_found_count += 1
                param_not_found_types.add(type_name)
                # print("# Info: Parameter '{}' not found on WallType '{}'. Cannot update.".format(target_parameter_name, type_name)) # Optional

        except Exception as e:
            print("# Error processing WallType '{}': {}".format(type_name, repr(e)))
            param_update_errors += 1


    # Print Summary
    print("--- Wall Type '{}' Update Summary ---".format(target_parameter_name))
    print("# Data Rows Processed: {}".format(total_rows_processed))
    print("# Rows Skipped (WallType Not Found in Project): {}".format(rows_skipped_type_not_found))
    print("# Rows Skipped (Invalid Cost Format): {}".format(rows_skipped_invalid_cost))
    print("# Wall Types Found and Processed: {}".format(types_processed_count))
    print("# Wall Types Successfully Updated: {}".format(types_updated_count))
    if updated_type_names:
        print("#   Updated Types: {}".format(", ".join(updated_type_names)))
    print("# Parameter Update Errors (Set() failed or other exception): {}".format(param_update_errors))
    print("# Parameter '{}' Not Found on Types: {}".format(target_parameter_name, param_not_found_count))
    if param_not_found_types:
        print("#   (Types: {})".format(", ".join(sorted(list(param_not_found_types)))))
    print("# Parameter '{}' Read-Only on Types (Update Prevented): {}".format(target_parameter_name, param_read_only_count))
    if param_read_only_types:
        print("#   (Types: {})".format(", ".join(sorted(list(param_read_only_types)))))