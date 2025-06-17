# Purpose: This script updates the floor finish parameter of Revit rooms based on data from a CSV string.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter

# Attempt to import Room class
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    # Fallback if RevitAPIArchitecture is not automatically referenced
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Assembly might be missing or blocked. Original error: {{}}".format(e))

# --- CSV Data for Room Floor Finishes ---
# Format: RoomNumber,FloorFinish (Header ignored)
csv_data_string = """RoomNumber,FloorFinish
G.01,VCT-1
G.02,CPT-2
G.03,VCT-1"""

# --- Parse CSV Data into a Dictionary ---
room_finish_map = {}
lines = csv_data_string.strip().split('\n')
if len(lines) > 1: # Check if there's data beyond the header
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if line:
            parts = line.split(',', 1) # Split only on the first comma
            if len(parts) == 2:
                room_number = parts[0].strip()
                floor_finish = parts[1].strip()
                if room_number: # Ensure room number is not empty
                    room_finish_map[room_number] = floor_finish
            # else:
                # print("# WARNING: Skipping malformed CSV line: {}".format(line))

# --- Collect Rooms and Update Floor Finish Parameter ---
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

updated_count = 0
skipped_count = 0
error_count = 0
rooms_not_found = list(room_finish_map.keys()) # Keep track of rooms from CSV not found in model

if not room_finish_map:
    print("# WARNING: No valid Room Number to Floor Finish mappings found in the provided data.")
else:
    for room in collector:
        if not isinstance(room, Room):
            continue

        # Skip unplaced rooms
        if room.Location is None:
            skipped_count += 1
            continue

        try:
            # --- Get Room Number ---
            room_number = None
            number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if number_param and number_param.HasValue:
                number_val = number_param.AsString()
                if number_val and number_val.strip():
                    room_number = number_val.strip()

            # If no valid room number found, skip this room
            if not room_number:
                skipped_count += 1
                continue

            # --- Check if this room number is in our mapping ---
            if room_number in room_finish_map:
                # Mark this room number as found
                if room_number in rooms_not_found:
                    rooms_not_found.remove(room_number)

                target_finish = room_finish_map[room_number]

                # --- Get Floor Finish Parameter ---
                # Using BuiltInParameter based on API documentation context (ParameterTypeIdRoomFinishFloor)
                finish_param = room.get_Parameter(BuiltInParameter.ROOM_FINISH_FLOOR)

                # --- Update Parameter if possible and necessary ---
                if finish_param and not finish_param.IsReadOnly:
                    current_finish = finish_param.AsString()
                    # Update only if the value is different
                    if current_finish != target_finish:
                        try:
                            finish_param.Set(target_finish)
                            updated_count += 1
                        except Exception as set_ex:
                            print("# ERROR: Failed to set Floor Finish for Room '{{}}' (ID: {{}}): {{}}".format(room_number, room.Id.ToString(), str(set_ex)))
                            error_count += 1
                    # else: # Room already has the correct finish
                        # skipped_count += 1 # Optionally count rooms that already match
                else:
                    # Parameter not found or read-only
                    skipped_count += 1
                    # print("# INFO: Floor Finish parameter not found or read-only for Room: '{}'".format(room_number))

            else:
                # Room number exists in model but not in the mapping
                skipped_count += 1

        except Exception as e:
            error_count += 1
            try:
                # Try to log the specific room ID causing the error
                print("# ERROR: Failed to process Room ID {{}}: {{}}".format(room.Id.ToString(), str(e)))
            except:
                print("# ERROR: Failed to process a Room element: {{}}".format(str(e)))

# Optional: Print summary to console
# print("--- Room Floor Finish Update Summary ---")
# print("Rooms updated: {}".format(updated_count))
# print("Rooms skipped (unplaced, no number, not in mapping, already correct, or param issue): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# if rooms_not_found:
#    print("Room Numbers from CSV not found in model: {}".format(", ".join(rooms_not_found)))