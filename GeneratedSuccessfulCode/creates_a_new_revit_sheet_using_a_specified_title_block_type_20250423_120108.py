# Purpose: This script creates a new Revit sheet using a specified title block type.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, BuiltInCategory, ViewSheet, ElementId
import System # For Exception handling

# --- Configuration ---
target_title_block_name = "A1 Metric Titleblock" # The exact name of the title block type to use

# --- Step 1: Find the specified Title Block Type ID ---
title_block_type_id = ElementId.InvalidElementId
collector_types = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()

found_title_block = None
for tb_type in collector_types:
    if tb_type.Name == target_title_block_name:
        found_title_block = tb_type
        break

if found_title_block:
    title_block_type_id = found_title_block.Id
    # print("# Using title block type: '{}' (ID: {})".format(found_title_block.Name, title_block_type_id)) # Debug
else:
    print("# Error: Title Block type named '{}' not found in the project. Cannot create sheet.".format(target_title_block_name))
    # Stop script execution if the specific title block is not found
    title_block_type_id = None

# --- Step 2: Create the new sheet ---
if title_block_type_id and title_block_type_id != ElementId.InvalidElementId:
    new_sheet = None
    try:
        new_sheet = ViewSheet.Create(doc, title_block_type_id)
        if new_sheet:
            # Optional: Assign a default name/number if needed, otherwise Revit assigns defaults
            # Revit usually assigns the next available number and a default name like "Unnamed"
            # new_sheet.Name = "Default New Sheet Name"
            # new_sheet.SheetNumber = "S-XXX" # Requires logic to determine next available number
            # print("# Successfully created new sheet with ID: {}".format(new_sheet.Id)) # Debug
            pass # Sheet created successfully
        else:
            print("# Error: ViewSheet.Create returned None even with a valid title block ID.")
    except System.ArgumentException as arg_ex:
        # This might catch issues if the title block ID is somehow invalid despite the check
         print("# Error creating sheet: {}. The title block ID might be invalid.".format(arg_ex.Message))
    except Exception as create_ex:
        print("# Error creating sheet: {}".format(create_ex))

# No specific output or data export is required for this task.
# The sheet creation happens within the C# wrapper's transaction.