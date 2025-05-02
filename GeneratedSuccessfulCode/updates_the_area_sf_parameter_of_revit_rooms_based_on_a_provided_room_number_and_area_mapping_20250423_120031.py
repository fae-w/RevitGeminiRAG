# Purpose: This script updates the 'Area SF' parameter of Revit rooms based on a provided room number and area mapping.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    Parameter,
    ElementId,
    StorageType # Import StorageType for checking parameter type
)
# Import Room class specifically from Architecture namespace
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Error: {}".format(e))

# --- Configuration ---
# Input data provided in the prompt format
input_data = """RoomNumber,AreaSM
105,25.5
106,30.2"""

# Parameter name to update
target_parameter_name = "Area SF" # Case-sensitive parameter name

# Conversion factor
sqm_to_sqft_factor = 10.764

# --- Processing ---

# Dictionary to store mapping from Room Number to Area in Square Feet
room_updates = {}

# Parse the input data
lines = input_data.strip().split('\n')
if len(lines) > 1: # Check if there is data beyond the header
    header = lines[0].split(',')
    # Optional: Validate header if needed
    # if header[0].strip() != "RoomNumber" or header[1].strip() != "AreaSM":
    #     print("# Error: Input data header format is incorrect. Expected 'RoomNumber,AreaSM'.")

    for i, line in enumerate(lines[1:]):
        try:
            parts = line.strip().split(',')
            if len(parts) == 2:
                room_number_str = parts[0].strip()
                area_sm_str = parts[1].strip()
                area_sm = float(area_sm_str) # Convert area in square meters to float
                area_sf = area_sm * sqm_to_sqft_factor # Convert to square feet
                room_updates[room_number_str] = area_sf # Store RoomNumber (as string) and Area (as float in sqft)
            else:
                print("# Warning: Skipping malformed line #{}: '{}'".format(i+2, line)) # Line number is i+2 because we skip header and start from 1
        except ValueError:
            print("# Warning: Skipping line #{}: Could not parse AreaSM as a number in '{}'".format(i+2, line))
        except Exception as e:
            print("# Warning: Error processing line #{}: '{}'. Error: {}".format(i+2, line, e))
else:
    print("# Error: Input data is empty or contains only a header.")


# Collect all Room elements
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Iterate through rooms and update the parameter if found in the input data
updated_count = 0
not_found_rooms = list(room_updates.keys()) # Keep track of rooms from input not found in model
param_not_found = []
param_read_only = []
param_wrong_type = []

for element in collector:
    # Ensure the element is a Room and is placed (has an Area > 0 or Location is not None)
    if isinstance(element, Room) and element.Area > 0:
        room = element
        try:
            # Get the Room Number parameter
            number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)

            if number_param and number_param.HasValue:
                current_room_number = number_param.AsString()

                # Check if this room number is in our update list
                if current_room_number in room_updates:
                    area_sf_to_set = room_updates[current_room_number]

                    # Find the target parameter ('Area SF') on this room
                    target_param = room.LookupParameter(target_parameter_name)

                    if target_param:
                        # Check if parameter is read-only
                        if not target_param.IsReadOnly:
                             # Check if parameter storage type is Double (suitable for area/number)
                             if target_param.StorageType == StorageType.Double:
                                 target_param.Set(area_sf_to_set)
                                 updated_count += 1
                                 # Remove the room number from the not_found list as it was processed
                                 if current_room_number in not_found_rooms:
                                     not_found_rooms.remove(current_room_number)
                             else:
                                 # Parameter type mismatch
                                 if current_room_number not in param_wrong_type:
                                     param_wrong_type.append(current_room_number)
                                 print("# Warning: Parameter '{}' on Room '{}' is not of type Number/Double. Cannot set value.".format(target_parameter_name, current_room_number))
                        else:
                            # Parameter is read-only
                            if current_room_number not in param_read_only:
                                param_read_only.append(current_room_number)
                            print("# Warning: Parameter '{}' on Room '{}' is read-only.".format(target_parameter_name, current_room_number))
                    else:
                        # Parameter not found on this room instance
                        if current_room_number not in param_not_found:
                             param_not_found.append(current_room_number)
                        # print("# Warning: Parameter '{}' not found on Room '{}' (ID: {}).".format(target_parameter_name, current_room_number, room.Id))
                        # No need to remove from not_found_rooms here, it will be handled below if it was in the input list

        except Exception as e:
            room_num_err = "Unknown"
            try:
                num_p = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                if num_p and num_p.HasValue:
                    room_num_err = num_p.AsString()
            except: pass
            print("# Error processing Room '{}' (ID: {}): {}".format(room_num_err, element.Id, e))


# --- Final Report ---
print("# --- Update Summary ---")
print("# Successfully updated '{}' parameter for {} rooms.".format(target_parameter_name, updated_count))

if not_found_rooms:
    print("# Warning: The following Room Numbers from the input data were not found or not placed in the model: {}".format(", ".join(not_found_rooms)))
if param_not_found:
     # Filter param_not_found to only include those that were originally in the input list
     relevant_param_not_found = [rn for rn in param_not_found if rn in room_updates]
     if relevant_param_not_found:
         print("# Warning: Parameter '{}' was not found on the following Room Numbers (which were found in the model): {}".format(target_parameter_name, ", ".join(relevant_param_not_found)))
if param_read_only:
     print("# Warning: Parameter '{}' was read-only for the following Room Numbers: {}".format(target_parameter_name, ", ".join(param_read_only)))
if param_wrong_type:
     print("# Warning: Parameter '{}' had an incorrect storage type (expected Double) for the following Room Numbers: {}".format(target_parameter_name, ", ".join(param_wrong_type)))