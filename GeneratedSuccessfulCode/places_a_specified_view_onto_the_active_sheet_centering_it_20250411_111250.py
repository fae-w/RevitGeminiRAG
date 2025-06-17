# Purpose: This script places a specified view onto the active sheet, centering it.

# Purpose: This script places a specific view onto the currently active sheet in Revit, centering the viewport.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewSheet,
    Viewport,
    XYZ,
    ElementId,
    BoundingBoxXYZ # Needed for sheet bounds
)

# --- Configuration ---
target_view_name = "Level 1 - Enlarged Core"

# --- Get Active Sheet ---
active_view = doc.ActiveView
target_sheet = None
if isinstance(active_view, ViewSheet):
    target_sheet = active_view
    # print("# Active view is sheet: '{}' (ID: {})".format(target_sheet.Name, target_sheet.Id))
else:
    print("# Error: The active view is not a sheet. Please activate the desired sheet.")
    target_sheet = None # Explicitly set to None

# --- Find the Target View ---
view_to_place = None
if target_sheet: # Only proceed if we have a sheet
    collector = FilteredElementCollector(doc).OfClass(View)
    # Ensure it's not a ViewSheet or ViewTemplate
    collector.Where(lambda v: not v.IsTemplate and not isinstance(v, ViewSheet))

    found = False
    for view in collector:
        if view.Name == target_view_name:
            view_to_place = view
            found = True
            # print("# Found target view: '{}' (ID: {})".format(view_to_place.Name, view_to_place.Id))
            break

    if not found:
        print("# Error: View named '{}' not found in the document.".format(target_view_name))
        view_to_place = None # Explicitly set to None

# --- Place View on Sheet ---
if target_sheet and view_to_place:
    sheet_id = target_sheet.Id
    view_id = view_to_place.Id

    try:
        # Check if the view can be added to the sheet
        if Viewport.CanAddViewToSheet(doc, sheet_id, view_id):
            # Calculate center point for placement
            center_point = XYZ(0, 0, 0) # Default fallback
            try:
                # Get sheet bounding box (using None for the view parameter gets sheet's overall box)
                sheet_bb = target_sheet.get_BoundingBox(None)
                if sheet_bb and sheet_bb.Min and sheet_bb.Max:
                    # Calculate the midpoint of the Min and Max XYZ points
                    center_point = (sheet_bb.Min + sheet_bb.Max) / 2.0
                    # print("# Calculated sheet center: {}".format(center_point))
                else:
                    print("# Warning: Could not get sheet bounding box. Placing viewport near origin (0,0,0).")
            except Exception as bb_ex:
                 print("# Warning: Error getting sheet bounding box: {}. Placing viewport near origin (0,0,0).".format(bb_ex))


            # Create the viewport centered on the sheet
            viewport = Viewport.Create(doc, sheet_id, view_id, center_point)

            if viewport:
                # print("# Successfully placed view '{}' on sheet '{}'.".format(view_to_place.Name, target_sheet.Name))
                pass # Success
            else:
                print("# Error: Viewport.Create returned None when trying to place view '{}' on sheet '{}'.".format(view_to_place.Name, target_sheet.Name))

        else:
            print("# Error: View '{}' cannot be added to sheet '{}'. It might already be placed on another sheet or is incompatible.".format(view_to_place.Name, target_sheet.Name))

    except Exception as e:
        print("# Error placing view '{}' on sheet '{}': {}".format(view_to_place.Name, target_sheet.Name, e))
#else:
    # Errors already printed above if sheet or view not found/valid
    # pass