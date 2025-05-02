# Purpose: This script places specified legend views onto a designated Revit sheet.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewType,
    ViewSheet,
    Viewport,
    XYZ,
    ElementId,
    BuiltInParameter
)

# --- Configuration ---
target_sheet_name = "G-002"
view_name_keyword = "Legend"
# Starting position for the center of the first viewport (in feet from sheet origin)
start_x = 1.0
start_y = 10.0
# Vertical distance between the centers of consecutive viewports (in feet)
vertical_offset = 2.0

# --- Find the target sheet ---
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
target_sheet = None
for sheet in sheet_collector:
    if sheet.Name == target_sheet_name:
        target_sheet = sheet
        break

if not target_sheet:
    print("# Error: Sheet '{}' not found.".format(target_sheet_name))
else:
    # --- Find Legend views containing the keyword ---
    view_collector = FilteredElementCollector(doc).OfClass(View)
    legend_views_to_place = []
    for view in view_collector:
        # Check if it's a Legend view and contains the keyword
        if view.ViewType == ViewType.Legend and view_name_keyword in view.Name:
            # Check if the view can be placed on the sheet
            if Viewport.CanAddViewToSheet(doc, target_sheet.Id, view.Id):
                legend_views_to_place.append(view)
            # else: # Optional: Inform user if a view cannot be placed
                # print("# Info: View '{}' (ID: {}) cannot be added to sheet '{}'. It might be a template or already restricted.".format(view.Name, view.Id, target_sheet.Name))

    if not legend_views_to_place:
        print("# Info: No suitable Legend views containing '{}' found or none could be placed on sheet '{}'.".format(view_name_keyword, target_sheet_name))
    else:
        # --- Place the views ---
        current_x = start_x
        current_y = start_y
        placed_count = 0

        for view in legend_views_to_place:
            try:
                placement_point = XYZ(current_x, current_y, 0)
                # Create the viewport (places the view's center at the point)
                viewport = Viewport.Create(doc, target_sheet.Id, view.Id, placement_point)
                if viewport:
                    # print("# Placed view '{}' (ID: {}) on sheet '{}' at ({}, {})".format(view.Name, view.Id, target_sheet.Name, current_x, current_y)) # Debug
                    placed_count += 1
                    # Update the Y coordinate for the next viewport
                    current_y -= vertical_offset
                #else: # Should not happen if CanAddViewToSheet passed, but good practice
                    #print("# Warning: Failed to create viewport for view '{}' (ID: {})".format(view.Name, view.Id))
            except Exception as e:
                print("# Error placing view '{}' (ID: {}): {}".format(view.Name, view.Id, e))

        # print("# Summary: Placed {} legend views on sheet '{}'.".format(placed_count, target_sheet_name)) # Final Summary