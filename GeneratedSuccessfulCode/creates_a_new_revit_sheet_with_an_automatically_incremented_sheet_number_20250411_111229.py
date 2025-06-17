# Purpose: This script creates a new Revit sheet with an automatically incremented sheet number.

# Purpose: This script creates a new Revit sheet with an automatically incremented sheet number and a predefined name, using the first available title block type found in the project.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilySymbol,
    BuiltInCategory,
    ViewSheet,
    ElementId
)
import System # For Exception handling

# --- Configuration ---
sheet_name = "Enlarged Plan Details"
sheet_number_prefix = "A2"
sheet_number_digits = 2 # Corresponds to "xx" in A2xx (e.g., A200, A201 ... A299)

# --- Step 1: Find the first available Title Block Type ID ---
title_block_type_id = ElementId.InvalidElementId
collector_types = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
first_title_block_type = collector_types.FirstElement()

if first_title_block_type:
    title_block_type_id = first_title_block_type.Id
    # print("# Using title block type: {} (ID: {})".format(first_title_block_type.Name, title_block_type_id)) # Debug
else:
    print("# Error: No Title Block types found in the project. Cannot create sheet.")
    # Stop script execution if no title block is found
    title_block_type_id = None

if title_block_type_id and title_block_type_id != ElementId.InvalidElementId:
    # --- Step 2: Determine the next available sheet number in the sequence ---
    existing_suffixes = set()
    collector_sheets = FilteredElementCollector(doc).OfClass(ViewSheet)

    max_suffix = -1
    expected_length = len(sheet_number_prefix) + sheet_number_digits

    for sheet in collector_sheets:
        if isinstance(sheet, ViewSheet):
            sheet_num_str = sheet.SheetNumber
            # Check prefix, length, and if the suffix is numeric
            if sheet_num_str.startswith(sheet_number_prefix) and len(sheet_num_str) == expected_length:
                suffix_str = sheet_num_str[len(sheet_number_prefix):]
                if suffix_str.isdigit():
                    try:
                        suffix = int(suffix_str)
                        existing_suffixes.add(suffix)
                        if suffix > max_suffix:
                            max_suffix = suffix
                    except ValueError:
                        # print("# Warning: Could not parse suffix of sheet number '{}'. Skipping.".format(sheet_num_str)) # Debug
                        pass # Should be caught by isdigit, but for safety

    next_suffix = -1
    start_suffix = 0 # Typically start from 00
    max_possible_suffix = (10**sheet_number_digits) - 1 # e.g., 99 for 2 digits

    if max_suffix == -1:
        # No existing sheets in the sequence found, start with the first number (e.g., 00)
        if start_suffix not in existing_suffixes: # Check if 00 is somehow already taken by a sheet not matching the exact pattern
             next_suffix = start_suffix
        else:
             current_check = start_suffix + 1
             while current_check <= max_possible_suffix and current_check in existing_suffixes:
                 current_check += 1
             next_suffix = current_check

    else:
        # Start checking from the number after the max found
        current_check = max_suffix + 1
        while current_check <= max_possible_suffix and current_check in existing_suffixes:
            current_check += 1
        next_suffix = current_check

    next_sheet_num_str = None
    if next_suffix > max_possible_suffix:
        print("# Error: Cannot find an available sheet number in the {}{} range ({} to {}). All are taken.".format(
              sheet_number_prefix, 'x'*sheet_number_digits, start_suffix, max_possible_suffix))
    else:
        # Format the next sheet number string (e.g., "A205")
        format_string = "{}{:0" + str(sheet_number_digits) + "d}" # e.g., "{}{:02d}"
        next_sheet_num_str = format_string.format(sheet_number_prefix, next_suffix)

    # --- Step 3: Create the new sheet and set properties ---
    if next_sheet_num_str:
        new_sheet = None
        try:
            new_sheet = ViewSheet.Create(doc, title_block_type_id)
            if new_sheet:
                try:
                    # Set Number first, as it's more likely to fail if already taken
                    new_sheet.SheetNumber = next_sheet_num_str
                    new_sheet.Name = sheet_name
                    # print("# Successfully created sheet '{}' - '{}'".format(new_sheet.SheetNumber, new_sheet.Name)) # Debug
                except System.ArgumentException as arg_ex:
                    # This catches if the sheet number is already in use or contains invalid characters.
                    print("# Error setting sheet number/name: {}. The number '{}' might be invalid or already taken.".format(arg_ex.Message, next_sheet_num_str))
                    # The C# wrapper's transaction should handle rollback.
                except Exception as e:
                    print("# Error setting sheet properties: {}".format(e))
                    # The C# wrapper's transaction should handle rollback.
            else:
                print("# Error: ViewSheet.Create returned None.")
        except Exception as create_ex:
            print("# Error creating sheet: {}".format(create_ex))