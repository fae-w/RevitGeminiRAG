# Purpose: This script aligns selected viewports on a Revit sheet to the lowest bottom edge.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    Outline,
    XYZ,
    ElementTransformUtils,
    ElementId,
    Element # Import Element base class for GetElement
)
from Autodesk.Revit.Exceptions import InvalidOperationException

# Get the active view
active_view = doc.ActiveView

# Check if the active view is a sheet
if not isinstance(active_view, ViewSheet):
    print("# Error: The active view is not a sheet.")
else:
    sheet = active_view
    sheet_id = sheet.Id

    # Get selected element IDs
    selected_ids = uidoc.Selection.GetElementIds()

    if not selected_ids:
        print("# Error: No elements selected.")
    else:
        selected_viewports = []
        # Filter selected elements to get only Viewports on the active sheet
        for element_id in selected_ids:
            element = doc.GetElement(element_id)
            if isinstance(element, Viewport) and element.SheetId == sheet_id:
                selected_viewports.append(element)

        if not selected_viewports:
            print("# Error: No viewports selected on the active sheet.")
        elif len(selected_viewports) < 2:
            print("# Info: Only one or zero viewports selected. Alignment requires at least two.")
        else:
            # Find the lowest bottom edge Y-coordinate among selected viewports
            min_bottom_y = None
            error_getting_bounds = False

            for viewport in selected_viewports:
                try:
                    outline = viewport.GetBoxOutline() # Outline excluding label
                    if outline and outline.MinimumPoint:
                        bottom_y = outline.MinimumPoint.Y
                        if min_bottom_y is None or bottom_y < min_bottom_y:
                            min_bottom_y = bottom_y
                    else:
                        print("# Warning: Could not get valid outline for viewport ID {}. Skipping.".format(viewport.Id))
                        error_getting_bounds = True # Mark that at least one failed, alignment might be inaccurate

                except InvalidOperationException:
                    print("# Warning: Viewport ID {} might not be properly placed on the sheet or has issues. Skipping.".format(viewport.Id))
                    error_getting_bounds = True
                except Exception as e:
                    print("# Warning: Unexpected error getting outline for viewport ID {}: {}. Skipping.".format(viewport.Id, e))
                    error_getting_bounds = True

            if min_bottom_y is None:
                print("# Error: Could not determine the target alignment position from the selected viewports.")
            else:
                # Align each selected viewport to the lowest bottom edge
                moved_count = 0
                skipped_count = 0
                tolerance = 1e-9 # Tolerance for floating point comparison

                for viewport in selected_viewports:
                    try:
                        current_outline = viewport.GetBoxOutline()
                        if current_outline and current_outline.MinimumPoint:
                            current_bottom_y = current_outline.MinimumPoint.Y
                            delta_y = min_bottom_y - current_bottom_y

                            # Only move if the difference is significant
                            if abs(delta_y) > tolerance:
                                move_vector = XYZ(0, delta_y, 0)
                                ElementTransformUtils.MoveElement(doc, viewport.Id, move_vector)
                                moved_count += 1
                            else:
                                skipped_count += 1 # Already aligned
                        else:
                             # Already warned about outline issues above
                             skipped_count += 1

                    except InvalidOperationException:
                         # Already warned about outline issues above
                         skipped_count += 1
                    except Exception as e:
                        print("# Error moving viewport ID {}: {}".format(viewport.Id, e))
                        skipped_count += 1

                # Optional summary (uncomment if needed)
                # print("# Alignment process completed. Moved {} viewports, skipped {}.".format(moved_count, skipped_count))
                # if error_getting_bounds:
                #     print("# Note: Some viewport bounds could not be determined, alignment might not include all intended elements or be perfectly accurate.")