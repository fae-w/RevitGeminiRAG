# Purpose: This script creates a new sheet in Revit and places specified drafting views onto it.

﻿# Import necessary classes
import clr
clr.AddReference('System') # Required for Exception handling and generic collections
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    ViewDrafting,
    Viewport,
    ElementId,
    XYZ,
    BuiltInCategory,
    FamilySymbol,
    ViewFamily # Needed for ViewFamily.Drafting comparison if necessary, though OfClass(ViewDrafting) is better
)
import System # For Exception handling

# --- Configuration ---
new_sheet_number = "D-001" # Proposed sheet number
new_sheet_name = "Standard Details"
placement_start_x = 0.5 # Starting X position (in feet from sheet origin - usually lower left)
placement_start_y = 0.5 # Starting Y position
placement_offset_x = 2.0 # Offset for next view in X direction (feet) - increased spacing
placement_offset_y = 0 # Keep Y constant for a row layout

# --- Find Drafting Views ---
# Filter for elements of class ViewDrafting
drafting_view_collector = FilteredElementCollector(doc).OfClass(ViewDrafting)
# Ensure they are not view templates
drafting_views_to_place = [v for v in drafting_view_collector if v and v.IsValidObject and not v.IsTemplate]

if not drafting_views_to_place:
    print("# No non-template Drafting Views found to place on the new sheet.")
    # If no drafting views, script effectively stops here as 'else' block won't run
