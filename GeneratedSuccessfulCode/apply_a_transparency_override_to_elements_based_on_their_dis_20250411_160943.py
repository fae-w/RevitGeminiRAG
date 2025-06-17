# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Math and exceptions
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View3D,
    ElementId,
    OverrideGraphicSettings,
    XYZ,
    BoundingBoxXYZ,
    ViewOrientation3D,
    Element # To check if element is valid for overrides
)
import System
import math # For infinity

# --- Configuration ---
# Transparency range (0 = opaque, 100 = fully transparent)
MIN_TRANSPARENCY = 0
MAX_TRANSPARENCY = 80 # Elements furthest away will be 80% transparent
# Categories to exclude (add BuiltInCategory enums as needed)
EXCLUDED_CATEGORIES = set([
    # Example: BuiltInCategory.OST_Levels, BuiltInCategory.OST_Grids
])
# Exclude elements smaller than this bounding box diagonal size (in feet) to filter out small details
MIN_BBOX_DIAGONAL = 0.1

# --- Script Logic ---
active_view = uidoc.ActiveView
processed_count = 0
error_count = 0
skipped_count = 0

# 1. Validate View
if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View3D):
    print("# Error: Active view is not a 3D view.")
elif active_view.IsLocked:
    print("# Error: Active 3D view is locked and cannot be modified.")
else:
    try:
        # 2. Get Camera Information
        view_orientation = active_view.GetOrientation()
        eye_position = view_orientation.EyePosition
        # Ensure forward direction is normalized (it should be, but safety check)
        forward_direction = view_orientation.ForwardDirection.Normalize()

        # 3. Collect Visible Elements
        collector = FilteredElementCollector(doc, active_view.Id)\
                    .WhereElementIsNotElementType()\
                    .WhereElementIsViewIndependent() # Excludes view-specific annotation etc.

        elements_data = [] # List to store (elementId, distance) tuples
        min_dist = float('inf')
        max_dist = float('-inf')
        found_elements = False

        # 4. Calculate Distances and Find Min/Max
        for element in collector:
            # Basic check if element might have geometry and supports overrides
            if not element or not element.IsValidObject or not element.Category:
                 skipped_count += 1
                 continue
            if element.Category.Id.IntegerValue in [int(bic) for bic in EXCLUDED_CATEGORIES]:
                skipped_count += 1
                continue
            if not element.CanHaveTypeAssigned(): # Filter out some non-geometric things
                skipped_count += 1
                continue
            if not active_view.IsElementVisibleInTemporaryViewMode(TemporaryViewMode.TemporaryHideIsolate, element.Id):
                 # Skips elements explicitly hidden in the view (if temp hide/isolate is active, this reflects that too)
                 # Note: This might not catch all visibility controls perfectly (e.g., complex filters), but is a reasonable check.
                 skipped_count += 1
                 continue


            bbox = element.get_BoundingBox(active_view) # Use view-specific bounding box

            if bbox is None or not bbox.Enabled or bbox.Min is None or bbox.Max is None:
                # Try model bounding box as a fallback
                bbox = element.get_BoundingBox(None)

            if bbox is None or not bbox.Enabled or bbox.Min is None or bbox.Max is None:
                skipped_count += 1
                continue # Skip elements without a valid bounding box

            # Check bounding box size to filter small elements
            diagonal = bbox.Min.DistanceTo(bbox.Max)
            if diagonal < MIN_BBOX_DIAGONAL:
                 skipped_count += 1
                 continue

            try:
                # Calculate center of the bounding box
                center = (bbox.Min + bbox.Max) / 2.0

                # Calculate vector from camera eye to element center
                eye_to_center = center - eye_position

                # Project this vector onto the view's forward direction to get distance
                # Positive distance means in front of the camera
                distance = eye_to_center.DotProduct(forward_direction)

                if distance > 0: # Only consider elements in front of the camera
                    elements_data.append((element.Id, distance))
                    min_dist = min(min_dist, distance)
                    max_dist = max(max_dist, distance)
                    found_elements = True

            except Exception as dist_ex:
                # print("# Warning: Could not process element ID {}: {}".format(element.Id, dist_ex))
                error_count += 1
                skipped_count += 1


        # 5. Apply Transparency Overrides
        if not found_elements:
            print("# Info: No suitable elements found in the active view in front of the camera to apply overrides.")
        elif min_dist == float('inf') or max_dist == float('-inf'):
             print("# Info: Could not determine valid distance range for elements.")
        else:
            distance_range = max_dist - min_dist

            for element_id, distance in elements_data:
                try:
                    transparency = MIN_TRANSPARENCY # Default if range is zero

                    if distance_range > 1e-6: # Avoid division by zero if all elements are at the same distance
                        # Linear interpolation
                        normalized_distance = (distance - min_dist) / distance_range
                        transparency = MIN_TRANSPARENCY + (MAX_TRANSPARENCY - MIN_TRANSPARENCY) * normalized_distance

                    # Clamp transparency to the valid 0-100 range and convert to integer
                    final_transparency = int(round(max(0, min(100, transparency))))

                    # Create override settings
                    ogs = OverrideGraphicSettings()
                    ogs.SetSurfaceTransparency(final_transparency)

                    # Apply override (Transaction handled externally)
                    active_view.SetElementOverrides(element_id, ogs)
                    processed_count += 1

                except System.ArgumentException as arg_ex:
                     print("# Error setting transparency for element ID {}: {}. Value was: {}".format(element_id, arg_ex.Message, final_transparency))
                     error_count += 1
                except Exception as apply_ex:
                    print("# Error applying override to element ID {}: {}".format(element_id, apply_ex))
                    error_count += 1

            # Optional: Provide summary feedback
            # print("# Applied distance-based transparency to {} elements.".format(processed_count))
            # if skipped_count > 0:
            #    print("# Skipped {} elements (no geometry, excluded category, too small, behind camera, or hidden).".format(skipped_count))
            # if error_count > 0:
            #    print("# Encountered {} errors during processing.".format(error_count))

    except Exception as e:
        print("# Error: An unexpected error occurred: {}".format(e))