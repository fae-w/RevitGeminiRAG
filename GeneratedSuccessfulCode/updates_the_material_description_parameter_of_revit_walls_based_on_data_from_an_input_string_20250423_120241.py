# Purpose: This script updates the 'Material Description' parameter of Revit walls based on data from an input string.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    ElementId,
    Wall,
    Parameter,
    BuiltInParameter # Though unlikely to be used for 'Material Description'
)
clr.AddReference('System') # Required for TryParse
from System import Int32 # Required for TryParse

# --- Input Data ---
# Format: ID,WallType,FinishCode
data_string = """ID,WallType,FinishCode
11223,Concrete,PNT-1
33445,Stud,PNT-2
55667,Brick Veneer,BRK-1
11223,Concrete,PNT-3 # Example: Update existing ID with new finish
99999,NonExistentWall,XXX-1 # Example: ID does not exist
88888,Floor,FLR-1 # Example: ID exists but is not a Wall
77777,Concrete,PNT-4 # Example: Wall exists but lacks parameter
66666,Stud,PNT-5 # Example: Wall exists but parameter is read-only (simulate)
"""

# --- Configuration ---
target_parameter_name = "Material Description"

# --- Helper Functions ---
def parse_data(data_str):
    """Parses the input data string into a list of dictionaries."""
    lines = data_str.strip().split('\n')
    parsed_data = []
    if not lines or len(lines) < 2:
        print("# Warning: Input data string is empty or missing header.")
        return parsed_data

    header = [h.strip() for h in lines[0].split(',')]
    required_headers = ['ID', 'WallType', 'FinishCode']
    if not all(h in header for h in required_headers):
        print("# Error: Input data header is missing required columns. Expected: {{}}".format(", ".join(required_headers)))
        return parsed_data # Return empty list on header error

    for i, line in enumerate(lines[1:], 1):
        values = [v.strip() for v in line.split(',')]
        if len(values) == len(header):
            row_dict = dict(zip(header, values))
            # Basic validation
            if not row_dict.get('ID') or not row_dict.get('WallType') or row_dict.get('FinishCode') is None: # FinishCode can be empty string
                 print("# Warning: Skipping malformed or incomplete data line {{}}: {{}}".format(i + 1, line))
                 continue
            parsed_data.append(row_dict)
        else:
            print("# Warning: Skipping malformed data line {{}}: {{}}".format(i + 1, line))
    return parsed_data

# --- Script Core Logic ---

input_rows = parse_data(data_string)

if not input_rows:
    print("# No valid data rows parsed from input string. Script terminated.")
