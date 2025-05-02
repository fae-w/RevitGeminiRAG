# Purpose: This script creates a new Revit sheet with an automatically incremented number and a specified name.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    BuiltInCategory,
    ElementId,
    ParameterFilterUtilities
)
import System # Required for exception handling

# --- Configuration ---
target_sheet_name = 'Parking Level Plan'
sheet_number_prefix = 'P-'
number_padding = 3 # Number of digits for padding (e.g., 3 for P-001)

# --- Helper Function ---
def get_next_sheet_number(prefix, padding):
    """
    Finds the next available sheet number with a given prefix and padding.
    e.g., prefix 'P-', padding 3 -> finds highest P-XXX and returns P-YYY where YYY = XXX + 1
    """
    max_num = 0
    found_prefix_sheets = False
    collector = FilteredElementCollector(doc).OfClass(ViewSheet)
    for sheet in collector:
        try:
            num_str = sheet.SheetNumber
            if num_str and num_str.startswith(prefix):
                found_prefix_sheets = True
                num_part = num_str[len(prefix):]
                if num_part.isdigit():
                    current_num = int(num_part)
                    if current_num > max_num:
                        max_num = current_num
        except Exception:
            # Ignore sheets with invalid or inaccessible numbers
            pass

    next_num = max_num + 1
    # Format the number with leading zeros
    return "{}{:0{}}".format(prefix, next_num, padding) # Escaped format specifier

# --- Main Logic ---
try:
    # 1. Find a Title Block Type
    title_block_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
    first_title_block_type = title_block_collector.FirstElement()

    if not first_title_block_type:
        print("# Error: No Title Block types found in the project. Cannot create sheet.")
    else:
        title_block_type_id = first_title_block_type.Id
        # print(f"# Using Title Block Type: {first_title_block_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()}") # Escaped

        # 2. Determine the next available sheet number
        next_sheet_number = get_next_sheet_number(sheet_number_prefix, number_padding)
        # print(f"# Determined next available sheet number: {next_sheet_number}") # Escaped

        # 3. Create the new Sheet
        new_sheet = None
        try:
            new_sheet = ViewSheet.Create(doc, title_block_type_id)
            if new_sheet:
                # print(f"# Successfully created new sheet (ID: {new_sheet.Id})") # Escaped
                pass # Success
            else:
                print("# Error: ViewSheet.Create returned None.")
                # Stop execution if sheet creation failed
                new_sheet = None # Ensure it remains None

        except Exception as create_ex:
            print("# Error creating sheet: {}".format(create_ex))
            new_sheet = None # Ensure it remains None

        # 4. Assign Name and Number if sheet was created
        if new_sheet:
            sheet_updated = False
            error_messages = []
            # Set Sheet Number
            try:
                if new_sheet.SheetNumber != next_sheet_number:
                    new_sheet.SheetNumber = next_sheet_number
                    sheet_updated = True
                    # print(f"# Set Sheet Number to: '{next_sheet_number}'") # Escaped
                else:
                     # This case should not happen for a new sheet, but check anyway
                     # print(f"# Sheet Number is already '{next_sheet_number}'.") # Escaped
                     pass
            except System.ArgumentException as ex:
                error_messages.append("# Error setting Sheet Number: {}. The number '{}' might be invalid or already in use (check concurrent runs).".format(ex.Message, next_sheet_number))
            except Exception as ex:
                error_messages.append("# An unexpected error occurred while setting Sheet Number: {}".format(ex))

            # Set Sheet Name
            try:
                if new_sheet.Name != target_sheet_name:
                    # Use the Name property directly
                    new_sheet.Name = target_sheet_name
                    sheet_updated = True
                    # print(f"# Set Sheet Name to: '{target_sheet_name}'") # Escaped
                else:
                    # print(f"# Sheet Name is already '{target_sheet_name}'.") # Escaped
                    pass
            except System.ArgumentException as ex:
                 error_messages.append("# Error setting Sheet Name: {}. The name '{}' might be invalid.".format(ex.Message, target_sheet_name))
            except Exception as ex:
                 error_messages.append("# An unexpected error occurred while setting Sheet Name: {}".format(ex))

            # Report final status
            if not error_messages:
                if sheet_updated:
                    print("# Successfully created and configured new sheet: '{}' - '{}'".format(next_sheet_number, target_sheet_name))
                else:
                    print("# New sheet created, but properties already matched target values (unexpected).")
            else:
                print("# Sheet created, but encountered errors during configuration:")
                for msg in error_messages:
                    print(msg)

except Exception as e:
    print("# An overall error occurred: {}".format(e))