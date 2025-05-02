# Purpose: This script prefixes room numbers on a specified Revit level.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementLevelFilter,
    Level,
    ElementId,
    Parameter,
    BuiltInParameter
)

# Attempt to import Room class, adding reference if needed
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Ensure RevitAPIArchitecture.dll is available. Error: {}".format(e))

# Define the target level name and the prefix to add
target_level_name = "Level 3"
prefix_to_add = "3-"

# --- Find the target Level ---
target_level_id = ElementId.InvalidElementId
level_collector = FilteredElementCollector(doc).OfClass(Level)
found_level = False
for level in level_collector:
    # Compare level names robustly
    try:
        if level.Name.strip().lower() == target_level_name.strip().lower():
            target_level_id = level.Id
            found_level = True
            break
    except Exception:
        # Skip levels if name cannot be accessed
        continue

# --- Process Rooms if Level Found ---
if found_level and target_level_id != ElementId.InvalidElementId:
    # Create a filter for elements on the target level
    level_filter = ElementLevelFilter(target_level_id)

    # Collect all Room elements on the specified level
    room_collector = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_Rooms)\
        .WhereElementIsNotElementType()\
        .WherePasses(level_filter)

    # Iterate through the collected rooms
    for room in room_collector:
        # Double check it's a Room instance and is placed (has area/location)
        if isinstance(room, Room) and room.Area > 0 and room.Location is not None:
            try:
                # Get the 'Room Number' parameter using BuiltInParameter
                room_number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)

                # Check if the parameter exists and is not read-only
                if room_number_param and not room_number_param.IsReadOnly:
                    current_number = room_number_param.AsString()

                    # Proceed only if the current number is not None or empty
                    if current_number:
                        # Check if the prefix is already present to avoid adding it again
                        if not current_number.startswith(prefix_to_add):
                            new_number = prefix_to_add + current_number
                            # Set the new value (Transaction handled externally)
                            room_number_param.Set(new_number)
                    # else:
                        # Optional: Handle rooms with no existing number if required
                        # print("# INFO: Room ID {} (Name: '{}') has no existing number, skipping.".format(room.Id, room.Name))
                        # pass

            except Exception as e:
                # Log errors encountered while processing a specific room (optional)
                # import traceback
                # room_name_err = "Unknown"
                # try: room_name_err = room.Name
                # except: pass
                # print("# ERROR processing Room ID {} (Name: '{}'): {}".format(room.Id, room_name_err, e))
                # print(traceback.format_exc())
                pass # Continue with the next room even if one fails

# else:
    # Optional: Inform if the target level wasn't found (commented out)
    # if not found_level:
    #     print("# WARNING: Target Level '{}' not found in the project. No rooms were processed.".format(target_level_name))

# Final message (optional, commented out)
# print("# Script finished processing rooms on level '{}'.".format(target_level_name))