# Purpose: This script automates the placement of specified views onto a Revit sheet.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for Exception handling
import System

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewSheet,
    Viewport,
    ElementId,
    XYZ,
    BoundingBoxUV,
    FamilySymbol,
    BuiltInCategory,
    BuiltInParameter, # Import BuiltInParameter
    ViewPlacementOnSheetStatus
)

# --- Configuration ---
target_sheet_number = "A-001"
target_sheet_name = "Generated Sheet" # Optional name if creating
view_names_to_place = ['Parking Plan', 'L1 - Block 35 Plan', 'L1 - Block 43 Plan', 'R1 Plan']

# --- Helper Function ---
def find_view_by_name(doc_param, view_name):
    """Finds a View element by its exact name, excluding view templates."""
    views = FilteredElementCollector(doc_param).OfClass(View).ToElements()
    for v in views:
        if v.IsTemplate:
            continue
        # Use Parameter for Name to handle potential variations in View subclasses
        # Corrected: Use BuiltInParameter.VIEW_NAME
        name_param = v.get_Parameter(BuiltInParameter.VIEW_NAME)
        if name_param and name_param.AsString() == view_name:
            return v
        # Fallback for views where Name property works directly and matches
        try:
            if hasattr(v, "Name") and v.Name == view_name:
                 return v
        except:
            pass # Ignore errors accessing Name property on certain view types
    return None

# --- Main Logic ---
sheet = None
found_views = {} # Dictionary to store found View objects {name: view_element}
view_ids_to_place = [] # List of ElementIds of views to place

# 1. Find the target views
print("# Searching for specified views...")
for view_name in view_names_to_place:
    view = find_view_by_name(doc, view_name)
    if view:
        found_views[view_name] = view
        view_ids_to_place.append(view.Id)
        print("# Found view: '{}' (ID: {})".format(view_name, view.Id.IntegerValue))
    else:
        print("# Error: View named '{}' not found. It will be skipped.".format(view_name))

if not found_views:
    print("# Error: No valid views found to place. Script terminated.")
