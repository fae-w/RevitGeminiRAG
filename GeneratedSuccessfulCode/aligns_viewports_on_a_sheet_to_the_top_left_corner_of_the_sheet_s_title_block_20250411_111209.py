# Purpose: This script aligns viewports on a sheet to the top-left corner of the sheet's title block.

# Purpose: This script aligns all viewports on the active sheet to the top-left corner of the sheet's title block.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Required for List<T> if used, good practice
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ViewSheet,
    Viewport,
    FamilyInstance,
    XYZ,
    ElementTransformUtils,
    ElementId # Not strictly needed here but good practice
)
from Autodesk.Revit.Exceptions import InvalidOperationException # For specific error handling
from System.Collections.Generic import List # Not strictly needed here but good practice

# Get the active view
active_view = doc.ActiveView

# Check if the active view is a sheet
if not active_view:
    print("# Error: No active view.")
elif not isinstance(active_view, ViewSheet):
    print("# Error: Active view is not a Sheet.")
else:
    sheet = active_view
    sheet_id = sheet.Id

    # Find the title block instance on the sheet
    # Assuming there is only one title block per sheet, take the first one found
    title_block_collector = FilteredElementCollector(doc, sheet_id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType()
    title_block_instance = title_block_collector.FirstElement()

    if not title_block_instance:
        print("# Error: No title block found on the active sheet.")
    elif not isinstance(title_block_instance, FamilyInstance):
         print("# Error: Found an element in OST_TitleBlocks category that is not a FamilyInstance.")
    else:
        # Get the bounding box of the title block in the sheet's coordinates
        target_point_xy = None
        try:
            # Using the sheet (view) itself to get the context for the bounding box
            bbox = title_block_instance.get_BoundingBox(sheet)
            if bbox is None:
                 print("# Error: Could not get bounding box for the title block.")
                 # title_block_instance remains valid but target_point_xy will be None
            else:
                 # Calculate the target point (Top-Left corner of the title block bbox)
                 # Assuming sheet coordinates are XY, Z is typically 0 or constant for sheet elements.
                 # BBox Min is usually bottom-left, Max is top-right in internal coordinates.
                 # Top-Left corner would have Min.X and Max.Y
                 # We use Z=0 for the target and move vector calculation to ensure alignment only in the sheet plane.
                 target_point_xy = XYZ(bbox.Min.X, bbox.Max.Y, 0)
                 # print("# Target Point (Top-Left of Title Block BBox): {}".format(target_point_xy)) # Debug

        except Exception as e:
            print("# Error getting title block bounding box: {}".format(e))
            # target_point_xy remains None

        if target_point_xy: # Proceed only if title block and its bbox were found and target calculated
            # Find all viewports on the sheet
            viewport_collector = FilteredElementCollector(doc, sheet_id).OfClass(Viewport)
            viewports = list(viewport_collector) # Convert iterator to list

            if not viewports:
                print("# No viewports found on the active sheet.")
            else:
                moved_count = 0
                skipped_count = 0
                for viewport in viewports:
                    if not isinstance(viewport, Viewport):
                        # This check might be redundant due to OfClass(Viewport) filter but safer
                        skipped_count += 1
                        continue

                    try:
                        # Get the center of the viewport's box (excluding label)
                        current_center = viewport.GetBoxCenter()

                        # Calculate the translation vector needed to move the viewport's center to the target point
                        # Ensure the move is purely in the XY plane of the sheet
                        move_vector = XYZ(target_point_xy.X - current_center.X,
                                          target_point_xy.Y - current_center.Y,
                                          0) # Force Z component to 0

                        # Check if movement is needed (avoid unnecessary API calls for tiny movements)
                        # Use a small tolerance for floating point comparisons
                        if move_vector.GetLength() > 1e-9:
                            ElementTransformUtils.MoveElement(doc, viewport.Id, move_vector)
                            moved_count += 1
                        else:
                            # Already aligned or close enough
                            skipped_count += 1

                    except InvalidOperationException as ioe:
                         # This might occur if GetBoxCenter fails for some reason, e.g., viewport state issues
                         # print("# Skipping viewport ID {}: Error - {}. Might be an issue with GetBoxCenter.".format(viewport.Id, ioe.Message)) # Debug
                         skipped_count += 1
                    except Exception as ex:
                        # Catch any other unexpected errors during processing a single viewport
                        # print("# Skipping viewport ID {}: Unexpected error during processing - {}".format(viewport.Id, ex)) # Debug
                        skipped_count += 1

                # Optional summary message (commented out by default)
                # print("# Attempted to align {} viewports. Skipped {} viewports.".format(moved_count, skipped_count))
        elif title_block_instance: # Title block was found, but bbox failed
             print("# Could not determine target alignment point from title block bounding box.")
        # else: # title_block_instance was None already handled by the initial check
             # pass