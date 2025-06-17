# Purpose: This script identifies doors accessing corridor rooms and sets a shared parameter to indicate corridor access.

# Purpose: This script identifies doors accessing rooms with "Corridor" in their name and sets a shared parameter accordingly.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')

from System.Collections.Generic import List, HashSet # HashSet used for efficient ID lookup

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    ElementId,
    BuiltInParameter,
    Parameter,
    Phase,
    StorageType
)
# Import classes from specific namespaces
from Autodesk.Revit.DB.Architecture import Room # Removed Door from this line

# --- Configuration ---
SHARED_PARAM_NAME = "Corridor Access Door" # The name of the shared parameter to set
ROOM_NAME_SUBSTRING = "Corridor" # Case-insensitive substring to find in Room names
TARGET_PARAM_VALUE = "Yes" # The string value to set for String parameters
TARGET_PARAM_VALUE_INT = 1 # The integer value to set for Integer (Yes/No) parameters

# --- Main Script ---

# 1. Find IDs of all Rooms containing the substring in their name
# Using .NET HashSet for potentially better performance with Contains() lookups
corridor_room_ids = HashSet[ElementId]()
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in room_collector:
    # Ensure it's a Room element and it's placed (Location is not null checks spatial rooms)
    # Unplaced rooms (e.g., redundant rooms) won't have valid boundaries or From/To relationships
    if isinstance(room, Room) and room.Location is not None:
        try:
            # Get the ROOM_NAME parameter using BuiltInParameter for reliability
            name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
            if name_param and name_param.HasValue:
                room_name = name_param.AsString()
                # Check if name is not None and contains the substring (case-insensitive)
                if room_name and ROOM_NAME_SUBSTRING.lower() in room_name.lower():
                    corridor_room_ids.Add(room.Id) # Add the ElementId to the HashSet
        except Exception as e_room_name:
            # Silently ignore rooms where name cannot be read or causes errors
            # print("# Warning: Could not read name for Room ID: {{{{}}}}. Error: {{{{}}}}".format(room.Id, e_room_name)) # Optional debug for troubleshooting
            pass

# 2. Proceed only if any rooms matching the criteria were found
if corridor_room_ids.Count == 0:
    # print("# No rooms found containing '{{{{}}}}' in their name. No doors updated.".format(ROOM_NAME_SUBSTRING)) # Optional user feedback
    pass # Exit script gracefully if no target rooms exist, no need to iterate doors
