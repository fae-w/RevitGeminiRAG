# Purpose: This script updates a specified parameter on walls separating rooms of a particular department.

﻿# Import necessary base classes
import clr
clr.AddReference('RevitAPI')

# Import DB namespaces/classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Wall,
    SpatialElementBoundaryOptions,
    SpatialElementBoundaryLocation,
    BoundarySegment,
    Element,
    StorageType # Added for parameter check
)
# Import Architecture specific classes - relying on environment to load the assembly
from Autodesk.Revit.DB.Architecture import Room

# --- Configuration ---
target_department = "Office" # Case-sensitive department name
parameter_name = "Acoustic Rating Required" # The exact name of the custom shared parameter on Walls
parameter_value = "Yes" # The value to set the parameter to

# --- Helper Function ---
def get_room_department(room):
    """Safely gets the Department parameter value for a room."""
    if not isinstance(room, Room):
        return None
    try:
        # Using BuiltInParameter.ROOM_DEPARTMENT for reliability
        dept_param = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)
        if dept_param and dept_param.HasValue:
            # Ensure the value is returned as a string
            dept_value = dept_param.AsString()
            return dept_value if dept_value is not None else ""
    except Exception:
        # Ignore errors during parameter retrieval for a single room
        pass
    return None # Return None if parameter missing, not Room, or error

# --- Main Logic ---

# 1. Collect all placed rooms and store their departments for quick lookup
all_placed_rooms = {} # {ElementId: Room}
room_departments = {} # {ElementId: department_string}
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in room_collector:
    # Ensure it's a Room instance and it's placed in the model
    if isinstance(room, Room) and room.Location is not None:
        room_id = room.Id
        all_placed_rooms[room_id] = room
        dept = get_room_department(room)
        # Store department even if it's None or empty
        room_departments[room_id] = dept

# 2. Build a map of Walls to the Rooms they bound
#    wall_to_rooms_map = { wall_ElementId: [room_ElementId1, room_ElementId2, ...], ... }
wall_to_rooms_map = {}
boundary_options = SpatialElementBoundaryOptions()
# Use Finish face boundary as it usually represents the separation relevant for acoustics/finishes
boundary_options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish

for room_id, room in all_placed_rooms.items():
    try:
        # GetBoundarySegments returns a list of lists (loops)
        boundary_segment_loops = room.GetBoundarySegments(boundary_options)
        if not boundary_segment_loops:
            continue # Skip rooms with no boundaries (e.g., redundant rooms)

        # Track wall IDs processed for this room to avoid redundant GetElement calls
        processed_walls_for_room = set()

        for loop in boundary_segment_loops:
            for segment in loop:
                boundary_element_id = segment.ElementId
                # Check if the boundary element is a valid element ID and not already processed for this room
                if boundary_element_id != ElementId.InvalidElementId and boundary_element_id not in processed_walls_for_room:
                    # Attempt to get the element
                    boundary_element = doc.GetElement(boundary_element_id)
                    # Check if the boundary element is a Wall instance
                    if boundary_element and isinstance(boundary_element, Wall):
                        wall_id = boundary_element_id
                        processed_walls_for_room.add(wall_id) # Mark wall as processed for this room

                        # Initialize the list for the wall if it's not in the map yet
                        if wall_id not in wall_to_rooms_map:
                            wall_to_rooms_map[wall_id] = []
                        # Add the current room ID to the list for this wall, ensuring uniqueness
                        if room_id not in wall_to_rooms_map[wall_id]:
                             wall_to_rooms_map[wall_id].append(room_id)

    except Exception as e:
        # Silently ignore errors processing boundaries for a single room
        pass # Continue processing other rooms

# 3. Identify walls that separate at least two 'Office' rooms
walls_to_update_ids = set() # Use a set to store unique wall ElementIds

for wall_id, bounding_room_ids in wall_to_rooms_map.items():
    office_room_count = 0
    # Count how many rooms bounding this wall have the target department
    for room_id in bounding_room_ids:
        # Use the pre-calculated department dictionary
        if room_departments.get(room_id) == target_department:
            office_room_count += 1

    # If the wall bounds two or more 'Office' rooms, it potentially separates them
    if office_room_count >= 2:
        walls_to_update_ids.add(wall_id)

# 4. Update the specified parameter on the identified walls (Transaction handled externally)
for wall_id in walls_to_update_ids:
    try:
        wall = doc.GetElement(wall_id)
        # Double-check it's a wall (should be, based on map construction)
        if not isinstance(wall, Wall):
            continue

        # Find the custom shared parameter by name
        target_param = wall.LookupParameter(parameter_name)

        if target_param:
            if not target_param.IsReadOnly:
                current_value_str = None
                try:
                    # Check if parameter has a value before trying AsString()
                    if target_param.HasValue:
                        current_value_str = target_param.AsString()
                    # Handle cases where parameter exists but is empty (AsString might return None or empty string)
                    elif target_param.StorageType == StorageType.String:
                         current_value_str = "" # Treat empty string param as ""
                except Exception:
                    # Might fail if AsString() not applicable (e.g., non-text param)
                    pass

                # Set value if it's not already the target value (string comparison)
                # This assumes the target parameter is Text or compatible with string input "Yes"
                if current_value_str != parameter_value:
                    try:
                        target_param.Set(parameter_value)
                    except Exception as set_error:
                        # Failed to set value (e.g., wrong data type, invalid value)
                        # Silently ignore set errors for individual parameters
                        pass
            # else: Parameter is read-only, do nothing
        # else: Parameter not found on this wall, do nothing

    except Exception as get_wall_err:
        # Error retrieving or processing the wall element itself
        # Silently ignore errors for individual walls
        pass