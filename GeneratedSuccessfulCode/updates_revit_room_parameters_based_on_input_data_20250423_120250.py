# Purpose: This script updates Revit room parameters based on input data.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Level, ElementId
# Explicitly import Room, handle potential import paths
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture: {}".format(e))

import System

# Input data string (CSV-like format)
# Format: Level,Number,OccupancyCategory
input_data = """Level,Number,OccupancyCategory
Level 1,101,Office
Level 2,101,Storage
Level 2,201,Meeting"""

# --- Parameter Configuration ---
# The name of the parameter to update.
# IMPORTANT: This assumes 'OccupancyCategory' is a text-based Project or Shared Parameter.
# There is no standard BuiltInParameter named 'OccupancyCategory'.
target_parameter_name = "OccupancyCategory"

# --- Data Parsing ---
# Split the input data into lines and skip the header
lines = input_data.strip().split('\n')
header = [h.strip() for h in lines[0].split(',')]
data_rows = []
try:
    data_rows = [dict(zip(header, [val.strip() for val in line.split(',', 2)])) for line in lines[1:]]
except Exception as parse_error:
    print("# Error parsing input data: {}".format(parse_error))
    # Stop execution if parsing fails
    raise System.Exception("Input data parsing failed.")


# --- Level Collection ---
# Collect all Level elements into a dictionary keyed by their name for efficient lookup
levels_by_name = {level.Name: level for level in FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()}

# --- Room Collection ---
# Collect all placed Room elements into a dictionary keyed by (Level Name, Room Number)
rooms_by_level_and_number = {}
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for element in room_collector:
    if isinstance(element, Room):
        room = element
        try:
            # Check if the room is placed (has area/location) before processing
            # Using Location check as Area might be zero for tiny valid rooms sometimes
            if room.Location is not None:
                num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                level_prop = room.Level # Use the Level property

                if num_param and num_param.HasValue and level_prop:
                    room_number = num_param.AsString()
                    level_name = level_prop.Name
                    if room_number and level_name: # Ensure both are valid strings
                        lookup_key = (level_name.strip(), room_number.strip())
                        rooms_by_level_and_number[lookup_key] = room
        except Exception as e:
            # Optional: Log errors for rooms that couldn't be processed
            # print("# Error collecting room {}: {}".format(element.Id.ToString(), str(e)))
            pass

# --- Update Room Parameters ---
updated_count = 0
not_found_count = 0
param_not_found_count = 0
param_read_only_count = 0
level_not_found_count = 0
error_count = 0

for row_data in data_rows:
    target_level_name = row_data.get('Level')
    target_number = row_data.get('Number')
    new_occupancy_category = row_data.get('OccupancyCategory')

    if not target_level_name or not target_number or new_occupancy_category is None:
        # print("# Skipping row with missing Level, Number, or OccupancyCategory: {}".format(str(row_data)))
        error_count += 1
        continue

    # Check if the level exists in the project
    if target_level_name not in levels_by_name:
        # print("# Level '{}' specified in data not found in the project.".format(target_level_name))
        level_not_found_count += 1
        continue # Skip this row if level doesn't exist

    lookup_key = (target_level_name, target_number)

    if lookup_key in rooms_by_level_and_number:
        room_to_update = rooms_by_level_and_number[lookup_key]
        try:
            # Find the target parameter by name
            # Using LookupParameter for flexibility (works for shared/project/some built-in)
            occ_cat_param = room_to_update.LookupParameter(target_parameter_name)

            if occ_cat_param:
                if not occ_cat_param.IsReadOnly:
                    # Assuming the parameter accepts a string value
                    occ_cat_param.Set(new_occupancy_category)
                    updated_count += 1
                    # print("# Successfully updated '{}' for Room '{}' on Level '{}'".format(target_parameter_name, target_number, target_level_name))
                else:
                    # print("# Warning: Parameter '{}' is read-only for Room '{}' on Level '{}'.".format(target_parameter_name, target_number, target_level_name))
                    param_read_only_count += 1
            else:
                # print("# Warning: Parameter '{}' not found for Room '{}' on Level '{}'.".format(target_parameter_name, target_number, target_level_name))
                param_not_found_count += 1

        except Exception as ex:
            # print("# Error updating Room '{}' on Level '{}': {}".format(target_number, target_level_name, str(ex)))
            error_count += 1
    else:
        # print("# Room with Number '{}' on Level '{}' not found in the project.".format(target_number, target_level_name))
        not_found_count += 1

# Optional: Print summary to pyRevit/RPS console
# print("--- Update Summary ---")
# print("Rooms updated: {}".format(updated_count))
# print("Rooms not found (Level/Number match): {}".format(not_found_count))
# print("Levels specified in data not found: {}".format(level_not_found_count))
# print("Target parameter ('{}') not found on room: {}".format(target_parameter_name, param_not_found_count))
# print("Target parameter ('{}') read-only: {}".format(target_parameter_name, param_read_only_count))
# print("Errors encountered (parsing or update): {}".format(error_count))

# Provide a summary message if nothing was updated
if updated_count == 0 and not_found_count == 0 and level_not_found_count == 0 and param_not_found_count == 0 and param_read_only_count == 0 and error_count == 0:
    print("# No rooms matched the criteria or no valid data provided.")
elif updated_count == 0 and (not_found_count > 0 or level_not_found_count > 0 or param_not_found_count > 0 or param_read_only_count > 0):
     print("# No rooms were updated. Check console output (if uncommented) or review reasons: Not Found={}, Level Not Found={}, Param Not Found={}, Param ReadOnly={}".format(not_found_count, level_not_found_count, param_not_found_count, param_read_only_count))
# Else: Assume updates happened or errors occurred, messages printed above if uncommented.