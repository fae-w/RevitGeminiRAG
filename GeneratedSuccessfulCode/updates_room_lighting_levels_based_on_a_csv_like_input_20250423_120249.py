# Purpose: This script updates room lighting levels based on a CSV-like input.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter, StorageType, ElementId
# Explicitly import Room, handle potential import paths
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        # Older Revit/API versions might require this path
        from Autodesk.Revit.DB import Room # Some categories are directly in DB namespace too
    except ImportError:
        # If still not found, raise a clearer error
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture or Autodesk.Revit.DB")

import System

# Input data string (CSV-like format)
# Format: Number,LightingLevel
input_data = """Number,LightingLevel
401,300
402,500
403,150"""

# --- Parameter Configuration ---
# The name of the parameter to update.
# IMPORTANT: This assumes 'Required Lighting Level (Lux)' is an existing numerical (Integer or Number/Double) INSTANCE parameter on Rooms.
target_parameter_name = "Required Lighting Level (Lux)"

# --- Data Parsing ---
lines = input_data.strip().split('\n')
if not lines or len(lines) < 2:
    print("# Error: Input data is empty or missing header/data rows.")
    import sys
    sys.exit()

header = [h.strip() for h in lines[0].split(',')]
data_rows = []
parsing_errors = 0
try:
    required_headers = ['Number', 'LightingLevel']
    if header != required_headers:
         print("# Error: Input data header format incorrect. Expected 'Number,LightingLevel', got '{}'".format(",".join(header)))
         import sys
         sys.exit()

    for i, line in enumerate(lines[1:], 1): # Start from the second line
        parts = [val.strip() for val in line.split(',', 1)] # Split only once
        if len(parts) == 2:
            # Basic validation: Check if LightingLevel seems numeric
            if parts[1].isdigit() or (parts[1].replace('.', '', 1).isdigit() and parts[1].count('.') <= 1):
                 data_rows.append(dict(zip(header, parts)))
            else:
                 # print("# Skipping line {}: 'LightingLevel' ('{}') is not a valid number.".format(i + 1, parts[1]))
                 parsing_errors += 1
        else:
            # print("# Skipping line {} due to incorrect format: '{}'".format(i + 1, line))
            parsing_errors += 1

except Exception as parse_error:
    print("# Error parsing input data: {}".format(parse_error))
    # Stop execution if parsing fails
    raise System.Exception("Input data parsing failed.")

if not data_rows:
     print("# No valid data rows parsed from input.")
     if parsing_errors > 0:
          print("# Encountered {} parsing errors.".format(parsing_errors))
     import sys
     sys.exit()

# --- Room Collection ---
# Collect all placed Room elements into a dictionary keyed by their Room Number
# Assumption: Room Numbers are unique in the project. If not, this will only store the *last* room encountered with a given number.
rooms_by_number = {}
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for element in room_collector:
    # Ensure it's a Room instance
    if isinstance(element, Room):
        room = element
        try:
            # Check if the room is placed (has location and area > 0) before processing
            if room.Location is not None and room.Area > 0:
                num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)

                # Check if number parameter exists and has a value
                if num_param and num_param.HasValue:
                    room_number = num_param.AsString()
                    if room_number: # Ensure it's a non-empty string
                        lookup_key = room_number.strip()
                        # If numbers are not unique, consider storing a list of rooms per number
                        # For now, overwrite if duplicate number found (last one wins)
                        rooms_by_number[lookup_key] = room
        except Exception as e:
            # Optional: Log errors for rooms that couldn't be processed
            # print("# Error collecting room ID {}: {}".format(element.Id.ToString(), str(e)))
            pass

# --- Update Room Parameters ---
updated_count = 0
not_found_count = 0
param_not_found_count = 0
param_read_only_count = 0
param_wrong_type_count = 0
conversion_error_count = 0
error_count = 0