else:
    print("# Found {} non-template Drafting Views.".format(len(drafting_views_to_place)))

    # --- Find a Title Block ---
    # Get all TitleBlock types (FamilySymbols)
    titleblock_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
    first_titleblock_id = ElementId.InvalidElementId
    titleblock_types = list(titleblock_collector)

    if titleblock_types:
        # Use the first available title block type found
        first_titleblock_id = titleblock_types[0].Id
        try:
             # Attempt to get the name for logging purposes
             tb_name = titleblock_types[0].get_Parameter(BuiltInCategory.SYMBOL_NAME_PARAM).AsString()
             if not tb_name: # Fallback if SYMBOL_NAME_PARAM is null/empty
                 tb_name = Element.Name.__get__(titleblock_types[0])
             print("# Using title block type: '{}' (ID: {})".format(tb_name, first_titleblock_id))
        except:
             print("# Using first available title block type (ID: {})".format(first_titleblock_id)) # Name retrieval failed
    else:
        print("# Warning: No title block types found in the project. Creating sheet without a title block.")

    # --- Create the New Sheet ---
    new_sheet = None
    try:
        # Create the sheet using the found title block ID (or InvalidElementId if none found)
        new_sheet = ViewSheet.Create(doc, first_titleblock_id)

        if new_sheet:
            # Set the desired name
            new_sheet.Name = new_sheet_name

            # Check if the proposed sheet number already exists and find a unique one if needed
            existing_sheet_numbers = [s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet) if s.Id != new_sheet.Id] # Exclude the sheet just created
            temp_sheet_number = new_sheet_number
            num_suffix = 1
            max_attempts = 100 # Prevent infinite loop
            while temp_sheet_number in existing_sheet_numbers and num_suffix <= max_attempts:
                temp_sheet_number = "{}-{:02d}".format(new_sheet_number, num_suffix) # Pad suffix e.g., D-001-01
                num_suffix += 1

            if temp_sheet_number != new_sheet_number:
                 if num_suffix > max_attempts:
                     print("# Error: Could not find a unique sheet number after {} attempts. Using default.".format(max_attempts))
                     # Attempt to set the original number anyway, may fail if truly duplicate
                     new_sheet.SheetNumber = new_sheet_number
                 else:
                     print("# Warning: Sheet number '{}' already exists or is invalid. Using '{}' instead.".format(new_sheet_number, temp_sheet_number))
                     new_sheet.SheetNumber = temp_sheet_number
            else:
                new_sheet.SheetNumber = new_sheet_number # Set the original number

            print("# Successfully created new sheet: '{}' (Number: {})".format(new_sheet.Name, new_sheet.SheetNumber))
        else:
            # ViewSheet.Create can return null if it fails internally before throwing an exception
            print("# Error: Failed to create the new sheet (ViewSheet.Create returned null).")

    except System.Exception as create_ex:
        print("# Error during sheet creation: {}".format(create_ex))
        new_sheet = None # Ensure new_sheet is None if creation failed

    # --- Place Drafting Views on the Sheet ---
    if new_sheet and new_sheet.IsValidObject: # Proceed only if sheet creation was successful
        placed_count = 0
        failed_count = 0
        skipped_count = 0
        current_x = placement_start_x
        current_y = placement_start_y
        views_already_on_sheets = {} # Cache views already placed to avoid re-checking

        # Pre-check which views might already be on *any* sheet
        all_viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()
        for vp in all_viewports:
            if vp and vp.IsValidObject:
                views_already_on_sheets[vp.ViewId] = vp.SheetId

        print("# Attempting to place {} drafting views...".format(len(drafting_views_to_place)))
        for i, view in enumerate(drafting_views_to_place):
            if not view or not view.IsValidObject:
                print("# Skipped invalid view element encountered during placement.")
                skipped_count += 1
                continue

            view_id = view.Id
            view_name = "Unknown View"
            try:
                view_name = Element.Name.__get__(view)
            except: pass # Keep default name if fails

            try:
                # Check if view is already on *any* sheet
                if view_id in views_already_on_sheets:
                     # Optional: Check if it's on the *new* sheet already (unlikely here but good practice)
                     if views_already_on_sheets[view_id] == new_sheet.Id:
                          print("# Info: View '{}' (ID: {}) seems already placed on the target sheet '{}'".format(view_name, view_id, new_sheet.SheetNumber))
                          # Count as skipped rather than failed if already present
                          skipped_count += 1
                     else:
                          # It's on a DIFFERENT sheet. Revit generally allows a view on only one sheet.
                          other_sheet = doc.GetElement(views_already_on_sheets[view_id])
                          other_sheet_num = "Unknown Sheet"
                          if other_sheet and other_sheet.IsValidObject:
                              try: other_sheet_num = other_sheet.SheetNumber
                              except: pass
                          print("# Skipped: View '{}' (ID: {}) is already placed on sheet '{}'.".format(view_name, view_id, other_sheet_num))
                          skipped_count += 1
                     continue # Move to the next view

                # Verify if the view *can* be added (redundant if already checked above, but safe)
                if Viewport.CanAddViewToSheet(doc, new_sheet.Id, view_id):
                    # Calculate position for this viewport
                    placement_point = XYZ(current_x, current_y, 0)

                    # Create the viewport
                    viewport = Viewport.Create(doc, new_sheet.Id, view_id, placement_point)

                    if viewport and viewport.IsValidObject:
                        placed_count += 1
                        # print("# Placed view '{}' on sheet '{}'".format(view_name, new_sheet.SheetNumber)) # Optional debug
                        # Increment position for the next view
                        current_x += placement_offset_x
                        # TODO: Add logic here to wrap to the next row if current_x exceeds a reasonable sheet width estimate?
                        # For now, it just creates a single potentially very long row.
                    else:
                        failed_count += 1
                        print("# Warning: Failed to create viewport for view '{}' (ID: {}) on sheet '{}'. Viewport.Create returned null or invalid.".format(view_name, view_id, new_sheet.SheetNumber))
                else:
                    # This block might be reached if CanAddViewToSheet fails for reasons other than already being placed (e.g., view type incompatibility, though unlikely for DraftingView)
                    failed_count += 1
                    print("# Warning: Cannot add view '{}' (ID: {}) to sheet '{}'. CanAddViewToSheet returned false.".format(view_name, view_id, new_sheet.SheetNumber))

            except System.Exception as place_ex:
                failed_count += 1
                print("# Error placing view '{}' (ID: {}): {}".format(view_name, view_id, place_ex))
            except Exception as py_ex: # Catch Python specific errors too
                 failed_count += 1
                 print("# Python Error placing view '{}' (ID: {}): {}".format(view_name, view_id, py_ex))

        print("\n# --- Placement Summary ---")
        print("# Sheet: '{}' (Number: {})".format(new_sheet.Name, new_sheet.SheetNumber))
        print("# Successfully placed {} drafting views.".format(placed_count))
        print("# Skipped {} views (e.g., already on a sheet).".format(skipped_count))
        print("# Failed to place {} drafting views.".format(failed_count))
    elif not new_sheet:
        # This case handles if sheet creation failed earlier
        print("# Cannot place views as sheet creation failed or the sheet object is invalid.")