else:
    # 2. Find or Create the Sheet
    print("# Searching for or creating sheet '{}'...".format(target_sheet_number))
    sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
    existing_sheet = None
    for s in sheet_collector:
        if s.SheetNumber == target_sheet_number:
            existing_sheet = s
            break

    if existing_sheet:
        sheet = existing_sheet
        print("# Found existing sheet: '{}' - '{}' (ID: {})".format(sheet.SheetNumber, sheet.Name, sheet.Id.IntegerValue))
    else:
        print("# Sheet '{}' not found. Attempting to create it.".format(target_sheet_number))
        # Find a title block type to use
        title_block_collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
        first_title_block_id = title_block_collector.FirstElementId()

        if first_title_block_id is None or first_title_block_id == ElementId.InvalidElementId:
            print("# Error: No Title Block types found in the project. Cannot create a new sheet.")
            sheet = None # Ensure sheet is None if creation fails
        else:
            try:
                # NOTE: Transaction handled by C# wrapper
                sheet = ViewSheet.Create(doc, first_title_block_id)
                sheet.SheetNumber = target_sheet_number
                sheet.Name = target_sheet_name # Set the name
                print("# Successfully created new sheet: '{}' - '{}' (ID: {})".format(sheet.SheetNumber, sheet.Name, sheet.Id.IntegerValue))
            except System.Exception as create_ex:
                print("# Error creating sheet '{}': {}".format(target_sheet_number, str(create_ex)))
                # Check if the error was due to duplicate number *after* attempting creation
                sheet_collector_retry = FilteredElementCollector(doc).OfClass(ViewSheet)
                for s_retry in sheet_collector_retry:
                    if s_retry.SheetNumber == target_sheet_number:
                        sheet = s_retry
                        print("# Found sheet '{}' after creation attempt failed (likely duplicate number). Using existing sheet.".format(target_sheet_number))
                        break
                if not sheet: # Still couldn't find or create
                     print("# Fatal Error: Could not find or create sheet '{}'".format(target_sheet_number))


    # 3. Place Views if Sheet is available
    if sheet:
        sheet_id = sheet.Id
        placed_count = 0
        skipped_count = 0

        # Basic grid layout calculation (assuming 4 views -> 2x2 grid)
        # Get sheet dimensions (may be inaccurate if title block has complex shape or sheet is empty)
        sheet_width = 1.0 # Default width in feet if outline fails
        sheet_height = 1.0 # Default height in feet if outline fails
        points = None
        try:
            # Try getting the Bounding Box of the Title Block if available
            titleblock_bb = None
            titleblock_instance = None
            tb_collector = FilteredElementCollector(doc).OwnedByView(sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType()
            if tb_collector.Any():
                titleblock_instance = tb_collector.FirstElement()
            if titleblock_instance:
                 # BoundingBoxXYZ gives model coords, we need sheet coords (UV)
                 # Getting sheet outline directly is often problematic.
                 # Let's use the BoundingBoxUV approach if titleblock exists
                 bb = titleblock_instance.get_BoundingBox(sheet) # Get BB relative to the sheet view
                 if bb:
                     min_u, max_u = bb.Min.U, bb.Max.U
                     min_v, max_v = bb.Min.V, bb.Max.V
                     sheet_width = max_u - min_u
                     sheet_height = max_v - min_v
                     print("# Using TitleBlock BBox (WxH): {:.2f} x {:.2f} feet".format(sheet_width, sheet_height))
                     # Define grid points based on center of quadrants (relative to min U/V)
                     points = [
                         XYZ(min_u + sheet_width * 0.25, min_v + sheet_height * 0.75, 0), # Top-Left
                         XYZ(min_u + sheet_width * 0.75, min_v + sheet_height * 0.75, 0), # Top-Right
                         XYZ(min_u + sheet_width * 0.25, min_v + sheet_height * 0.25, 0), # Bottom-Left
                         XYZ(min_u + sheet_width * 0.75, min_v + sheet_height * 0.25, 0)  # Bottom-Right
                     ]

            if not points: # Fallback if title block bb not found or sheet.Outline is needed
                 outline = sheet.Outline
                 if outline and outline.Min and outline.Max:
                     min_u, max_u = outline.Min.U, outline.Max.U
                     min_v, max_v = outline.Min.V, outline.Max.V
                     sheet_width = max_u - min_u
                     sheet_height = max_v - min_v
                     print("# Using Sheet Outline (WxH): {:.2f} x {:.2f} feet".format(sheet_width, sheet_height))
                     points = [
                         XYZ(min_u + sheet_width * 0.25, min_v + sheet_height * 0.75, 0), # Top-Left
                         XYZ(min_u + sheet_width * 0.75, min_v + sheet_height * 0.75, 0), # Top-Right
                         XYZ(min_u + sheet_width * 0.25, min_v + sheet_height * 0.25, 0), # Bottom-Left
                         XYZ(min_u + sheet_width * 0.75, min_v + sheet_height * 0.25, 0)  # Bottom-Right
                     ]
                 else:
                      print("# Warning: Could not get sheet outline or TitleBlock BBox. Using default placement points.")
                      points = [XYZ(0.75, 2.0, 0), XYZ(2.25, 2.0, 0), XYZ(0.75, 0.75, 0), XYZ(2.25, 0.75, 0)]

        except System.Exception as outline_ex:
             print("# Warning: Error getting sheet dimensions ({}). Using default placement points.".format(str(outline_ex)))
             points = [XYZ(0.75, 2.0, 0), XYZ(2.25, 2.0, 0), XYZ(0.75, 0.75, 0), XYZ(2.25, 0.75, 0)]

        # Iterate through found views and attempt placement
        print("# Attempting to place views...")
        view_index = 0
        for view_name, view_element in found_views.items():
            if view_index >= len(points):
                print("# Warning: More views than available placement points ({}) in grid. Skipping remaining views.".format(len(points)))
                skipped_count += (len(found_views) - view_index)
                break

            view_id = view_element.Id
            placement_point = points[view_index]

            # Check if view can be added
            if Viewport.CanAddViewToSheet(doc, sheet_id, view_id):
                try:
                    # Check current placement status (informational)
                    placement_status = view_element.GetPlacementOnSheetStatus()
                    if placement_status != ViewPlacementOnSheetStatus.NotPlaced:
                         print("# Info: View '{}' is already placed (Status: {}). Attempting placement anyway.".format(view_name, placement_status))

                    # NOTE: Transaction handled by C# wrapper
                    new_viewport = Viewport.Create(doc, sheet_id, view_id, placement_point)
                    if new_viewport:
                        print("# Successfully placed view '{}' at ({:.2f}, {:.2f}) on sheet '{}'.".format(view_name, placement_point.X, placement_point.Y, target_sheet_number))
                        placed_count += 1
                    else:
                        print("# Error: Viewport.Create returned None for view '{}'. Placement failed.".format(view_name))
                        skipped_count += 1
                except System.Exception as place_ex:
                    print("# Error placing view '{}': {}".format(view_name, str(place_ex)))
                    skipped_count += 1
            else:
                # Check if view is already on *this* sheet
                is_on_this_sheet = False
                existing_viewports = FilteredElementCollector(doc, sheet_id).OfClass(Viewport).ToElements()
                for vp in existing_viewports:
                    if vp.ViewId == view_id:
                        is_on_this_sheet = True
                        break

                if is_on_this_sheet:
                     print("# Info: View '{}' is already placed on sheet '{}'. Cannot place again.".format(view_name, target_sheet_number))
                else:
                    print("# Error: View '{}' cannot be added to sheet '{}'. It might be incompatible or already placed exclusively on another sheet.".format(view_name, target_sheet_number))
                    # Additional check: what is the current placement status?
                    placement_status = view_element.GetPlacementOnSheetStatus()
                    print("# Current placement status of view '{}': {}".format(view_name, placement_status))
                skipped_count += 1

            view_index += 1

        print("# --- Placement Summary ---")
        print("# Sheet: '{}' - '{}'".format(sheet.SheetNumber, sheet.Name))
        print("# Views Found: {}".format(len(found_views)))
        print("# Views Successfully Placed: {}".format(placed_count))
        print("# Views Skipped/Failed: {}".format(skipped_count))

    else:
        # This case means sheet creation/finding failed earlier
        print("# Error: Cannot proceed with view placement as the sheet '{}' could not be found or created.".format(target_sheet_number))