for row_data in data_rows:
    target_number = row_data.get('Number')
    lighting_level_str = row_data.get('LightingLevel')

    if not target_number or lighting_level_str is None: # Should not happen due to parsing check, but good practice
        # print("# Skipping row with missing Number or LightingLevel: {}".format(str(row_data)))
        error_count += 1
        continue

    if target_number in rooms_by_number:
        room_to_update = rooms_by_number[target_number]
        try:
            # Find the target parameter by name
            target_param = room_to_update.LookupParameter(target_parameter_name)

            if target_param:
                if not target_param.IsReadOnly:
                    storage_type = target_param.StorageType
                    value_set = False
                    try:
                        if storage_type == StorageType.Integer:
                            value_to_set = int(lighting_level_str)
                            target_param.Set(value_to_set)
                            value_set = True
                        elif storage_type == StorageType.Double:
                             # Use float for conversion from string, Revit API Set(Double) takes float
                            value_to_set = float(lighting_level_str)
                            target_param.Set(value_to_set)
                            value_set = True
                        elif storage_type == StorageType.String:
                            # Less likely for 'Lux', but handle it
                            target_param.Set(lighting_level_str)
                            value_set = True
                        else:
                            # Parameter type is not Integer, Double, or String
                            # print("# Warning: Parameter '{}' for Room '{}' has an unsupported StorageType: {}. Cannot set value '{}'.".format(target_parameter_name, target_number, storage_type, lighting_level_str))
                            param_wrong_type_count += 1

                        if value_set:
                            updated_count += 1
                            # print("# Successfully updated '{}' for Room '{}' to '{}'".format(target_parameter_name, target_number, lighting_level_str))

                    except ValueError:
                        # Error converting string to number
                        # print("# Error: Could not convert '{}' to the required type ({}) for parameter '{}' in Room '{}'.".format(lighting_level_str, storage_type, target_parameter_name, target_number))
                        conversion_error_count += 1
                    except Exception as set_ex:
                         # Catch other potential errors during Set
                         # print("# Error setting parameter '{}' for Room '{}': {}".format(target_parameter_name, target_number, str(set_ex)))
                         error_count += 1

                else:
                    # print("# Warning: Parameter '{}' is read-only for Room '{}'.".format(target_parameter_name, target_number))
                    param_read_only_count += 1
            else:
                # print("# Warning: Parameter '{}' not found for Room '{}'.".format(target_parameter_name, target_number))
                param_not_found_count += 1

        except System.Exception as ex:
            # print("# Error processing Room '{}': {}".format(target_number, str(ex)))
            error_count += 1
    else:
        # print("# Room with Number '{}' not found or not placed in the project.".format(target_number))
        not_found_count += 1

# --- Summary ---
total_processed = len(data_rows)
total_issues = not_found_count + param_not_found_count + param_read_only_count + param_wrong_type_count + conversion_error_count + error_count + parsing_errors

if updated_count > 0:
    summary_message = "Successfully updated {} Room(s).".format(updated_count)
    if total_issues > 0:
        summary_message += " Encountered {} issues ({} Parse Err, {} Not Found, {} Param Not Found, {} Read-Only, {} Wrong Type, {} Conversion Err, {} Other Err).".format(
            total_issues, parsing_errors, not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, conversion_error_count, error_count)
    print(summary_message)
elif total_processed == 0 and parsing_errors > 0:
     print("No rooms updated. {} parsing errors prevented processing.".format(parsing_errors))
elif total_issues == total_processed + parsing_errors and total_processed > 0:
    print("No rooms were updated. {} issues encountered ({} Parse Err, {} Not Found, {} Param Not Found, {} Read-Only, {} Wrong Type, {} Conversion Err, {} Other Err).".format(
        total_issues, parsing_errors, not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, conversion_error_count, error_count))
elif updated_count == 0 and total_issues == 0 and total_processed > 0:
    print("No rooms required updating (perhaps values were already correct).")
else: # Should cover cases where parsing errors occurred but some rows were still processed, or other edge cases
    print("Operation finished. {} rooms updated. {} issues encountered ({} Parse Err, {} Not Found, {} Param Not Found, {} Read-Only, {} Wrong Type, {} Conversion Err, {} Other Err).".format(
        updated_count, total_issues, parsing_errors, not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, conversion_error_count, error_count))

# Optional: More detailed console logging (uncomment print statements above) for debugging.