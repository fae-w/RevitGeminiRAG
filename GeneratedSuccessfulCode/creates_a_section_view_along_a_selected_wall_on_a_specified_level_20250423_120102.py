# Purpose: This script creates a section view along a selected wall on a specified level.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List
import System # For Exception handling

# Mandatory Revit API Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    Wall,
    Level,
    BuiltInCategory,
    LocationCurve,
    Curve,
    Line,
    XYZ,
    Transform,
    BoundingBoxXYZ,
    ViewFamilyType,
    ViewSection,
    ViewType,
    BuiltInParameter
)
# Import Autodesk specific exceptions if needed for specific catches
# from Autodesk.Revit.Exceptions import ArgumentsInconsistentException, InvalidOperationException

# --- Constants ---
TARGET_LEVEL_NAME = "L5"
DEFAULT_SECTION_DEPTH = 5.0 # Feet, view depth perpendicular to wall
DEFAULT_SECTION_HEIGHT = 10.0 # Feet (fallback if wall height unavailable)

# --- Initialize Variables ---
selected_wall = None
target_level = None
error_message = None

# --- Get Selection ---
selection = uidoc.Selection
selected_ids = selection.GetElementIds()

# --- Validate Selection and Level ---
if not selected_ids or selected_ids.Count != 1:
    error_message = "# Error: Please select exactly one Wall element."
else:
    element = doc.GetElement(selected_ids[0])
    if not isinstance(element, Wall):
        error_message = "# Error: Selected element (ID: {}) is not a Wall, it is a '{}'.".format(element.Id, element.GetType().Name)
    else:
        # --- Find Target Level ---
        level_collector = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()
        for level in level_collector:
            if level.Name == TARGET_LEVEL_NAME:
                target_level = level
                break
        if not target_level:
            error_message = "# Error: Level named '{}' not found in the document.".format(TARGET_LEVEL_NAME)
        else:
            # --- Check Wall's Level ---
            wall_level_id = element.LevelId
            if wall_level_id == ElementId.InvalidElementId:
                 error_message = "# Error: Selected wall (ID: {}) does not have an associated Level ID.".format(element.Id)
            elif wall_level_id != target_level.Id:
                wall_level = doc.GetElement(wall_level_id)
                error_message = "# Error: Selected wall (ID: {}) is on Level '{}', not the target Level '{}'.".format(element.Id, wall_level.Name if wall_level else "Invalid ID: {}".format(wall_level_id), TARGET_LEVEL_NAME)
            else:
                selected_wall = element # Wall is valid and on the correct level

# --- Print error or proceed ---
if error_message:
    print(error_message)
