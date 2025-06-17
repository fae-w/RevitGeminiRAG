# Purpose: This script automates the creation of floor plan views and sheets for specified levels in a Revit project.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for Exception handling
import System # Import System for exception types

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewPlan,
    ViewSheet,
    Viewport,
    ViewFamilyType,
    ViewType,
    View,
    ElementId,
    XYZ,
    BuiltInCategory,
    FamilySymbol,
    BuiltInParameter,
    ViewPlacementOnSheetStatus
)

# --- Configuration ---
level_names = [
    'Parking', 'L1 - Block 35', 'L1 - Block 43', 'M1', 'L2', 'L3', 'L4', 'L5', 'R1', 'R2'
]
view_template_name = "General Floor Plan"
sheet_name_suffix = " Plan"
# Use first available Floor Plan VFT and Title Block
# Default placement point if sheet center calculation fails (in feet from origin)
default_placement_point = XYZ(1.5, 1.0, 0)

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    for level in levels:
        if level.Name == level_name:
            return level
    print("# Error: Level named '{{}}' not found.".format(level_name))
    return None

def find_view_template_by_name(doc_param, template_name):
    """Finds a View Template by its exact name."""
    views = FilteredElementCollector(doc_param).OfClass(View).ToElements()
    for v in views:
        if v.IsTemplate and v.Name == template_name:
            return v
    print("# Error: View Template named '{{}}' not found.".format(template_name))
    return None

