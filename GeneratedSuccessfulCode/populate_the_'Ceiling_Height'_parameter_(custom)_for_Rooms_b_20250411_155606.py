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
    XYZ,
    Parameter,
    StorageType
)
# Import Room class directly from DB.Architecture namespace
from Autodesk.Revit.DB.Architecture import Room

# --- Parameters ---
# Define the name of the custom parameter on the Room to store the ceiling height
target_room_param_name = "Ceiling Height"

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
    found_ceiling_height = None
    target_ceiling = None # Keep track of the ceiling element found

    try:
        # Iterate through all ceilings to find one whose center point is inside this room
        for ceiling in all_ceilings:
            if not isinstance(ceiling, Ceiling):
                continue

            # Get the ceiling's bounding box in model coordinates
            bb = ceiling.get_BoundingBox(None) # Pass None for view to get model extents

            if bb is None:
                continue # Cannot get bounding box for this ceiling

            # Calculate the center point of the ceiling's bounding box
            center_point = (bb.Min + bb.Max) * 0.5

            # Check if the center point of the ceiling lies within the room boundaries
            # This uses the room's 2D footprint at its computation height.
            if room.IsPointInRoom(center_point):
                # Found a potential ceiling for the room
                target_ceiling = ceiling
                # Assume the first ceiling found whose center is in the room is the correct one.
                break # Stop searching for ceilings for this room

        # If a ceiling was associated with the room
        if target_ceiling:
            # Get the ceiling's "Height Offset From Level" parameter
            height_param = target_ceiling.get_Parameter(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM)

            if height_param and height_param.HasValue:
                # Ensure the parameter stores a numerical value (Double)
                if height_param.StorageType == StorageType.Double:
                    found_ceiling_height = height_param.AsDouble()
                else:
                    # Skip if the height parameter is not a number (unexpected)
                    continue # Skip to the next room
            else:
                # Ceiling found, but height parameter is missing or has no value
                continue # Skip to the next room

            # Now attempt to set the room's custom 'Ceiling Height' parameter
            room_target_param = room.LookupParameter(target_room_param_name)

            if room_target_param and not room_target_param.IsReadOnly:
                # Check if the target parameter is of type Double
                if room_target_param.StorageType == StorageType.Double:
                    try:
                        # Set the parameter value (Revit's internal units - feet)
                        current_value = room_target_param.AsDouble()
                        # Optional: Only set if value is different to avoid unnecessary updates
                        # Check for small tolerance if needed
                        tolerance = 0.001 # Example tolerance in feet
                        if abs(current_value - found_ceiling_height) > tolerance:
                             room_target_param.Set(found_ceiling_height)
                    except Exception as set_ex:
                        # Error during setting the parameter
                        # print("Error setting parameter '{}' for room {}: {}".format(target_room_param_name, room.Id, set_ex)) # Debug
                        pass # Silently ignore setting errors
                # else:
                    # Target parameter exists but is not a Double type, cannot set height value directly
                    # print("Target parameter '{}' on room {} is not a numeric type.".format(target_room_param_name, room.Id)) # Debug
                    pass
            # else:
                # Target parameter not found or is read-only on this room
                # print("Target parameter '{}' not found or read-only for room {}.".format(target_room_param_name, room.Id)) # Debug
                pass
        # else:
            # No ceiling center point found within this room's boundaries using the current method.
            # print("No ceiling center point found within room {}.".format(room.Id)) # Debug
            pass

    except Exception as room_proc_ex:
        # Error processing this specific room
        # print("Error processing room {}: {}".format(room.Id, room_proc_ex)) # Debug
        pass # Silently ignore errors for individual rooms

# Optional: Add a print statement for successful completion if run in an interactive console
# print("Script finished attempting to set '{}' parameter on rooms.".format(target_room_param_name))