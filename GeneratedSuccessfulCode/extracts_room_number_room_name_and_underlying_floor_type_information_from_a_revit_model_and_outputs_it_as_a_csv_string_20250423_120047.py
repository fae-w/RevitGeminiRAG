# Purpose: This script extracts room number, room name, and underlying floor type information from a Revit model and outputs it as a CSV string.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Floor, FloorType,
    BuiltInParameter, ElementId, Level, XYZ, Options, GeometryInstance,
    Solid, Line, SolidCurveIntersectionOptions, ViewDetailLevel
)
from Autodesk.Revit.DB.Architecture import Room
# Add System reference if needed for specific operations (though not strictly needed for this core logic)
# clr.AddReference('System')
# import System

# Helper function to get a valid Solid from an element, handling GeometryInstances
def GetSolidFromElement(element, opts):
    """Extracts the first valid Solid geometry from an element."""
    geo_element = element.get_Geometry(opts)
    if geo_element:
        for geo_object in geo_element:
            if isinstance(geo_object, Solid) and geo_object.Volume > 1e-6:
                return geo_object
            elif isinstance(geo_object, GeometryInstance):
                # Use GetInstanceGeometry() with the same options object
                instance_geometry = geo_object.GetInstanceGeometry(opts) # Pass options here
                if instance_geometry:
                    for instance_obj in instance_geometry:
                        if isinstance(instance_obj, Solid) and instance_obj.Volume > 1e-6:
                            # Return the solid from the instance
                            return instance_obj
    return None

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Room Number","Room Name","Floor Type Name"')

# Geometry options - Fix the View/DetailLevel conflict
geom_options = Options()
geom_options.ComputeReferences = False
geom_options.IncludeNonVisibleObjects = False
try:
    active_view = doc.ActiveView
    if active_view and hasattr(active_view, 'DetailLevel'):
        # Set the view; DetailLevel will be derived from the view automatically
        geom_options.View = active_view
        # DO NOT set DetailLevel explicitly if View is set
    else:
        # Fallback if no active view or view has no DetailLevel (e.g., schedules)
        geom_options.DetailLevel = ViewDetailLevel.Fine
except Exception as e_options:
    # General fallback in case accessing ActiveView fails or other issues
    # print("Error setting Geometry Options: {}, using default DetailLevel.".format(e_options)) # Optional Debug
    geom_options.DetailLevel = ViewDetailLevel.Fine

# Collect all Room elements that are placed
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
# Ensure room is placed (has Area > 0 and Location is not None) and belongs to a level
placed_rooms = [r for r in room_collector if r.Area > 0 and r.Location is not None and r.LevelId != ElementId.InvalidElementId]

# Collect all Floor elements once for efficiency
all_floors = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType().ToElements()

