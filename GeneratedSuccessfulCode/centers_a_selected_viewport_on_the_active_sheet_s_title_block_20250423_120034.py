# Purpose: This script centers a selected viewport on the active sheet's title block.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ViewSheet,
    Viewport,
    FamilyInstance,
    XYZ,
    ElementTransformUtils,
    ElementId,
    BoundingBoxXYZ # Needed for title block bounding box
)
from System.Collections.Generic import ICollection

# Get the active view
active_view = doc.ActiveView

# Check if the active view is a sheet
if not isinstance(active_view, ViewSheet):
    print("# Error: Active view is not a Sheet.")
else:
    sheet = active_view
    sheet_id = sheet.Id

    # Get the current selection
    selected_ids = uidoc.Selection.GetElementIds()

    # Validate selection: Ensure exactly one element is selected and it's a Viewport
    selected_viewport = None
    if not selected_ids or selected_ids.Count == 0:
        print("# Error: Please select exactly one Viewport to center.")
    elif selected_ids.Count > 1:
        print("# Error: More than one element selected. Please select exactly one Viewport.")
    else:
        selected_element = doc.GetElement(selected_ids[0])
        if not isinstance(selected_element, Viewport):
            print("# Error: The selected element is not a Viewport.")
        elif selected_element.SheetId != sheet_id:
             print("# Error: The selected Viewport is not on the active sheet.")
        else:
            selected_viewport = selected_element
            # print("# Selected Viewport ID: {}".format(selected_viewport.Id)) # Debug

    # Proceed only if a valid viewport was selected on the active sheet
    if selected_viewport:
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
            target_center_point = None
            try:
                bbox = title_block_instance.get_BoundingBox(sheet) # Use sheet view context
                if bbox is None or bbox.Min is None or bbox.Max is None:
                    print("# Error: Could not get a valid bounding box for the title block.")
                else:
                    # Calculate the target center point (center of the title block bbox)
                    # Ensure Z component is 0 for sheet coordinate system
                    target_center_point = (bbox.Min + bbox.Max) / 2.0
                    target_center_point = XYZ(target_center_point.X, target_center_point.Y, 0)
                    # print("# Target Center (Title Block BBox Center): {}".format(target_center_point)) # Debug

            except Exception as e:
                print("# Error getting title block bounding box or calculating center: {}".format(e))
                target_center_point = None

            # Proceed only if target center point was calculated
            if target_center_point:
                try:
                    # Get the current center of the viewport's box (excluding label)
                    current_center = selected_viewport.GetBoxCenter()
                    # Ensure Z component is 0 for vector calculation in sheet plane
                    current_center = XYZ(current_center.X, current_center.Y, 0)
                    # print("# Current Viewport Center: {}".format(current_center)) # Debug

                    # Calculate the translation vector needed
                    move_vector = target_center_point - current_center

                    # Check if movement is needed (avoid unnecessary API calls for tiny movements)
                    if move_vector.GetLength() > 1e-9:
                        ElementTransformUtils.MoveElement(doc, selected_viewport.Id, move_vector)
                        # print("# Viewport moved successfully.") # Debug
                    #else:
                        # print("# Viewport already centered.") # Debug

                except Exception as ex:
                    print("# Error getting viewport center or moving viewport: {}".format(ex))
            #else:
                 # Error message already printed if target_center_point is None
                 # pass
        #else:
             # Error message already printed if title_block_instance is None or not FamilyInstance
             # pass
    #else:
        # Error message already printed if selection was invalid
        # pass
#else:
    # Error message already printed if active view is not a sheet
    # pass