elif selected_wall and target_level:
    try:
        # --- Get Wall Geometry ---
        location = selected_wall.Location
        if not isinstance(location, LocationCurve):
            print("# Error: Selected wall (ID: {}) does not have a LocationCurve.".format(selected_wall.Id))
        else:
            curve = location.Curve
            # Check for valid, bound curve with non-negligible length
            if not curve or not curve.IsBound or curve.Length < doc.Application.ShortCurveTolerance:
                print("# Error: Could not retrieve a valid bound curve with sufficient length from the wall's location (ID: {}). Length: {}".format(selected_wall.Id, curve.Length if curve else "N/A"))
            else:
                # --- Calculate Section Box Parameters ---
                start_point = curve.GetEndPoint(0)
                end_point = curve.GetEndPoint(1)
                # Use curve midpoint Z for section box origin Z if needed? No, BBox is relative to transform origin.
                # Wall curve Z coordinate might not be exactly level elevation, but should be close.
                mid_point = (start_point + end_point) / 2.0
                wall_length = curve.Length

                # Get wall height, trying User Height parameter first, then Unconnected Height
                wall_height = DEFAULT_SECTION_HEIGHT # Use default as fallback
                height_param = selected_wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
                if height_param and height_param.HasValue:
                    wall_height = height_param.AsDouble()
                else:
                    unconnected_height_param = selected_wall.get_Parameter(BuiltInParameter.WALL_UNCONNECTED_HEIGHT)
                    if unconnected_height_param and unconnected_height_param.HasValue:
                         wall_height = unconnected_height_param.AsDouble()
                         # print("# Debug: Using Unconnected Height: {} ft".format(wall_height)) # Optional Debug
                    else:
                         print("# Warning: Could not determine Wall User Height or Unconnected Height for wall ID {}. Using default: {} ft".format(selected_wall.Id, DEFAULT_SECTION_HEIGHT))


                # --- Define basis vectors for the section box transform ---
                wall_direction = (end_point - start_point).Normalize()
                up_direction = XYZ.BasisZ

                # Handle vertically oriented walls (rare for standard walls, possible for faces?)
                if wall_direction.IsAlmostEqualTo(up_direction) or wall_direction.IsAlmostEqualTo(-up_direction):
                     print("# Warning: Wall centerline appears vertical. Section box orientation might be unexpected. Attempting calculation using world Y-axis as 'along'.")
                     # If wall line is vertical, define 'along' as world Y, 'up' as world Z, view dir as world X
                     t_basisX = XYZ.BasisY # 'Along' the wall (arbitrary horizontal if wall is vertical)
                     t_basisY = XYZ.BasisZ # 'Up'
                     t_basisZ = XYZ.BasisX # View Direction (perpendicular)
                     # Adjust box dimensions if interpretation changes
                     # min_x/max_x now refers to Y extent, min_y/max_y to Z extent based on wall_height
                     # This case is ambiguous for "section along centerline". Assuming user wants elevation-like view.
                else:
                    # Standard case: Wall line is horizontal or sloped
                    t_basisX = wall_direction # Along the wall length (local X)
                    t_basisY = up_direction   # Vertical (world Z) (local Y)
                    # View direction is perpendicular to the wall plane (wall_dir x up_dir)
                    t_basisZ = t_basisX.CrossProduct(t_basisY).Normalize() # Perpendicular to wall (local Z)

                # Check if cross product resulted in zero vector (should be caught above)
                if t_basisZ.IsZeroLength():
                     print("# Error: Could not determine valid perpendicular view direction. Wall direction may be parallel to Z-axis.")
                     # Attempt recovery: use cross product with X axis?
                     t_basisZ = t_basisX.CrossProduct(XYZ.BasisX).Normalize()
                     if t_basisZ.IsZeroLength(): # If wall is aligned with X too... use Y
                         t_basisZ = t_basisX.CrossProduct(XYZ.BasisY).Normalize()
                     if t_basisZ.IsZeroLength(): # Should not happen now
                         raise ValueError("Invalid view direction calculation (BasisZ is zero after checks)")
                     print("# Warning: Wall direction was parallel to Z. Used alternate axis for view direction.")


                # Create the transform for the BoundingBox
                transform = Transform.Identity
                transform.Origin = mid_point # Center the box on the wall's midpoint
                transform.BasisX = t_basisX
                transform.BasisY = t_basisY
                transform.BasisZ = t_basisZ

                # Define BBox extents relative to the transform's local coordinate system
                # Local X axis runs along the wall centerline
                # Local Y axis is vertical (world Z)
                # Local Z axis is perpendicular to the wall (view depth)
                min_x = -wall_length / 2.0
                max_x = wall_length / 2.0
                # Wall height relative to the curve location (assume curve is at base)
                min_y = 0.0 # Start at the wall base (relative to curve Z)
                max_y = wall_height # Go up by wall height
                # Section depth perpendicular to the wall, centered on centerline
                min_z = -DEFAULT_SECTION_DEPTH / 2.0 # Corrected syntax: 2.0
                max_z = DEFAULT_SECTION_DEPTH / 2.0

                section_box = BoundingBoxXYZ()
                section_box.Transform = transform
                section_box.Min = XYZ(min_x, min_y, min_z)
                section_box.Max = XYZ(max_x, max_y, max_z)

                # --- Find a Section View Type ---
                vft_collector = FilteredElementCollector(doc).OfClass(ViewFamilyType)
                section_vft = None
                for vft in vft_collector:
                    if vft.ViewFamily == ViewFamily.Section:
                        section_vft = vft
                        break # Use the first one found

                if not section_vft:
                    print("# Error: No Section View Family Type found in the document.")
                else:
                    # --- Create Section View ---
                    # Transaction needs to be handled by the calling C# environment
                    new_section_view = ViewSection.CreateSection(doc, section_vft.Id, section_box)
                    if new_section_view:
                        # Optional: Set view name or other parameters
                        try:
                             new_view_name = "Section Along Wall {}".format(selected_wall.Id)
                             new_section_view.Name = new_view_name
                        except Exception as name_ex:
                             print("# Warning: Could not set name for new section view: {}".format(str(name_ex)))

                        print("# Success: Created Section View '{}' (ID: {}) along Wall {} on Level '{}'".format(
                            new_section_view.Name, new_section_view.Id, selected_wall.Id, target_level.Name))
                        # Optional: Make the new view active
                        # uidoc.ActiveView = new_section_view
                    else:
                        print("# Error: Failed to create Section View.")

    except Exception as ex:
        # Print detailed exception information for debugging
        import traceback
        print("# Error: An exception occurred during section creation.")
        print("Exception Type: {}".format(type(ex).__name__))
        print("Exception Message: {}".format(str(ex)))
        # Uncomment for full traceback if needed, might be too verbose for user
        # print("Traceback:\n{}".format(traceback.format_exc()))