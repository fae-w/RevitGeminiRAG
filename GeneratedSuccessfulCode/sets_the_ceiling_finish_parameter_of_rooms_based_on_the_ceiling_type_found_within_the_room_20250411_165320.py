# Purpose: This script sets the 'Ceiling Finish' parameter of rooms based on the ceiling type found within the room.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Ceiling,
    Element,
    BoundingBoxXYZ,
    XYZ
)
# Import Room class directly from DB.Architecture namespace
from Autodesk.Revit.DB.Architecture import Room

# --- Script Core Logic ---

# Collect all Ceiling elements
ceiling_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Ceilings).WhereElementIsNotElementType()
all_ceilings = list(ceiling_collector)

# Collect all Room elements that are placed
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
placed_rooms = []
for room in room_collector:
    # Ensure it's a valid Room object and is placed (has a Location and Area > 0)
    if isinstance(room, Room) and room.Location is not None and room.Area > 0:
        placed_rooms.append(room)

# Iterate through each placed room
for room in placed_rooms:
    found_ceiling_type_name = None
    target_ceiling = None # Keep track of the ceiling element found

    try:
        # Iterate through all ceilings to find one whose center point is inside this room
        for ceiling in all_ceilings:
            if not isinstance(ceiling, Ceiling):
                continue

            # Get the ceiling's bounding box in model coordinates
            # Passing None for the view gets the model extents bounding box
            bb = ceiling.get_BoundingBox(None)

            if bb is None:
                # Cannot get bounding box for this ceiling, skip it
                continue

            # Calculate the center point of the ceiling's bounding box
            # Add small vertical offset to avoid potential issues if center is exactly on boundary?
            # center_point = (bb.Min + bb.Max) * 0.5 + XYZ(0,0,0.01) # Optional small Z offset
            center_point = (bb.Min + bb.Max) * 0.5

            # Check if the center point of the ceiling lies within the room boundaries
            # This is an approximation but often sufficient.
            # It might fail for complex room/ceiling shapes or if the ceiling only partially overlaps.
            # Or if the ceiling spans multiple rooms (center might only be in one).
            if room.IsPointInRoom(center_point):
                # Found a potential ceiling for the room
                target_ceiling = ceiling
                # Assume the first ceiling found whose center is in the room is the correct one.
                # More complex logic could be added here to choose between multiple ceilings
                # (e.g., based on area, level, etc.)
                break # Stop searching for ceilings for this room

        # If a ceiling was associated with the room
        if target_ceiling:
            ceiling_type_id = target_ceiling.GetTypeId()
            ceiling_type = doc.GetElement(ceiling_type_id)
            if ceiling_type:
                found_ceiling_type_name = ceiling_type.Name
            else:
                # Failed to get ceiling type element - skip setting parameter
                continue # Skip to the next room

            # Attempt to set the room's 'Ceiling Finish' parameter
            ceiling_finish_param = room.get_Parameter(BuiltInParameter.ROOM_FINISH_CEILING)

            if ceiling_finish_param and not ceiling_finish_param.IsReadOnly:
                try:
                    current_value = ceiling_finish_param.AsString()
                    # Set the parameter value if it's different
                    if current_value != found_ceiling_type_name:
                        ceiling_finish_param.Set(found_ceiling_type_name)
                except Exception as set_ex:
                    # Error during setting the parameter
                    # print("Error setting parameter for room {} ({}): {}".format(room.Id, room.Name ,set_ex)) # Debug
                    pass # Silently ignore setting errors for now
            # else: Parameter not found or read-only
                # print("Parameter 'Ceiling Finish' not found or read-only for room {} ({})".format(room.Id, room.Name)) # Debug
                pass
        # else:
            # No ceiling center point found within this room's boundaries using the current method.
            # print("No ceiling center point found within room {} ({})".format(room.Id, room.Name)) # Debug
            pass

    except Exception as room_proc_ex:
        # Error processing this specific room
        # print("Error processing room {} ({}): {}".format(room.Id, room.Name, room_proc_ex)) # Debug
        pass # Silently ignore errors for individual rooms