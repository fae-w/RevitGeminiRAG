# Purpose: This script updates Revit room finish parameters from CSV input.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter, StorageType
# Explicitly import Room, handle potential import paths
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        from Autodesk.Revit.DB import Room # Might be directly under DB in some versions
    except ImportError:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB or Autodesk.Revit.DB.Architecture")

import sys
import System

# Input data string (CSV format)
# Format: Number,FloorFinish,WallFinish,CeilingFinish
input_data = """Number,FloorFinish,WallFinish,CeilingFinish
401,CPT-1,PNT-1,
402,,PNT-2,ACT-1
403,VCT-1,,GWB"""

# --- Parameter Mapping ---
# Map input column headers to BuiltInParameter enums
param_map = {
    "FloorFinish": BuiltInParameter.ROOM_FINISH_FLOOR,
    "WallFinish": BuiltInParameter.ROOM_FINISH_WALL,
    "CeilingFinish": BuiltInParameter.ROOM_FINISH_CEILING
}
# Also store string names for potential LookupParameter fallback or error messages
param_names = {
    "FloorFinish": "Floor Finish",
    "WallFinish": "Wall Finish",
    "CeilingFinish": "Ceiling Finish"
}

# --- Data Parsing ---
data_to_update = {}
lines = input_data.strip().split('\n')
if not lines or len(lines) < 2:
    print("# Error: Input data is empty or contains only a header.")
    sys.exit()

header = [h.strip() for h in lines[0].split(',')]
expected_headers = ["Number", "FloorFinish", "WallFinish", "CeilingFinish"]

# Basic header validation
if header != expected_headers:
    print("# Error: Input data header does not match expected format: {}".format(",".join(expected_headers)))
    sys.exit()

parsed_rows = 0
parsing_errors = 0
for i, line in enumerate(lines[1:], 1): # Start from the second line (index 1)
    parts = [val.strip() for val in line.split(',')]
    if len(parts) == len(expected_headers):
        room_number = parts[0]
        if room_number: # Ensure room number is not empty
            finishes = {
                "FloorFinish": parts[1],
                "WallFinish": parts[2],
                "CeilingFinish": parts[3]
            }
            data_to_update[room_number] = finishes
            parsed_rows += 1
        else:
            # print("# Skipping line {} due to empty Room Number: '{}'".format(i + 1, line))
            parsing_errors += 1
    else:
        # print("# Skipping line {} due to incorrect column count: '{}'".format(i + 1, line))
        parsing_errors += 1

if not data_to_update:
    print("# No valid data rows parsed from input.")
    if parsing_errors > 0:
        print("# Encountered {} parsing errors.".format(parsing_errors))
    sys.exit()

# --- Room Collection ---
rooms_by_number = {}
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for element in room_collector:
    if isinstance(element, Room):
        room = element
        # Check if the room is placed (has location and area)
        if room.Location is not None and room.Area > 0:
            num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if num_param and num_param.HasValue:
                room_number_val = num_param.AsString()
                if room_number_val and room_number_val.strip():
                    rooms_by_number[room_number_val.strip()] = room

# --- Update Room Parameters ---
update_success_count = 0
update_skipped_blank_count = 0
update_skipped_no_change_count = 0
rooms_not_found_count = 0
param_not_found_count = 0
param_read_only_count = 0
param_wrong_type_count = 0
update_error_count = 0

processed_room_numbers = set()

