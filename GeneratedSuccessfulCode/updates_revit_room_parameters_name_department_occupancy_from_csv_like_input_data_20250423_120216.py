# Purpose: This script updates Revit room parameters (Name, Department, Occupancy) from CSV-like input data.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room
import System

# Input data string (CSV-like format)
# Format: Number,Name,Department,OccupancyLoadFactor (assumed to be Number of People/Occupancy)
input_data = """Number,Name,Department,OccupancyLoadFactor
201,Conference Room,Meeting,5
202,Break Room,Amenity,15
203,Office Cluster,Admin,10"""

# --- Parameter Mapping ---
# Map input headers to Revit BuiltInParameters
# Assuming 'OccupancyLoadFactor' corresponds to the 'Occupancy' parameter (number of people)
param_map = {
    'Number': BuiltInParameter.ROOM_NUMBER,
    'Name': BuiltInParameter.ROOM_NAME,
    'Department': BuiltInParameter.ROOM_DEPARTMENT,
    'OccupancyLoadFactor': BuiltInParameter.ROOM_OCCUPANCY # Maps to Occupancy (integer)
}

# --- Data Processing ---
# Split the input data into lines and skip the header
lines = input_data.strip().split('\n')
header = [h.strip() for h in lines[0].split(',')]
data_rows = [dict(zip(header, [val.strip() for val in line.split(',')])) for line in lines[1:]]

# --- Room Collection ---
# Collect all Room elements into a dictionary keyed by their Room Number for efficient lookup
all_rooms = {}
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for element in room_collector:
    if isinstance(element, Room):
        room = element
        try:
            # Check if the room is placed (has area) before processing
            if room.Area > 1e-6:
                num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                if num_param and num_param.HasValue:
                    room_number = num_param.AsString()
                    if room_number: # Ensure number is not empty
                        all_rooms[room_number] = room
        except Exception as e:
            # Optional: Log errors for rooms that couldn't be processed
            # print("# Error collecting room {0}: {1}".format(element.Id.ToString(), str(e)))
            pass

# --- Update Room Parameters ---
updated_count = 0
not_found_count = 0
error_count = 0

for row_data in data_rows:
    target_number = row_data.get('Number')
    if not target_number:
        # print("# Skipping row with missing 'Number': {0}".format(str(row_data)))
        error_count += 1
        continue

    if target_number in all_rooms:
        room_to_update = all_rooms[target_number]
        try:
            # Update Name
            new_name = row_data.get('Name', None)
            if new_name is not None:
                name_param = room_to_update.get_Parameter(param_map['Name'])
                if name_param and not name_param.IsReadOnly:
                    name_param.Set(new_name)
                else:
                    # print("# Warning: Could not set Name for Room {0}".format(target_number))
                    pass

            # Update Department
            new_dept = row_data.get('Department', None)
            if new_dept is not None:
                dept_param = room_to_update.get_Parameter(param_map['Department'])
                if dept_param and not dept_param.IsReadOnly:
                    dept_param.Set(new_dept)
                else:
                    # print("# Warning: Could not set Department for Room {0}".format(target_number))
                    pass

            # Update Occupancy (assuming OccupancyLoadFactor means Occupancy number)
            new_occupancy_str = row_data.get('OccupancyLoadFactor', None)
            if new_occupancy_str is not None:
                occ_param = room_to_update.get_Parameter(param_map['OccupancyLoadFactor'])
                if occ_param and not occ_param.IsReadOnly:
                    try:
                        # Convert value to integer for Occupancy parameter
                        new_occupancy_int = int(new_occupancy_str)
                        occ_param.Set(new_occupancy_int)
                    except ValueError:
                        # print("# Error: Invalid integer value for OccupancyLoadFactor for Room {0}: '{1}'".format(target_number, new_occupancy_str))
                        error_count += 1
                else:
                    # print("# Warning: Could not set Occupancy for Room {0}".format(target_number))
                    pass

            updated_count += 1
            # print("# Successfully updated parameters for Room {0}".format(target_number))

        except Exception as ex:
            # print("# Error updating Room {0}: {1}".format(target_number, str(ex)))
            error_count += 1
    else:
        # print("# Room with Number '{0}' not found in the project.".format(target_number))
        not_found_count += 1

# Optional: Print summary to pyRevit/RPS console
# print("--- Update Summary ---")
# print("Rooms updated: {0}".format(updated_count))
# print("Rooms not found: {0}".format(not_found_count))
# print("Errors encountered: {0}".format(error_count))

# If no rooms were updated or found, provide a specific message
if updated_count == 0 and not_found_count > 0 and error_count == 0:
    print("# No rooms matching the provided numbers were found.")
elif updated_count == 0 and not_found_count == 0 and error_count == 0:
     print("# No valid room data provided or no placed rooms found in the project.")
# Else: Assume updates happened or errors occurred, messages printed above if uncommented.