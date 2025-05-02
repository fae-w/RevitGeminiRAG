# Purpose: This script adds a specified drafting view to selected Revit sheets within a defined number range.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ViewDrafting, ViewSheet, Viewport, XYZ, ElementId, BuiltInCategory
import System # For exception handling, though not strictly required by constraints

# --- Configuration ---
drafting_view_name = "General Notes"
sheet_number_prefix = "A-"
sheet_number_start = 100
sheet_number_end = 199
# Define the desired *center* point for the viewport on the sheet (in feet from sheet origin - bottom-left)
# Adjust these values as needed for desired placement near the top-left.
# A point like (1.0, 8.0) might place the center 1 foot right and 8 feet up.
viewport_center_point = XYZ(1.0, 8.0, 0.0)

# --- Find the Drafting View ---
drafting_view = None
collector = FilteredElementCollector(doc).OfClass(ViewDrafting)
for view in collector:
    if view.Name == drafting_view_name:
        drafting_view = view
        break

if not drafting_view:
    print("# Error: Drafting View named '{}' not found.".format(drafting_view_name))
else:
    drafting_view_id = drafting_view.Id
    print("# Found Drafting View: '{}' (ID: {})".format(drafting_view_name, drafting_view_id.IntegerValue))

    # --- Find Target Sheets and Add Viewport ---
    sheets_processed_count = 0
    viewports_added_count = 0
    skipped_sheets_count = 0

    sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)

    for sheet in sheet_collector:
        if not isinstance(sheet, ViewSheet):
            continue

        sheet_number = sheet.SheetNumber
        # Check if the sheet number starts with the prefix and falls within the numeric range
        is_target_sheet = False
        if sheet_number.startswith(sheet_number_prefix):
            try:
                number_part = sheet_number[len(sheet_number_prefix):]
                sheet_num_int = int(number_part)
                if sheet_number_start <= sheet_num_int <= sheet_number_end:
                    is_target_sheet = True
            except ValueError:
                # Handle cases where the part after prefix is not a valid integer
                pass # Not a target sheet if conversion fails

        if is_target_sheet:
            sheets_processed_count += 1
            sheet_id = sheet.Id

            # Check if the view can be added (avoids duplicates and handles certain view restrictions)
            can_add = False
            try:
                 # Check if view already exists on the sheet by iterating placed views
                 view_already_on_sheet = False
                 placed_view_ids = sheet.GetAllPlacedViews()
                 for placed_view_id in placed_view_ids:
                     if placed_view_id == drafting_view_id:
                         view_already_on_sheet = True
                         break

                 if not view_already_on_sheet:
                      # Use CanAddViewToSheet for a more robust check if needed, though direct check is often sufficient
                      # can_add = Viewport.CanAddViewToSheet(doc, sheet_id, drafting_view_id)
                      can_add = True # Assume true if not already present
                 else:
                      print("# Info: View '{}' already exists on sheet '{}'. Skipping.".format(drafting_view_name, sheet_number))
                      skipped_sheets_count += 1


            except System.Exception as e:
                 print("# Warning: Could not check if view can be added to sheet '{}'. Error: {}".format(sheet_number, e))
                 # Optionally skip or try adding anyway depending on desired behavior
                 skipped_sheets_count += 1


            if can_add and not view_already_on_sheet:
                try:
                    # Create the viewport
                    new_viewport = Viewport.Create(doc, sheet_id, drafting_view_id, viewport_center_point)
                    if new_viewport:
                        print("# Added viewport for '{}' to sheet '{}'.".format(drafting_view_name, sheet_number))
                        viewports_added_count += 1
                    else:
                         print("# Error: Failed to create viewport on sheet '{}'.".format(sheet_number))
                         skipped_sheets_count += 1
                except System.Exception as e:
                    print("# Error: Could not create viewport on sheet '{}'. Reason: {}".format(sheet_number, e))
                    skipped_sheets_count += 1

    print("# --- Summary ---")
    print("# Target Sheets Processed (Range {}{} to {}{}): {}".format(sheet_number_prefix, sheet_number_start, sheet_number_prefix, sheet_number_end, sheets_processed_count))
    print("# Viewports Added: {}".format(viewports_added_count))
    print("# Sheets Skipped (Already Exists or Error): {}".format(skipped_sheets_count))

if drafting_view and sheets_processed_count == 0:
     print("# Info: No sheets found matching the number range '{}{}' to '{}{}'.".format(sheet_number_prefix, sheet_number_start, sheet_number_prefix, sheet_number_end))