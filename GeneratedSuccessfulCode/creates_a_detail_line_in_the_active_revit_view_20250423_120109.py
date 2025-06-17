# Purpose: This script creates a detail line in the active Revit view.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    XYZ,
    Line,
    DetailLine,
    View,
    ViewType,
    BoundingBoxXYZ
)

# --- Configuration ---
line_length = 10.0 # Length of the detail line in feet
# Assumption: Draw a horizontal line of 'line_length' centered in the view's crop box.
# Assumption: If the crop box cannot be determined, use the view's origin (0,0,0) as the center.

# --- Get Active View ---
active_view = uidoc.ActiveView

if active_view is None:
    print("# Error: No active view found.")
    # Cannot proceed without an active view
    active_view = None # Ensure it's None to prevent further execution

elif active_view.ViewType not in [ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Elevation, ViewType.Section, ViewType.Detail, ViewType.DraftingView, ViewType.Legend]:
     print("# Error: Active view '{}' ('{}') cannot host detail lines.".format(active_view.Name, active_view.ViewType))
     # Cannot proceed with this view type
     active_view = None # Ensure it's None to prevent further execution

# --- Proceed only if view is valid ---
if active_view:
    # --- Determine View Center ---
    center_point = None
    try:
        # Use CropBox to find the center, works best if CropBox is active and visible
        crop_box = active_view.CropBox
        # Check if CropBox is enabled and its Min/Max points are valid
        if crop_box and crop_box.Enabled and crop_box.Min and crop_box.Max:
            center_point = (crop_box.Min + crop_box.Max) / 2.0
            # print("# Info: Using CropBox center.") # Optional debug info
        else:
            print("# Warning: Crop box is not enabled or invalid. Using view origin (0,0,0) as fallback center.")
            center_point = XYZ.Zero # Fallback to origin

    except Exception as e:
        print("# Error accessing view CropBox: {}. Using view origin (0,0,0) as fallback center.".format(e))
        center_point = XYZ.Zero # Fallback to origin

    # --- Create Line Geometry ---
    if center_point is not None: # Should always be true now due to fallback
        try:
            half_length = line_length / 2.0
            # Define line endpoints relative to the calculated center point
            # Assuming the view's X-axis is horizontal on screen
            start_point = center_point - XYZ(half_length, 0, 0)
            end_point = center_point + XYZ(half_length, 0, 0)

            # Create a bound Line geometry object
            geom_line = Line.CreateBound(start_point, end_point)

            # --- Create Detail Line ---
            # The document's creation factory is used.
            # Transaction is handled externally by the C# wrapper.
            detail_line = doc.Create.NewDetailCurve(active_view, geom_line)

            # Optional: Confirmation message
            # if detail_line:
            #    print("# Detail line created successfully in view '{}'.".format(active_view.Name))

        except Exception as e:
            print("# Error creating detail line: {}".format(e))
            # Provide specific hints for common errors
            if "curve is not in plane of the view" in str(e):
                 print("# Detail: This may happen if the view type or the calculated points are unsuitable.")
            elif "bound curve" in str(e):
                 print("# Detail: The created line geometry might be invalid (e.g., zero length).")
            elif "must be in 'Modifying'" in str(e):
                 print("# Detail: This script expects to run within an existing Transaction.")

    else:
        # This case should not be reached if the fallback logic works
        print("# Error: Could not determine a center point for the line.")