# Purpose: This script aligns a selected Scope Box to a selected Reference Plane in Autodesk Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception, Math
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    ElementId,
    BoundingBoxXYZ,
    XYZ,
    Plane,
    ReferencePlane,
    ElementTransformUtils,
    DatumPlane # Base class for ReferencePlane
)
from Autodesk.Revit.UI import Selection
from System import Exception, Math # For Abs

# --- Initialization ---
scope_box = None
ref_plane = None
error_message = None
moved = False
TOLERANCE = 1e-9 # Tolerance for checking if already aligned

# --- Step 1: Get and Validate Selection ---
try:
    selected_ids = uidoc.Selection.GetElementIds()
    if not selected_ids:
         error_message = "# Error: No elements selected. Please select one Scope Box and one Reference Plane."
    elif selected_ids.Count != 2:
        error_message = "# Error: Expected 2 selected elements, but found {}. Please select exactly one Scope Box and one Reference Plane.".format(selected_ids.Count)
    else:
        selected_elements = [doc.GetElement(elId) for elId in selected_ids]
        found_sb = 0
        found_rp = 0
        for elem in selected_elements:
            if isinstance(elem, ReferencePlane):
                if ref_plane is None:
                    ref_plane = elem
                    found_rp += 1
                else:
                    error_message = "# Error: More than one Reference Plane selected."
                    break
            # Check if it's a scope box (Volume of Interest Category)
            elif elem and elem.Category and elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_VolumeOfInterest):
                 if scope_box is None:
                     scope_box = elem
                     found_sb += 1
                 else:
                     error_message = "# Error: More than one Scope Box selected."
                     break

        # After checking all elements
        if not error_message:
            if found_sb == 0:
                error_message = "# Error: No Scope Box selected."
            elif found_rp == 0:
                error_message = "# Error: No Reference Plane selected."
            elif found_sb > 1 or found_rp > 1:
                 # This case should be caught above, but double check
                 error_message = "# Error: Invalid selection count for Scope Box or Reference Plane."

except Exception as e:
    error_message = "# Error processing selection: {}".format(e)

# --- Step 2: Get Geometry (if selection is valid) ---
bbox = None
plane = None
if not error_message:
    try:
        # Get Scope Box Bounding Box (model coordinates)
        # Using the scope box element directly for GetBoundingBox
        view_for_bbox = None # Use model coordinates
        bbox = scope_box.get_BoundingBox(view_for_bbox)
        if not bbox or not bbox.Min or not bbox.Max or bbox.Min.IsAlmostEqualTo(bbox.Max, TOLERANCE):
            error_message = "# Error: Could not retrieve a valid, non-zero volume bounding box for the Scope Box."
        else:
            # Get Reference Plane geometry
            # ReferencePlane guarantees GetPlane() method
            plane = ref_plane.GetPlane()
            if not plane or not plane.Normal or not plane.Origin or plane.Normal.IsZeroLength():
                 error_message = "# Error: Could not retrieve valid plane geometry (origin and non-zero normal) from the selected Reference Plane."

    except Exception as e:
        error_message = "# Error getting geometry: {}".format(e)

# --- Step 3: Calculate Alignment (if geometry available) ---
move_vector = None
if not error_message:
    try:
        plane_normal = plane.Normal.Normalize() # Ensure normal is normalized
        plane_origin = plane.Origin

        # Calculate the 8 corner points of the bounding box
        corners = []
        corners.append(bbox.Min)
        corners.append(XYZ(bbox.Max.X, bbox.Min.Y, bbox.Min.Z))
        corners.append(XYZ(bbox.Min.X, bbox.Max.Y, bbox.Min.Z))
        corners.append(XYZ(bbox.Min.X, bbox.Min.Y, bbox.Max.Z))
        corners.append(XYZ(bbox.Max.X, bbox.Max.Y, bbox.Min.Z))
        corners.append(XYZ(bbox.Max.X, bbox.Min.Y, bbox.Max.Z))
        corners.append(XYZ(bbox.Min.X, bbox.Max.Y, bbox.Max.Z))
        corners.append(bbox.Max)

        # Calculate signed distances from each corner to the plane
        min_dist = float('inf')
        max_dist = float('-inf')

        for corner in corners:
            # Signed distance = Normal . (Point - OriginOnPlane)
            dist = plane_normal.DotProduct(corner - plane_origin)
            if dist < min_dist:
                min_dist = dist
            if dist > max_dist:
                max_dist = dist

        # Determine which side (min distance point side or max distance point side) is closer to the plane
        move_distance = 0.0
        if abs(min_dist) < abs(max_dist):
            # The 'minimum distance' side/face is closer to the plane origin.
            # Move this side onto the plane.
            move_distance = -min_dist
        else:
            # The 'maximum distance' side/face is closer (or distances are equal).
            # Move this side onto the plane.
            move_distance = -max_dist

        # Construct the move vector if needed
        if abs(move_distance) > TOLERANCE:
             move_vector = move_distance * plane_normal
        else:
             move_vector = XYZ.Zero # Already aligned within tolerance

    except Exception as e:
        error_message = "# Error calculating alignment: {}".format(e)

# --- Step 4: Move Scope Box (if vector calculated) ---
if not error_message:
    if move_vector is None:
         # This implies an error occurred during calculation but wasn't caught
         if not error_message: # Avoid overwriting specific calculation errors
            error_message = "# Error: Move vector calculation failed unexpectedly."
    elif move_vector.IsZeroLength(): # Check if effectively zero using Revit API method
        print("# Scope Box is already aligned with the Reference Plane along the closest side (within tolerance).")
        moved = False # Indicate no move was performed
    else:
        try:
            # Ensure element IDs are valid before moving
            if scope_box and scope_box.IsValidObject and scope_box.Id != ElementId.InvalidElementId:
                ElementTransformUtils.MoveElement(doc, scope_box.Id, move_vector)
                moved = True
            else:
                error_message = "# Error: Scope Box element is invalid or has an invalid ID."

        except Exception as e:
            # Provide more context in the error message if possible
            sb_name = "Unknown"
            rp_name = "Unknown"
            try:
                sb_name = scope_box.Name if scope_box else "Invalid ScopeBox"
            except: pass
            try:
                rp_name = ref_plane.Name if ref_plane else "Invalid RefPlane"
            except: pass
            error_message = "# Error moving Scope Box '{}' to align with '{}': {}".format(sb_name, rp_name, e)

# --- Step 5: Final Output ---
if error_message:
    print(error_message)
elif moved:
    # Retrieve names safely for the final message
    sb_name = "Unknown"
    rp_name = "Unknown"
    try:
        sb_name = scope_box.Name
    except: pass
    try:
        rp_name = ref_plane.Name
    except: pass
    print("# Successfully moved Scope Box '{}' to align with Reference Plane '{}'.".format(sb_name, rp_name))
    # print("# Debug: Move Vector = ({:.4f}, {:.4f}, {:.4f})".format(move_vector.X, move_vector.Y, move_vector.Z)) # Optional debug info
elif not moved and not error_message and move_vector is not None and move_vector.IsZeroLength():
    pass # Message about alignment already printed in step 4
else:
    # Catch-all for unexpected states where no error was set, but no move happened
     if not error_message:
        print("# Alignment operation did not result in a move. The elements might already be aligned or another issue occurred.")