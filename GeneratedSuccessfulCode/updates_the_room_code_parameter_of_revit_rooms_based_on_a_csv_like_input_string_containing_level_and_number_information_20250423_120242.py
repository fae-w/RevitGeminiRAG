# Purpose: This script updates the 'Room Code' parameter of Revit rooms based on a CSV-like input string containing Level and Number information.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Level, ElementId, Parameter, StorageType
# Explicitly import Room, handle potential import paths
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        # This path might be needed in older Revit/API versions
        # clr.AddReference('RevitAPIArchitecture') # Typically not needed if RevitAPI is referenced
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        # Use a more standard way to format the error message
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture: {}".format(e))

import System

# Input data string (CSV-like format)
# Format: Level,Number
input_data = """Level,Number
L01,101A
L01,102B
L02,201A"""

# --- Parameter Configuration ---
# The name of the parameter to update.
# IMPORTANT: This assumes 'Room Code' is an existing text-based Project or Shared Parameter.
target_parameter_name = "Room Code"

# --- Data Parsing ---
# Split the input data into lines and skip the header
lines = input_data.strip().split('\n')
if not lines:
     raise System.Exception("Input data is empty.")

header = [h.strip() for h in lines[0].split(',')]
data_rows = []
try:
    # Ensure exactly two values per line after splitting by comma
    for i, line in enumerate(lines[1:], 1): # Start from the second line (index 1)
        parts = [val.strip() for val in line.split(',', 1)] # Split only once
        if len(parts) == 2:
             data_rows.append(dict(zip(header, parts)))
        else:
             # Optional: Log skipped lines due to incorrect format (uncomment if needed)
             # print("# Skipping line {} due to incorrect format: '{}'".format(i + 1, line))
             pass # Silently skip malformed lines

except Exception as parse_error:
    print("# Error parsing input data: {}".format(parse_error))
    # Stop execution if parsing fails
    raise System.Exception("Input data parsing failed.")

if not data_rows:
     print("# No valid data rows parsed from input.")
     # Exit gracefully if no data to process
     import sys
     sys.exit()

# --- Level Collection ---
# Collect all Level elements into a dictionary keyed by their name for efficient lookup
# Corrected dictionary comprehension syntax
levels_by_name = {level.Name: level for level in FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()}

# --- Room Collection ---
# Collect all placed Room elements into a dictionary keyed by (Level Name, Room Number)
# Corrected dictionary initialization
rooms_by_level_and_number = {}
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for element in room_collector:
    # Ensure it's a Room instance (though collector should handle this)
    if isinstance(element, Room):
        room = element
        try:
            # Check if the room is placed (has location) before processing
            if room.Location is not None and room.Area > 0: # Also check Area > 0 for placed rooms
                num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                # Use the Level property, which directly gives the Level element
                level_element = room.Level

                # Check if number parameter exists, has a value, and level exists
                if num_param and num_param.HasValue and level_element:
                    room_number = num_param.AsString()
                    # Get level name directly from the Level element
                    level_name = level_element.Name
                    if room_number and level_name: # Ensure both are non-empty strings
                        lookup_key = (level_name.strip(), room_number.strip())
                        rooms_by_level_and_number[lookup_key] = room
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
level_not_found_count = 0
error_count = 0

for row_data in data_rows:
    # Use .get() with default None to avoid KeyError if header mismatch
    target_level_name = row_data.get('Level')
    target_number = row_data.get('Number')

    if not target_level_name or not target_number:
        # print("# Skipping row with missing Level or Number: {}".format(str(row_data)))
        error_count += 1
        continue

    # Construct the new room code value
    new_room_code = "{}-{}".format(target_level_name, target_number)

    # Check if the level exists in the project (using the collected levels dictionary)
    if target_level_name not in levels_by_name:
        # print("# Level '{}' specified in data not found in the project.".format(target_level_name))
        level_not_found_count += 1
        continue # Skip this row if level doesn't exist

    lookup_key = (target_level_name, target_number)

    if lookup_key in rooms_by_level_and_number:
        room_to_update = rooms_by_level_and_number[lookup_key]
        try:
            # Find the target parameter by name
            room_code_param = room_to_update.LookupParameter(target_parameter_name)

            if room_code_param:
                # Check if parameter storage type is String
                if room_code_param.StorageType == StorageType.String:
                    # Check if parameter is not read-only
                    if not room_code_param.IsReadOnly:
                        current_value = room_code_param.AsString()
                        # Only update if the value is different or currently null/empty
                        if current_value != new_room_code:
                            room_code_param.Set(new_room_code)
                            updated_count += 1
                            # print("# Successfully updated '{}' for Room '{}' on Level '{}' to '{}'".format(target_parameter_name, target_number, target_level_name, new_room_code))
                    else:
                        # print("# Warning: Parameter '{}' is read-only for Room '{}' on Level '{}'.".format(target_parameter_name, target_number, target_level_name))
                        param_read_only_count += 1
                else:
                    # print("# Warning: Parameter '{}' is not a Text parameter for Room '{}' on Level '{}'. Expected StorageType.String, got {}".format(target_parameter_name, target_number, target_level_name, room_code_param.StorageType))
                    param_wrong_type_count += 1
            else:
                # print("# Warning: Parameter '{}' not found for Room '{}' on Level '{}'.".format(target_parameter_name, target_number, target_level_name))
                param_not_found_count += 1

        except System.Exception as ex: # Catch specific Revit API or system exceptions if needed
            # print("# Error updating Room '{}' on Level '{}': {}".format(target_number, target_level_name, str(ex)))
            error_count += 1
    else:
        # print("# Room with Number '{}' on Level '{}' not found or not placed in the project.".format(target_number, target_level_name))
        not_found_count += 1

# Optional: Print summary to pyRevit/RPS console
# print("--- Room Code Update Summary ---")
# print("Total Data Rows Processed: {}".format(len(data_rows)))
# print("Rooms updated: {}".format(updated_count))
# print("Rooms not found (Level/Number match): {}".format(not_found_count))
# print("Levels specified in data not found: {}".format(level_not_found_count))
# print("Target parameter ('{}') not found on room: {}".format(target_parameter_name, param_not_found_count))
# print("Target parameter ('{}') read-only: {}".format(target_parameter_name, param_read_only_count))
# print("Target parameter ('{}') not Text type: {}".format(target_parameter_name, param_wrong_type_count))
# print("Errors encountered (parsing or update): {}".format(error_count))

# Provide a summary message based on results
total_processed = len(data_rows)
total_issues = not_found_count + level_not_found_count + param_not_found_count + param_read_only_count + param_wrong_type_count + error_count

if updated_count > 0:
    print("Successfully updated {} Room(s).".format(updated_count))
    if total_issues > 0:
        print("Encountered {} issues ({} Rooms not found, {} Levels not found, {} Param not found, {} Param read-only, {} Param wrong type, {} Errors). See console for details.".format(
            total_issues, not_found_count, level_not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, error_count))
elif total_processed == 0:
     print("No valid data rows found in the input.")
elif total_issues == total_processed:
    print("No rooms were updated. {} issues encountered ({} Rooms not found, {} Levels not found, {} Param not found, {} Param read-only, {} Param wrong type, {} Errors).".format(
        total_issues, not_found_count, level_not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, error_count))
else: # updated_count == 0 but some rows processed without issue (e.g., value was already correct)
    print("No rooms required updating. {} issues encountered ({} Rooms not found, {} Levels not found, {} Param not found, {} Param read-only, {} Param wrong type, {} Errors).".format(
        total_issues, not_found_count, level_not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, error_count))