for room_num, finishes in data_to_update.items():
    processed_room_numbers.add(room_num)
    if room_num in rooms_by_number:
        room_to_update = rooms_by_number[room_num]
        room_updated_flag = False # Flag to check if any param was updated for this room

        for finish_key, new_value in finishes.items():
            if new_value: # Only process if the new value is not blank
                bip = param_map.get(finish_key)
                param_name_str = param_names.get(finish_key, finish_key) # Fallback to key if name not mapped

                if bip:
                    param = room_to_update.get_Parameter(bip)
                else:
                    # Fallback to LookupParameter if BIP is not defined (though it should be here)
                    param = room_to_update.LookupParameter(param_name_str)

                if param:
                    if param.StorageType == StorageType.String:
                        if not param.IsReadOnly:
                            current_value = param.AsString()
                            # Treat None or empty string from Revit as equivalent for comparison
                            current_value_normalized = current_value if current_value else ""
                            if current_value_normalized != new_value:
                                try:
                                    param.Set(new_value)
                                    update_success_count += 1
                                    room_updated_flag = True
                                except System.Exception as ex:
                                    # print("# Error setting parameter '{}' for Room '{}': {}".format(param_name_str, room_num, str(ex)))
                                    update_error_count += 1
                            else:
                                # Value is already correct
                                update_skipped_no_change_count += 1
                        else:
                            # print("# Warning: Parameter '{}' is read-only for Room '{}'.".format(param_name_str, room_num))
                            param_read_only_count += 1
                    else:
                        # print("# Warning: Parameter '{}' is not a Text parameter for Room '{}'. Expected StorageType.String, got {}".format(param_name_str, room_num, param.StorageType))
                        param_wrong_type_count += 1
                else:
                    # print("# Warning: Parameter '{}' not found for Room '{}'.".format(param_name_str, room_num))
                    param_not_found_count += 1
            else:
                # Input value was blank, skip update for this parameter
                update_skipped_blank_count += 1
                
    else:
        # print("# Room with Number '{}' not found or not placed in the project.".format(room_num))
        rooms_not_found_count += 1

# --- Summary ---
total_data_rows = len(data_to_update)
total_params_processed = update_success_count + update_skipped_blank_count + update_skipped_no_change_count + \
                         param_not_found_count + param_read_only_count + param_wrong_type_count + update_error_count
total_issues = rooms_not_found_count + param_not_found_count + param_read_only_count + param_wrong_type_count + update_error_count + parsing_errors


if update_success_count > 0:
    print("Successfully updated {} parameter(s).".format(update_success_count))
    if total_issues > 0 or update_skipped_blank_count > 0 or update_skipped_no_change_count > 0 :
         print("Skipped: {} (blank input), {} (no change).".format(update_skipped_blank_count, update_skipped_no_change_count))
         print("Issues: {} (Room not found), {} (Param not found), {} (Param read-only), {} (Param wrong type), {} (Update errors), {} (Parsing errors).".format(
             rooms_not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, update_error_count, parsing_errors))

elif total_data_rows == 0 and parsing_errors > 0:
     print("No valid data rows found in input due to {} parsing errors.".format(parsing_errors))
elif total_data_rows == 0:
     print("No data provided to process.")
elif total_issues + update_skipped_blank_count + update_skipped_no_change_count == total_params_processed:
     print("No parameters required updating.")
     print("Skipped: {} (blank input), {} (no change).".format(update_skipped_blank_count, update_skipped_no_change_count))
     if total_issues > 0:
         print("Issues: {} (Room not found), {} (Param not found), {} (Param read-only), {} (Param wrong type), {} (Update errors), {} (Parsing errors).".format(
             rooms_not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, update_error_count, parsing_errors))
else: # Should not happen if logic is correct, but as a fallback
    print("Processing complete. Updates: {}, Skipped (Blank): {}, Skipped (No Change): {}, Issues: {}".format(
        update_success_count, update_skipped_blank_count, update_skipped_no_change_count, total_issues))

# Optional: Print detailed summary to console
# print("--- Finish Parameter Update Summary ---")
# print("Total Data Rows Parsed: {} ({} parsing errors)".format(len(data_to_update), parsing_errors))
# print("Parameters Updated: {}".format(update_success_count))
# print("Updates Skipped (Blank Input): {}".format(update_skipped_blank_count))
# print("Updates Skipped (No Change): {}".format(update_skipped_no_change_count))
# print("Rooms Not Found: {}".format(rooms_not_found_count))
# print("Parameter Not Found: {}".format(param_not_found_count))
# print("Parameter Read-Only: {}".format(param_read_only_count))
# print("Parameter Wrong Type: {}".format(param_wrong_type_count))
# print("Update Errors: {}".format(update_error_count))