else:
    # Get the last phase defined in the project timeline
    # Door.FromRoom/ToRoom requires a Phase argument
    last_phase = None
    if doc.Phases.Size > 0:
        # Accessing the last phase - simpler way is often using Phases.get_Item(doc.Phases.Size - 1)
        try:
             last_phase = doc.Phases.get_Item(doc.Phases.Size - 1)
        except:
             # Fallback using iterator if indexing fails for some reason
             phase_iterator = doc.Phases.ReverseIterator()
             if phase_iterator.MoveNext(): # Move to the first element returned by ReverseIterator (which is the last phase)
                 last_phase = phase_iterator.Current

    if not last_phase:
        # print("# Error: Could not determine the project's final phase for FromRoom/ToRoom calculation. Cannot proceed.") # Optional message
        pass # Cannot proceed without a phase
    else:
        # 3. Find all Door instances in the project
        door_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()
        updated_door_count = 0

        for door in door_collector:
            # Doors are typically FamilyInstances, ensure this for safety
            if not isinstance(door, FamilyInstance):
                continue

            is_corridor_access = False
            try:
                # Check the FromRoom relationship for the door in the context of the last phase
                # Note: FromRoom/ToRoom can return null if the door doesn't border a room on that side,
                # is at the exterior, or if the room calculation fails for the given phase.
                # These properties exist on FamilyInstance for Doors
                from_room_prop = door.FromRoom.get_Item(last_phase) # Use get_Item for Phase-specific room
                # Check if from_room_prop is valid and its ID is in our set of corridor rooms
                if from_room_prop and corridor_room_ids.Contains(from_room_prop.Id):
                    is_corridor_access = True

                # Check the ToRoom relationship only if the FromRoom wasn't a corridor
                if not is_corridor_access:
                    to_room_prop = door.ToRoom.get_Item(last_phase) # Use get_Item for Phase-specific room
                    # Check if to_room_prop is valid and its ID is in our set of corridor rooms
                    if to_room_prop and corridor_room_ids.Contains(to_room_prop.Id):
                        is_corridor_access = True

            except Exception as e_room_check:
                # Handles potential errors like invalid phase arguments or issues accessing room properties for specific doors
                # print("# Warning: Could not check From/To Room for door {{{{}}}}. Error: {{{{}}}}".format(door.Id, e_room_check)) # Optional debug
                pass # Continue to the next door if room check fails

            # 4. If the door was found to access a corridor room, find and set the specified shared parameter
            if is_corridor_access:
                try:
                    # Attempt to find the parameter by its name.
                    # Assumption: The parameter "Corridor Access Door" exists as a shared parameter,
                    # is applied as an Instance parameter to the Doors category, and is writable.
                    param = door.LookupParameter(SHARED_PARAM_NAME)

                    # Proceed only if the parameter exists and is not read-only
                    if param and not param.IsReadOnly:
                        param_storage_type = param.StorageType
                        needs_update = False

                        # Determine if the parameter's current value needs to be updated
                        if param_storage_type == StorageType.String:
                            # Compare string value
                            current_val = param.AsString()
                            # Handle potential None value before comparison
                            if current_val is None or current_val != TARGET_PARAM_VALUE:
                                needs_update = True
                        elif param_storage_type == StorageType.Integer:
                            # Compare integer value (common for Yes/No parameters where 1=Yes, 0=No)
                            if param.AsInteger() != TARGET_PARAM_VALUE_INT:
                                needs_update = True
                        # Removed the 'else' block that assumed update needed for other types.
                        # Be explicit about which types we handle.
                        # If the parameter is neither String nor Integer, we won't update it here.

                        # If an update is determined to be necessary, attempt to set the new value
                        if needs_update:
                            set_successful = False
                            if param_storage_type == StorageType.String:
                                # Use param.Set(string) for String type parameters
                                if param.Set(TARGET_PARAM_VALUE):
                                     set_successful = True
                            elif param_storage_type == StorageType.Integer:
                                # Use param.Set(integer) for Integer type parameters (like Yes/No)
                                if param.Set(TARGET_PARAM_VALUE_INT):
                                    set_successful = True
                            # No fallback attempt for other types

                            if set_successful:
                                updated_door_count += 1
                            #else:
                                # print("# Warning: Failed to set parameter '{{{{}}}}' on door {{{{}}}}. Check type/permissions.".format(SHARED_PARAM_NAME, door.Id)) # Optional debug

                except Exception as e_param_set:
                    # Handle errors during parameter lookup or setting process
                    # print("# Error processing parameter '{{{{}}}}' for door {{{{}}}}. Error: {{{{}}}}".format(SHARED_PARAM_NAME, door.Id, e_param_set)) # Optional debug
                    pass # Continue processing other doors even if one fails

        # Final summary output (optional, can be printed to Revit's status bar or a log file if needed outside this script)
        # if updated_door_count > 0:
        #    print("# Successfully updated the '{{{{}}}}' parameter to '{{{{}}}}' for {{{{}}}} doors accessing '{{{{}}}}' rooms.".format(SHARED_PARAM_NAME, TARGET_PARAM_VALUE, updated_door_count, ROOM_NAME_SUBSTRING))
        # elif corridor_room_ids.Count > 0:
        #    print("# Found {{{{}}}} '{{{{}}}}' rooms, but no doors needed updating or failed to update.".format(corridor_room_ids.Count, ROOM_NAME_SUBSTRING))