# Iterate through placed rooms
for room in placed_rooms:
    # Already filtered by type, but an explicit check is safe
    if not isinstance(room, Room):
        continue

    room_number = "N/A"
    room_name = "N/A"
    found_floor_type_name = "Not Found" # Default if no floor is identified

    try:
        # Get Room Number
        num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
        if num_param and num_param.HasValue:
            room_number = num_param.AsString()
        elif hasattr(room, 'Number'): # Fallback to Number property
             room_number = room.Number

        # Get Room Name
        name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
        if name_param and name_param.HasValue:
            room_name = name_param.AsString()
        elif hasattr(room, 'Name'): # Fallback to Name property
             room_name = room.Name

        # Get Room Location Point and Level ID (already checked level validity earlier)
        room_location = room.Location
        room_level_id = room.LevelId
        room_pt = None
        if room_location and hasattr(room_location, 'Point'):
             room_pt = room_location.Point
        else: # Fallback using bounding box center if LocationPoint isn't available
             bb = room.get_BoundingBox(None) # Use view=None for model bounding box
             if bb is not None and bb.Min is not None and bb.Max is not None:
                 # Try to get Z from Level elevation
                 room_level = doc.GetElement(room_level_id) if room_level_id != ElementId.InvalidElementId else None
                 z_coord = room_level.Elevation if room_level and hasattr(room_level, 'Elevation') else (bb.Min.Z + bb.Max.Z) / 2.0
                 room_pt = XYZ((bb.Min.X + bb.Max.X) / 2.0, (bb.Min.Y + bb.Max.Y) / 2.0, z_coord)

        # Proceed only if we have a location point and level
        if room_pt and room_level_id != ElementId.InvalidElementId:
            # Define a vertical ray downwards from the room point
            # Start slightly above the room's Z location to ensure it's inside the room volume initially
            # If Z came from level, starting above is safer. If from BB center, it might already be ok.
            ray_start = XYZ(room_pt.X, room_pt.Y, room_pt.Z + 0.1) # Start 0.1 units above room location point Z
            # Long ray down (e.g., 100 units) to ensure it passes through floors below
            ray_end = XYZ(room_pt.X, room_pt.Y, room_pt.Z - 100.0)
            if ray_start.IsAlmostEqualTo(ray_end): # Avoid zero length line if Z was already very low
                 ray_end = XYZ(ray_start.X, ray_start.Y, ray_start.Z - 100.1)

            # Create the ray (bound line)
            ray = None
            try:
                # Ensure start and end points are not practically identical before creating line
                if not ray_start.IsAlmostEqualTo(ray_end, 1e-9):
                    ray = Line.CreateBound(ray_start, ray_end)
            except Exception as line_ex: # Handle potential errors creating the line
                # print("Error creating ray for Room {}: {}".format(room.Id, line_ex)) # Optional Debug
                pass # Ray remains None

            if ray:
                intersect_options = SolidCurveIntersectionOptions()

                # Check against floors on the same level first (most common scenario)
                intersected_floor = None
                min_intersect_dist_sq = float('inf') # Find the closest intersection point below the start

                for floor in all_floors:
                    # Initial check: Floor should ideally be on the same level or potentially below.
                    # For simplicity, we initially focus on the same level. Can be expanded later.
                    if floor.LevelId == room_level_id:
                        floor_solid = GetSolidFromElement(floor, geom_options)
                        if floor_solid:
                            try:
                                intersection_result = floor_solid.IntersectWithCurve(ray, intersect_options)
                                # Check if the intersection result is valid and has segments
                                if intersection_result and intersection_result.SegmentCount > 0:
                                    # Iterate through intersection points
                                    for i in range(intersection_result.SegmentCount):
                                        intersect_pt = intersection_result.GetCurveSegment(i).StartPoint
                                        # Ensure intersection is below or very close to the ray start Z
                                        if intersect_pt.Z <= ray_start.Z + 1e-6:
                                            dist_sq = ray_start.DistanceTo(intersect_pt)**2
                                            # If this is the closest intersection found so far
                                            if dist_sq < min_intersect_dist_sq:
                                                min_intersect_dist_sq = dist_sq
                                                intersected_floor = floor
                                    # We only need one floor, the first one intersected directly below.
                                    # Breaking here might miss a closer floor if multiple floors overlap
                                    # and the ray hits a further one first. Hence, check all on the level.

                            except Exception as intersect_ex:
                                # print("Intersection Error for Room {} with Floor {}: {}".format(room.Id, floor.Id, intersect_ex)) # Optional Debug
                                pass # Ignore intersection errors for specific floors

                # If a floor was found on the same level (the closest one intersected below ray start)
                if intersected_floor:
                     floor_type_id = intersected_floor.GetTypeId()
                     if floor_type_id != ElementId.InvalidElementId:
                         floor_type_element = doc.GetElement(floor_type_id)
                         if isinstance(floor_type_element, FloorType):
                             # Get Type Name using BuiltInParameter for robustness
                             type_name_param = floor_type_element.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                             if type_name_param and type_name_param.HasValue:
                                 found_floor_type_name = type_name_param.AsString()
                             else: # Fallback to Name property
                                 found_floor_type_name = floor_type_element.Name
                         else:
                             found_floor_type_name = "Invalid Floor Type Elem" # Handle case where TypeId doesn't yield FloorType
                     else:
                         found_floor_type_name = "Invalid Floor Type ID"
                # Optional: Add logic here to search floors on lower levels if none found on the same level

    except Exception as e:
        # Log error processing a specific room if needed for debugging
        # print("Error processing Room {} (Number: {}): {}".format(room.Id, room_number, str(e)))
        found_floor_type_name = "Error Processing" # Indicate an error occurred for this room
        # Ensure safe values even if error occurred before assignment
        room_number = room_number if room_number != "N/A" else "Error"
        room_name = room_name if room_name != "N/A" else "Error"
        pass # Continue to next room

    # Escape quotes for CSV safety
    safe_room_number = '"' + str(room_number).replace('"', '""') + '"'
    safe_room_name = '"' + str(room_name).replace('"', '""') + '"'
    safe_floor_type_name = '"' + str(found_floor_type_name).replace('"', '""') + '"'

    # Append data row
    csv_lines.append(','.join([safe_room_number, safe_room_name, safe_floor_type_name]))

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::room_floor_types.csv")
    print(file_content)
else:
    # Provide feedback if no rooms were processed or found
    print("# No placed Room elements meeting criteria found or processed in the project.")