def find_floor_plan_vft(doc_param):
    """Finds the first available Floor Plan ViewFamilyType."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        if vft.ViewFamily == ViewType.FloorPlan:
            return vft
    print("# Error: No Floor Plan View Family Type found in the document.")
    return None

def find_title_block_type(doc_param):
    """Finds the first available Title Block FamilySymbol."""
    tb_collector = FilteredElementCollector(doc_param).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
    first_tb_id = tb_collector.FirstElementId()
    if first_tb_id and first_tb_id != ElementId.InvalidElementId:
        return doc_param.GetElement(first_tb_id)
    print("# Error: No Title Block types found in the project.")
    return None

def get_sheet_center(sheet, doc_param):
    """Attempts to find the center point of the sheet, ideally based on the title block."""
    center_point = default_placement_point # Start with default
    try:
        # Find the title block instance on the sheet
        tb_collector = FilteredElementCollector(doc_param, sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType()
        title_block_instance = tb_collector.FirstElement()

        if title_block_instance:
            # Ensure sheet view is active or regenerated enough to get bounds
            # doc_param.Regenerate() # May be needed but expensive in a loop
            bb = title_block_instance.get_BoundingBox(sheet) # BBox relative to sheet UV coords
            if bb and bb.Min and bb.Max:
                # Check if the BBox is valid (Min < Max)
                if bb.Min.U < bb.Max.U and bb.Min.V < bb.Max.V:
                    center_u = (bb.Min.U + bb.Max.U) / 2.0
                    center_v = (bb.Min.V + bb.Max.V) / 2.0
                    center_point = XYZ(center_u, center_v, 0)
                    # print("# Calculated sheet center from Title Block: ({{:.2f}}, {{:.2f}})".format(center_u, center_v)) # Debug
                else:
                    print("# Warning: Invalid BoundingBox dimensions for Title Block on sheet '{{}}'. Using default center.".format(sheet.SheetNumber))
            else:
                print("# Warning: Could not get BoundingBox from Title Block on sheet '{{}}'. Using default center.".format(sheet.SheetNumber))
        else:
             print("# Warning: No Title Block found on sheet '{{}}' to determine center. Using default center.".format(sheet.SheetNumber))

    except System.Exception as ex:
        print("# Warning: Error calculating sheet center for sheet '{{}}': {{}}. Using default center.".format(sheet.SheetNumber, str(ex)))

    return center_point

# --- Pre-computation: Find common elements once ---
print("# Locating prerequisites...")
view_template = find_view_template_by_name(doc, view_template_name)
floor_plan_vft = find_floor_plan_vft(doc)
title_block_type = find_title_block_type(doc)

# --- Main Loop ---
if not view_template:
    print("# Stopping script: View Template '{{}}' is required but not found.".format(view_template_name))
elif not floor_plan_vft:
    print("# Stopping script: A Floor Plan View Family Type is required but not found.")
elif not title_block_type:
    print("# Stopping script: A Title Block Type is required but not found.")
else:
    print("# Prerequisites found: View Template, Floor Plan VFT, Title Block Type.")
    print("# Starting processing for {{}} levels...".format(len(level_names)))
    processed_count = 0
    skipped_count = 0
    created_view_ids = [] # Keep track of views created in this run
    created_sheet_ids = [] # Keep track of sheets created in this run

    for level_name in level_names:
        print("\n# --- Processing Level: {{}} ---".format(level_name))
        level = find_level_by_name(doc, level_name)
        if not level:
            skipped_count += 1
            continue # Skip to next level if this one isn't found

        level_id = level.Id
        new_view = None
        new_sheet = None

        # 1. Create Floor Plan View
        try:
            print("# Creating Floor Plan view for level '{{}}'...".format(level_name))
            # NOTE: Transaction handled by C# wrapper
            new_view = ViewPlan.Create(doc, floor_plan_vft.Id, level_id)
            doc.Regenerate() # Regenerate to ensure view properties are stable
            print("# Successfully created view '{{}}' (ID: {{}})".format(new_view.Name, new_view.Id.IntegerValue))
            created_view_ids.append(new_view.Id) # Track created view
        except System.Exception as ex:
            print("# Error creating view for level '{{}}': {{}}".format(level_name, str(ex)))
            skipped_count += 1
            continue # Cannot proceed without a view

        # 2. Apply View Template
        try:
            print("# Applying template '{{}}' to view '{{}}'...".format(view_template_name, new_view.Name))
            # NOTE: Transaction handled by C# wrapper
            new_view.ViewTemplateId = view_template.Id
            doc.Regenerate() # Apply template changes
            print("# Successfully applied template.")
        except System.Exception as ex:
            print("# Error applying template to view '{{}}': {{}}".format(new_view.Name, str(ex)))
            # Decide whether to continue without template or skip
            print("# Warning: Proceeding without template applied.")
            # If template is critical, uncomment below and handle cleanup if needed
            # skipped_count += 1
            # # Try deleting the created view if template application fails
            # try:
            #     doc.Delete(new_view.Id)
            #     created_view_ids.remove(new_view.Id)
            #     print("# Deleted view '{{}}' due to template error.".format(new_view.Name))
            # except Exception as del_ex:
            #      print("# Warning: Failed to delete view '{{}}': {{}}".format(new_view.Name, del_ex))
            # continue

        # 3. Create Sheet
        sheet_number = level_name # Use level name as sheet number
        sheet_name = level_name + sheet_name_suffix

        # Check for existing sheet with the same number BEFORE attempting creation
        existing_sheet = None
        sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
        for s in sheet_collector:
            # Compare sheet numbers case-insensitively? Assume case-sensitive for now.
            if s.SheetNumber == sheet_number:
                existing_sheet = s
                break

        if existing_sheet:
             print("# Info: Sheet with number '{{}}' already exists (Name: '{{}}'). Skipping sheet creation and view placement for this level.".format(sheet_number, existing_sheet.Name))
             skipped_count += 1
             # Delete the view created for this level as it won't be placed on a new sheet
             try:
                 if new_view.Id in created_view_ids: # Only delete if it was created in this run
                     doc.Delete(new_view.Id)
                     created_view_ids.remove(new_view.Id)
                     print("# Deleted unplaced view '{{}}' as sheet already exists.".format(new_view.Name))
             except System.Exception as del_ex:
                 print("# Warning: Failed to delete unplaced view '{{}}': {{}}".format(new_view.Name, str(del_ex)))
             continue # Skip to next level

        # Attempt to create the sheet
        try:
            print("# Creating sheet with Number: '{{}}', Name: '{{}}'...".format(sheet_number, sheet_name))
            # NOTE: Transaction handled by C# wrapper
            new_sheet = ViewSheet.Create(doc, title_block_type.Id)
            # Set Number and Name AFTER creation, handle potential errors
            try:
                new_sheet.SheetNumber = sheet_number
                new_sheet.Name = sheet_name
                doc.Regenerate() # Update sheet properties
                print("# Successfully created sheet '{{}}' - '{{}}' (ID: {{}})".format(new_sheet.SheetNumber, new_sheet.Name, new_sheet.Id.IntegerValue))
                created_sheet_ids.append(new_sheet.Id) # Track created sheet
            except System.Exception as name_ex:
                 print("# Error setting name/number for sheet (ID: {{}}): {{}}".format(new_sheet.Id.IntegerValue, str(name_ex)))
                 print("# Sheet created but naming failed. Attempting to delete sheet and view.")
                 # Clean up sheet and view
                 try:
                      doc.Delete(new_sheet.Id)
                      print("# Deleted sheet {{}} after naming error.".format(new_sheet.Id.IntegerValue))
                 except System.Exception as del_sheet_ex:
                      print("# Warning: Failed to delete sheet {{}} after naming error: {{}}".format(new_sheet.Id.IntegerValue, del_sheet_ex))
                 try:
                     if new_view.Id in created_view_ids:
                         doc.Delete(new_view.Id)
                         created_view_ids.remove(new_view.Id)
                         print("# Deleted view {{}} after sheet naming error.".format(new_view.Id.IntegerValue))
                 except System.Exception as del_view_ex:
                      print("# Warning: Failed to delete view {{}} after sheet naming error: {{}}".format(new_view.Id.IntegerValue, del_view_ex))
                 skipped_count += 1
                 continue

        except System.Exception as create_ex:
            print("# Error creating sheet for level '{{}}': {{}}".format(level_name, str(create_ex)))
            # Check if the error was due to duplicate number that wasn't caught by the pre-check
            sheet_collector_retry = FilteredElementCollector(doc).OfClass(ViewSheet)
            found_after_fail = False
            for s_retry in sheet_collector_retry:
                 if s_retry.SheetNumber == sheet_number:
                     print("# Info: Sheet '{{}}' likely already existed (duplicate number error).".format(sheet_number))
                     found_after_fail = True
                     break
            if not found_after_fail:
                 print("# Sheet creation failed for reason other than duplicate number.")

            # Clean up the created view since we can't place it
            try:
                 if new_view.Id in created_view_ids:
                     doc.Delete(new_view.Id) # <--- CORRECTED THIS LINE
                     created_view_ids.remove(new_view.Id)
                     print("# Deleted view '{{}}' due to sheet creation error.".format(new_view.Name))
            except System.Exception as del_ex:
                 print("# Warning: Failed to delete view '{{}}' after sheet creation error: {{}}".format(new_view.Name, str(del_ex)))
            skipped_count += 1
            continue # Skip to next level

        # 4. Place View on Sheet (Centered)
        if new_sheet and new_view: # Proceed only if both were created successfully
            try:
                print("# Placing view '{{}}' on sheet '{{}}'...".format(new_view.Name, new_sheet.SheetNumber))
                placement_point = get_sheet_center(new_sheet, doc)
                print("# Calculated placement point: ({}, {})".format(placement_point.X, placement_point.Y))

                # Check if view can be placed
                if Viewport.CanAddViewToSheet(doc, new_sheet.Id, new_view.Id):
                     # NOTE: Transaction handled by C# wrapper
                     viewport = Viewport.Create(doc, new_sheet.Id, new_view.Id, placement_point)
                     doc.Regenerate() # Ensure viewport is fully created
                     # Verify placement status
                     if viewport.SheetId == new_sheet.Id: # Basic check
                         print("# Successfully placed view (Viewport ID: {{}})".format(viewport.Id.IntegerValue))
                         processed_count += 1
                     else:
                         # This case might be rare if CanAddViewToSheet passed, but good to handle
                         print("# Error: Viewport.Create reported success, but verification failed. View might not be on sheet.")
                         skipped_count += 1
                         # Attempt to clean up the sheet and view? Or leave them? Leaving for now.
                else:
                    print("# Error: Cannot place view '{{}}' (ID: {{}}) on sheet '{{}}'. View might already be on a sheet or unsuitable.".format(new_view.Name, new_view.Id.IntegerValue, new_sheet.SheetNumber))
                    # Clean up the created sheet and view as placement failed
                    try:
                        if new_sheet.Id in created_sheet_ids:
                            doc.Delete(new_sheet.Id)
                            created_sheet_ids.remove(new_sheet.Id)
                            print("# Deleted sheet '{{}}' because view placement failed.".format(new_sheet.SheetNumber))
                        if new_view.Id in created_view_ids:
                             doc.Delete(new_view.Id)
                             created_view_ids.remove(new_view.Id)
                             print("# Deleted view '{{}}' because placement failed.".format(new_view.Name))
                    except System.Exception as cleanup_ex:
                         print("# Warning: Error during cleanup after failed view placement: {{}}".format(str(cleanup_ex)))
                    skipped_count += 1

            except System.Exception as place_ex:
                print("# Error placing view '{{}}' on sheet '{{}}': {{}}".format(new_view.Name, new_sheet.SheetNumber, str(place_ex)))
                # Attempt to clean up sheet and view after placement error
                try:
                    if new_sheet.Id in created_sheet_ids:
                        doc.Delete(new_sheet.Id)
                        created_sheet_ids.remove(new_sheet.Id)
                        print("# Deleted sheet '{{}}' due to placement error.".format(new_sheet.SheetNumber))
                    if new_view.Id in created_view_ids:
                         doc.Delete(new_view.Id)
                         created_view_ids.remove(new_view.Id)
                         print("# Deleted view '{{}}' due to placement error.".format(new_view.Name))
                except System.Exception as cleanup_ex:
                     print("# Warning: Error during cleanup after placement error: {{}}".format(str(cleanup_ex)))
                skipped_count += 1

    print("\n# --- Script Finished ---")
    print("# Processed (Sheet+View Created & Placed): {{}}".format(processed_count))
    print("# Skipped (Level Not Found or Errors): {{}}".format(skipped_count))
    print("# Total Levels in Request: {{}}".format(len(level_names)))
    print("# Views created in this run (IDs): {{}}".format([vid.IntegerValue for vid in created_view_ids]))
    print("# Sheets created in this run (IDs): {{}}".format([sid.IntegerValue for sid in created_sheet_ids]))