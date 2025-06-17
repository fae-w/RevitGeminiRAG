# Purpose: This script updates the 'Finish' parameter of walls adjacent to specific rooms.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Good practice

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Wall,
    SpatialElementBoundaryOptions,
    SpatialElementBoundaryLocation,
    BoundarySegment,
    Element
)
# Import Room class directly from DB namespace (it's within RevitAPI.dll)
from Autodesk.Revit.DB.Architecture import Room

# --- Script Core Logic ---

# Define the target room names (case-sensitive)
target_room_names = ["WC", "Bathroom"]

# Define the parameter name to update on the walls
# Assumes an Instance Parameter named "Finish" exists on Walls.
wall_parameter_name = "Finish"

# Define the value to set the parameter to
new_parameter_value = "Tile"

# --- Find Target Rooms ---
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
target_rooms = []
for room in room_collector:
    # Ensure it's a valid Room object and is placed (has a Location)
    if isinstance(room, Room) and room.Location is not None:
        try:
            room_name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
            if room_name_param and room_name_param.AsString() in target_room_names:
                target_rooms.append(room)
        except Exception:
            # Ignore rooms that might cause errors during name retrieval
            pass

# --- Identify Adjacent Walls ---
adjacent_wall_ids = set() # Use a set to store unique wall ElementIds

# Configure boundary options to get finish faces
boundary_options = SpatialElementBoundaryOptions()
boundary_options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish # Get boundary at the finish face

for room in target_rooms:
    try:
        # Get boundary segments (returns list of lists, one list per loop)
        boundary_segment_loops = room.GetBoundarySegments(boundary_options)
        if not boundary_segment_loops:
            continue

        for loop in boundary_segment_loops:
            for segment in loop:
                boundary_element_id = segment.ElementId
                # Check if the boundary element is a valid element ID
                if boundary_element_id != ElementId.InvalidElementId:
                    # Attempt to get the element to check if it's a wall later
                    adjacent_wall_ids.add(boundary_element_id)

    except Exception:
        # Ignore rooms that might cause errors during boundary segment retrieval
        pass

# --- Update Wall Parameter ---
# Optional counters, not printed per requirements
# updated_count = 0
# skipped_count = 0
# error_count = 0

for element_id in adjacent_wall_ids: # Renamed wall_id to element_id for clarity
    try:
        element = doc.GetElement(element_id)

        # Check if the element is actually a Wall
        if element and isinstance(element, Wall):
            wall = element
            # Look for the specified parameter
            finish_param = wall.LookupParameter(wall_parameter_name)

            if finish_param and not finish_param.IsReadOnly:
                # Check if the parameter can be set with a string
                try:
                    current_value = finish_param.AsString()
                    # Avoid unnecessary updates if value is already correct
                    if current_value != new_parameter_value:
                        finish_param.Set(new_parameter_value)
                        # updated_count += 1
                    # else:
                        # skipped_count += 1 # Already has the correct value
                except Exception:
                    # Error during setting (e.g., wrong data type expected)
                    # error_count += 1
                    pass # Silently ignore setting errors for now
            # elif finish_param and finish_param.IsReadOnly:
                # skipped_count += 1
            # else: # Parameter not found
                # skipped_count += 1
                pass
        # else: # Element is not a Wall (could be Room Sep Line, another Room, etc.)
            # skipped_count += 1
            pass

    except Exception:
        # Error processing element ID (e.g., element deleted)
        # error_count += 1
        pass