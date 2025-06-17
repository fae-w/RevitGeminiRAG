# Purpose: This script renames Revit sheets by prepending a new prefix to sheets with a specific old prefix.

﻿# Import necessary classes
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, ElementId
import System # For Exception handling

# --- Configuration ---
old_prefix = "A1"
new_prefix = "ARCH_" # The string to prepend to the existing sheet number

# --- Initialization ---
sheets_to_process = []
processed_count = 0
renamed_count = 0
failed_count = 0
errors = []

# --- Step 1: Collect all ViewSheets ---
collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure elements are valid ViewSheets before adding to list
all_sheets_elements = [sheet for sheet in collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

# --- Step 2: Identify sheets to rename and determine new names ---
for sheet in all_sheets_elements:
    processed_count += 1
    original_sheet_number = None
    try:
        original_sheet_number = sheet.SheetNumber
    except Exception as e:
        # Handle potential issue accessing the property, though unlikely for SheetNumber
        print("# Warning: Could not retrieve SheetNumber for sheet ID {}. Skipping. Error: {}".format(sheet.Id, e))
        continue

    if original_sheet_number is not None and original_sheet_number.startswith(old_prefix):
        # Construct the new sheet number by prepending the new prefix to the original number
        new_sheet_number = new_prefix + original_sheet_number

        # Store the sheet, old number, and proposed new number for processing
        sheets_to_process.append({
            "sheet": sheet,
            "old_number": original_sheet_number,
            "new_number": new_sheet_number
        })

# --- Step 3: Attempt renaming ---
if not sheets_to_process:
    print("# No sheets found with the prefix '{}'.".format(old_prefix))
else:
    print("# Found {} sheets starting with '{}'. Attempting to rename...".format(len(sheets_to_process), old_prefix))

    for item in sheets_to_process:
        sheet = item["sheet"]
        old_num = item["old_number"]
        new_num = item["new_number"]

        # Double-check: Skip if old and new numbers are somehow the same
        if old_num == new_num:
            # This shouldn't happen with the current logic but is a safe check
            continue

        try:
            # Attempt to set the new sheet number
            sheet.SheetNumber = new_num
            renamed_count += 1
            # print("# Successfully renamed sheet '{}' to '{}' (ID: {})".format(old_num, new_num, sheet.Id)) # Optional debug line
        except System.ArgumentException as arg_ex:
            # Handle cases like duplicate sheet numbers or invalid characters
            failed_count += 1
            error_msg = "# Error renaming sheet '{}' (ID: {}) to '{}': {}. Target number might already exist or contain invalid characters.".format(old_num, sheet.Id, new_num, arg_ex.Message)
            errors.append(error_msg)
            print(error_msg) # Print error immediately for visibility
        except Exception as e:
            # Handle other potential errors during renaming
            failed_count += 1
            error_msg = "# Unexpected error renaming sheet '{}' (ID: {}) to '{}': {}".format(old_num, sheet.Id, new_num, e)
            errors.append(error_msg)
            print(error_msg) # Print error immediately

    # --- Final Summary ---
    print("# --- Renaming Summary ---")
    print("# Total sheets checked: {}".format(processed_count))
    print("# Sheets matching prefix '{}': {}".format(old_prefix, len(sheets_to_process)))
    print("# Sheets successfully renamed: {}".format(renamed_count))
    print("# Sheets failed to rename: {}".format(failed_count))

    # Errors were already printed when they occurred.
    # if failed_count > 0:
    #     print("# Review errors above for details on failures.")