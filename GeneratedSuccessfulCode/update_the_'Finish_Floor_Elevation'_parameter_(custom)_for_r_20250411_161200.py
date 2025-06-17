# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference("System.Collections") # For List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Floor,
    Element,
    XYZ,
    Parameter,
    StorageType,
    Level,
    View3D,
    ReferenceIntersector,
    FindReferenceTarget,
    ElementCategoryFilter,
    Category,
    ElementFilter,
    LogicalAndFilter,
    PlanarFace,
    Face,
    HostObjectUtils,
    Solid,
    GeometryInstance,
    GeometryElement,
    Options as GeoOptions
)
# Import Room class directly from DB.Architecture namespace
from Autodesk.Revit.DB.Architecture import Room
from System.Collections.Generic import List

# --- Parameters ---
# Define the name of the custom parameter on the Room to store the floor elevation
target_room_param_name = "Finish Floor Elevation" # <<< USER DEFINED PARAMETER NAME

# --- Helper Function to Find a 3D View ---
def find_first_3d_view(doc):
    """Finds the first available 3D view suitable for ReferenceIntersector."""
    view_collector = FilteredElementCollector(doc).OfClass(View3D)
    for view in view_collector:
        if not view.IsTemplate and view.CanBePrinted: # Added CanBePrinted as another check for usability
             # Check if the view has a valid BoundingBox (might indicate it's properly generated)
            try:
                if view.get_BoundingBox(None) is not None:
                    return view
            except:
                 # Some views might throw errors on get_BoundingBox if not properly initialized
                 pass
    # Fallback: If no non-template view works, try the first one found even if template? Less ideal.
    if view_collector.GetElementCount() > 0:
         first_view = view_collector.FirstElement()
         # Check if the first view is usable
         try:
             if first_view.get_BoundingBox(None) is not None:
                 return first_view
         except:
             pass # If even the first view fails bbox check, return None
    return None

# --- Script Core Logic ---

# Find a suitable 3D view for ray casting
view3d = find_first_3d_view(doc)
if not view3d:
    print("# Warning: No suitable 3D view found for geometry operations. Ray casting unavailable.")
    # Proceed with fallback if needed, or alert user more strongly.

# Collect all Room elements that are placed
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
placed_rooms = []
for room in room_collector:
    # Ensure it's a valid Room object and is placed (has a Location and Area > 0)
    if isinstance(room, Room) and room.Location is not None and room.Area > 0:
        placed_rooms.append(room)

# If no 3D view, use fallback method (less precise)
if not view3d:
    print("# Warning: No 3D view. Attempting less precise floor finding method based on level and location.")
    # Collect floors
    floor_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()
    all_floors = list(floor_collector)

    for room in placed_rooms:
        try:
            room_location = room.Location.Point
            room_level_id = room.LevelId
            target_param = room.LookupParameter(target_room_param_name)

            if not target_param or target_param.IsReadOnly or target_param.StorageType != StorageType.Double:
                # print("# Skipping Room {{}} - Parameter '{{}}' invalid.".format(room.Id, target_room_param_name)) # Debug
                continue # Skip room if parameter is invalid

            best_floor_elevation = None
            min_vertical_distance = float('inf')

            for floor in all_floors:
                if not isinstance(floor, Floor):
                    continue

                # --- Get Floor Top Elevation ---
                floor_top_elevation = None
                try:
                    # Try getting level elevation + offset first (might be simpler)
                    floor_level = doc.GetElement(floor.LevelId)
                    if floor_level:
                         level_elev = floor_level.Elevation
                         offset_param = floor.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
                         if offset_param:
                             floor_top_elevation = level_elev + offset_param.AsDouble()
                    else: # Fallback to geometry if level info fails
                        top_faces_refs = HostObjectUtils.GetTopFaces(floor)
                        if top_faces_refs and len(top_faces_refs) > 0:
                            highest_z = -float('inf')
                            for face_ref in top_faces_refs:
                                geom_obj = floor.GetGeometryObjectFromReference(face_ref)
                                if isinstance(geom_obj, PlanarFace):
                                    if geom_obj.FaceNormal.Z > 0.9: # Check if face normal is upwards
                                        highest_z = max(highest_z, geom_obj.Origin.Z)
                            if highest_z > -float('inf'):
                                floor_top_elevation = highest_z
                        else: # Final fallback: BBox
                             bb_floor = floor.get_BoundingBox(None)
                             if bb_floor:
                                 floor_top_elevation = bb_floor.Max.Z # Approximate top using BBox Max Z

                except Exception as e:
                     # print("# Could not get elevation for floor {{}}: {{}}".format(floor.Id, e)) # Debug
                     bb_floor = floor.get_BoundingBox(None)
                     if bb_floor:
                         floor_top_elevation = bb_floor.Max.Z # Approximate top using BBox Max Z


                if floor_top_elevation is not None:
                    # Check if room location is vertically above or very close to this floor elevation
                    vertical_distance = room_location.Z - floor_top_elevation
                    # We want the floor just below or at the room location point.
                    # Positive distance means room is above floor.
                    if vertical_distance >= -0.1: # Allow small tolerance (floor slightly above point)
                        # Check if room location point is roughly within the floor's horizontal bounds
                        bb_floor_check = floor.get_BoundingBox(None) # Use model bounds
                        if bb_floor_check:
                            if (bb_floor_check.Min.X <= room_location.X <= bb_floor_check.Max.X and
                                bb_floor_check.Min.Y <= room_location.Y <= bb_floor_check.Max.Y):
                                # If this floor is closer vertically below the room point, consider it
                                # We want the smallest positive vertical distance.
                                if 0 <= vertical_distance < min_vertical_distance:
                                    min_vertical_distance = vertical_distance
                                    best_floor_elevation = floor_top_elevation
                                # Also consider the case where floor is exactly at or slightly above
                                elif -0.1 <= vertical_distance < 0 and best_floor_elevation is None:
                                     best_floor_elevation = floor_top_elevation # Initial guess if directly below is not found

            # Set parameter if a suitable floor was found
            if best_floor_elevation is not None:
                try:
                    current_value = target_param.AsDouble()
                    tolerance = 0.001 # Tolerance in feet
                    if abs(current_value - best_floor_elevation) > tolerance:
                        target_param.Set(best_floor_elevation)
                except Exception as set_ex:
                    # print("Error setting parameter '{{}}' for room {{}}: {{}}".format(target_room_param_name, room.Id, set_ex)) # Debug
                    pass # Silently ignore setting errors

        except Exception as room_proc_ex:
            # print("Error processing room {{}} (Fallback): {{}}".format(room.Id, room_proc_ex)) # Debug
            pass # Silently ignore errors for individual rooms