else:
    # Initialize Counters & Logs
    total_rows_processed = 0
    walls_found_count = 0
    walls_updated_count = 0
    rows_skipped_invalid_id = 0
    rows_skipped_element_not_found = 0
    rows_skipped_not_a_wall = 0
    param_update_errors = 0
    param_not_found_count = 0
    param_read_only_count = 0
    param_not_found_ids = set()
    param_read_only_ids = set()

    # Iterate through parsed data rows
    for row_data in input_rows:
        total_rows_processed += 1
        id_str = row_data['ID']
        # Use the WallType string directly from the input data for the description
        wall_type_str_from_data = row_data['WallType']
        finish_code_str = row_data['FinishCode']

        # Construct the target description value using data strings
        target_description = "{{}} / {{}}".format(wall_type_str_from_data, finish_code_str)

        # Validate and get ElementId
        element_id_int = -1
        # Use Int32.TryParse for robust parsing in IronPython
        # --- CORRECTED CODE BLOCK START ---
        element_id_int_ref = clr.Reference[Int32]() # Create the reference for the out parameter
        parse_success = Int32.TryParse(id_str, element_id_int_ref) # Call TryParse, get boolean result

        if parse_success:
             element_id_int = element_id_int_ref.Value # Access the parsed value from the reference
        else:
             element_id_int = -1 # Ensure a default value if parsing fails

        if not parse_success or element_id_int <= 0:
            print("# Warning: Invalid Element ID '{{}}' in row. Skipping.".format(id_str))
            rows_skipped_invalid_id += 1
            continue
        element_id = ElementId(element_id_int)
        # --- CORRECTED CODE BLOCK END ---

        # Get the element
        element = doc.GetElement(element_id)

        if not element:
            # print("# Info: Element with ID {{}} not found in project. Skipping row.".format(id_str)) # Optional info
            rows_skipped_element_not_found += 1
            continue

        # Check if it's a Wall
        if not isinstance(element, Wall):
            # print("# Info: Element ID {{}} found, but it is not a Wall (Type: {{}}). Skipping row.".format(id_str, element.GetType().Name)) # Optional info
            rows_skipped_not_a_wall += 1
            continue

        # We have a valid Wall element
        wall = element
        # Increment count for walls found matching an ID, regardless of update status
        # Note: if an ID appears multiple times, it increments the count each time it's processed
        walls_found_count += 1

        try:
            # Find the target parameter by name
            param = wall.LookupParameter(target_parameter_name)
            # Example: Add fallback for a common built-in parameter if needed (adjust BIP as necessary)
            # if not param:
            #     param = wall.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION) # Example fallback

            if param:
                if not param.IsReadOnly:
                    current_value = param.AsString() # Use AsString for text parameters
                    # Only update if the value is actually different
                    if current_value != target_description:
                        try:
                            # Transaction is handled externally by C# wrapper
                            param.Set(target_description)
                            walls_updated_count += 1
                        except Exception as set_err:
                            print("# Error setting parameter '{{}}' for Wall ID {{}}: {{}}".format(target_parameter_name, wall.Id.IntegerValue, repr(set_err)))
                            param_update_errors += 1
                    # else: # Value is already correct, no action needed, don't count as error or update
                    #    pass
                else:
                    # Parameter is read-only for this wall instance
                    # Only count as read-only if we intended to change it
                    current_value = param.AsString()
                    if current_value != target_description:
                        param_read_only_count += 1
                        param_read_only_ids.add(wall.Id.IntegerValue)
                        # print("# Info: Parameter '{{}}' on Wall ID {{}} is read-only. Cannot update.".format(target_parameter_name, wall.Id.IntegerValue)) # Optional
            else:
                # Parameter not found on this wall instance
                param_not_found_count += 1
                param_not_found_ids.add(wall.Id.IntegerValue)
                # print("# Info: Parameter '{{}}' not found on Wall ID {{}}. Cannot update.".format(target_parameter_name, wall.Id.IntegerValue)) # Optional

        except Exception as e:
            print("# Error processing Wall ID {{}}: {{}}".format(wall.Id.IntegerValue, repr(e)))
            param_update_errors += 1


    # Print Summary
    print("--- Wall '{{}}' Update Summary ---".format(target_parameter_name))
    print("# Data Rows Processed: {{}}".format(total_rows_processed))
    print("# Rows Skipped (Invalid ID Format): {{}}".format(rows_skipped_invalid_id))
    print("# Rows Skipped (Element ID Not Found in Project): {{}}".format(rows_skipped_element_not_found))
    print("# Rows Skipped (Element Found but Not a Wall): {{}}".format(rows_skipped_not_a_wall))
    print("# Wall Instances Found Matching ID in Data: {{}}".format(walls_found_count)) # Note: counts occurrences in data
    print("# Wall Instances Successfully Updated: {{}}".format(walls_updated_count))
    print("# Parameter Update Errors (Set() failed): {{}}".format(param_update_errors))
    print("# Parameter '{{}}' Not Found on Instances: {{}}".format(target_parameter_name, param_not_found_count))
    if param_not_found_ids:
        print("#   (Unique Wall IDs: {{}})".format(", ".join(map(str, sorted(list(param_not_found_ids))))))
    print("# Parameter '{{}}' Read-Only on Instances (Update Prevented): {{}}".format(target_parameter_name, param_read_only_count))
    if param_read_only_ids:
        print("#   (Unique Wall IDs: {{}})".format(", ".join(map(str, sorted(list(param_read_only_ids))))))