# --- Primary Method: Ray Casting (if 3D view exists) ---
elif view3d and len(placed_rooms) > 0:
    # Create filters for the ReferenceIntersector
    floor_cat_id = Category.GetCategory(doc, BuiltInCategory.OST_Floors).Id
    cat_filter = ElementCategoryFilter(floor_cat_id)

    # Setup ReferenceIntersector
    intersector = ReferenceIntersector(cat_filter, FindReferenceTarget.Face, view3d)
    intersector.FindReferencesInRevitLinks = False # Assume floors are in the main model

    # Iterate through each placed room
    for room in placed_rooms:
        try:
            room_location = room.Location.Point
            if not room_location:
                continue # Skip if room has no location point

            # Define Ray: Start slightly above room location point Z, shoot downwards
            ray_origin = room_location + XYZ(0, 0, 0.1) # Start 0.1 feet above room loc point Z
            ray_direction = XYZ(0, 0, -1) # Straight down

            # Find the nearest intersection below the point
            ref_context = intersector.FindNearest(ray_origin, ray_direction)

            if ref_context:
                intersected_ref = ref_context.GetReference()
                # prox = ref_context.Proximity # Distance from ray_origin to intersection

                # Get the element and the specific face intersected
                intersected_elem = doc.GetElement(intersected_ref.ElementId)
                if isinstance(intersected_elem, Floor):
                    geom_object = intersected_elem.GetGeometryObjectFromReference(intersected_ref)

                    if isinstance(geom_object, PlanarFace):
                        face = geom_object
                        # Check if the face is pointing upwards (it's a top face)
                        if face.FaceNormal.Z > 0.99: # Check if normal is predominantly Z+
                            floor_elevation = face.Origin.Z # Elevation of the planar face

                            # Find and set the room's custom parameter
                            target_param = room.LookupParameter(target_room_param_name)
                            if target_param and not target_param.IsReadOnly:
                                if target_param.StorageType == StorageType.Double:
                                    try:
                                        current_value = target_param.AsDouble()
                                        tolerance = 0.001 # Tolerance in feet
                                        if abs(current_value - floor_elevation) > tolerance:
                                             target_param.Set(floor_elevation)
                                    except Exception as set_ex:
                                        # print("Error setting parameter '{{}}' for room {{}}: {{}}".format(target_room_param_name, room.Id, set_ex)) # Debug
                                        pass # Silently ignore setting errors
                                # else: print("# Param '{{}}' on Room {{}} is not Double".format(target_room_param_name, room.Id)) # Debug
                            # else: print("# Param '{{}}' not found/writable on Room {{}}".format(target_room_param_name, room.Id)) # Debug
                    else: # Intersected face is not planar, might be edge case or complex floor
                         # Try getting elevation from intersection point itself?
                         intersection_point = ref_context.GetReference().GlobalPoint # Indentation Corrected
                         if intersection_point:
                              floor_elevation = intersection_point.Z
                              # Find and set the room's custom parameter (duplicate code block)
                              target_param = room.LookupParameter(target_room_param_name)
                              if target_param and not target_param.IsReadOnly:
                                   if target_param.StorageType == StorageType.Double:
                                       try:
                                           current_value = target_param.AsDouble()
                                           tolerance = 0.001 # Tolerance in feet
                                           if abs(current_value - floor_elevation) > tolerance:
                                                target_param.Set(floor_elevation)
                                       except Exception as set_ex:
                                           # print("Error setting parameter '{{}}' for room {{}} (non-planar face): {{}}".format(target_room_param_name, room.Id, set_ex)) # Debug
                                           pass


            # else: print("# No floor face found below Room {{}}".format(room.Id)) # Debug

        except Exception as room_proc_ex:
            # print("Error processing room {{}} (Ray Cast): {{}}".format(room.Id, room_proc_ex)) # Debug
            pass # Silently ignore errors for individual rooms

# Optional: print a completion message if needed in interactive mode
# print("Script finished attempting to set '{{}}' parameter on rooms.".format(target_room_param_name))