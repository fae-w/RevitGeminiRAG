# Purpose: This script renumbers Revit sheets sequentially based on a defined prefix and starting number.

﻿# Import necessary classes
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, ElementId
import System # For Exception handling

# --- Configuration ---
start_prefix = "A-"
start_number = 1
number_padding = 3 # How many digits the number should have (e.g., 3 for 001, 002)
# Flag to indicate if sorting sheets by their current number should be attempted
sort_by_current_number = True

# --- Step 1: Collect all ViewSheets ---
collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure elements are valid ViewSheets before adding to list
all_sheets_elements = []
for sheet in collector:
    if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet):
        all_sheets_elements.append(sheet)

if not all_sheets_elements:
    print("# No ViewSheet elements found in the project.")
else:
    # --- Step 2: Sort sheets ---
    sorted_sheets = []
    if sort_by_current_number:
        # Assumption: Sorting alphabetically/numerically by the current SheetNumber
        # approximates the desired Project Browser order. This might not be accurate
        # if custom browser organization parameters are used or if sorting is complex.
        try:
            # Standard string sort is used here. For complex cases like 'A10' vs 'A2' or mixed formats,
            # a more sophisticated natural sort key might be needed.
            sorted_sheets = sorted(all_sheets_elements, key=lambda sheet: sheet.SheetNumber)
            # print("# Sorted {} sheets by current sheet number.".format(len(sorted_sheets))) # Debug
        except Exception as sort_err:
            print("# Error sorting sheets by current number: {}. Proceeding with collector order.".format(sort_err))
            sorted_sheets = all_sheets_elements # Fallback to original collected order
    else:
        # Use the order returned by the collector (often creation order, but not guaranteed)
        sorted_sheets = all_sheets_elements
        # print("# Proceeding with collector order ({} sheets).".format(len(sorted_sheets))) # Debug


    # --- Step 3: Renumber sheets sequentially (Two-Pass Approach) ---
    sheets_renumbered_count = 0 # Counts sheets where number was successfully *changed*
    sheets_failed_count = 0     # Counts sheets that failed final assignment
    errors = []                 # Stores error messages for failed sheets
    temp_rename_failures = []   # Stores (sheet, target_number, error_detail) for retry

    # First pass: Apply new numbers, store potential conflicts for later
    for index, sheet in enumerate(sorted_sheets):
        target_number_int = start_number + index
        # Format the new sheet number (e.g., "A-001")
        # Creates a format string like "{}{:0>3d}" for padding=3
        format_string = "{}{{:{:0>" + str(number_padding) + "}d}}"
        new_sheet_number = format_string.format(start_prefix, target_number_int)

        try:
            # Check if the new number is the same as the old one
            if sheet.SheetNumber != new_sheet_number:
                 # Attempt to set the new sheet number
                 old_number = sheet.SheetNumber # Store old number for logging if needed
                 sheet.SheetNumber = new_sheet_number
                 # print("# Successfully renamed sheet ID {} ('{}') to {}".format(sheet.Id, old_number, new_sheet_number)) # Debug
                 sheets_renumbered_count += 1
            # else: # No change needed
                 # print("# Sheet ID {} already has number {}".format(sheet.Id, new_sheet_number)) # Debug
                 # No count increment needed if no change occurred

        except System.ArgumentException as arg_ex:
            # This likely means the target number is already in use by another sheet
            # that hasn't been renamed yet. Store it for a potential second pass.
            error_detail = "ArgumentException: {}".format(arg_ex.Message)
            temp_rename_failures.append((sheet, new_sheet_number, error_detail))
            # Don't count as failure yet, will retry

        except Exception as e:
            # Catch other potential errors during renaming
            error_msg = "# Error renaming sheet ID {} ('{}') to '{}': {}. Skipping.".format(
                sheet.Id, sheet.SheetNumber, new_sheet_number, e)
            print(error_msg)
            errors.append(error_msg)
            sheets_failed_count += 1 # Count as failure immediately for non-ArgumentException errors


    # Second pass: Retry sheets that failed due to potential conflicts
    if temp_rename_failures:
        # print("# Retrying {} sheets that failed initial rename attempt.".format(len(temp_rename_failures))) # Debug
        for sheet, target_number, initial_error in temp_rename_failures:
            try:
                # Check if it somehow got the right number already or still needs changing
                if sheet.SheetNumber != target_number:
                    sheet.SheetNumber = target_number
                    # print("# Successfully renamed sheet ID {} on retry to {}".format(sheet.Id, target_number)) # Debug
                    sheets_renumbered_count += 1 # Count success *change* on retry
                # else: # Already has the target number now
                    # pass
            except Exception as e:
                 # Failed again on retry
                 error_msg = "# Error on retry renaming sheet ID {} ('{}') to '{}': {} (Initial error: {}). Skipping.".format(
                     sheet.Id, sheet.SheetNumber, target_number, e, initial_error)
                 print(error_msg)
                 errors.append(error_msg)
                 sheets_failed_count += 1 # Count as failure now


    # --- Final Summary ---
    total_processed = len(sorted_sheets)
    print("# Renumbering process attempted on {} sheets.".format(total_processed))
    # A sheet is successful if it wasn't counted as a final failure
    print("# Sheets successfully assigned a new number (or kept existing if already correct): {}".format(total_processed - sheets_failed_count))
    # This count specifically tracks how many sheets actually had their number property changed
    print("# Sheets where the number was actually changed: {}".format(sheets_renumbered_count))
    print("# Sheets that failed final assignment: {}".format(sheets_failed_count))

    if sheets_failed_count > 0:
        print("# Some sheets could not be renumbered due to persistent conflicts or errors.")
        # for err in errors: # Uncomment to print detailed errors
        #    print(err)
    elif sheets_renumbered_count > 0:
         print("# Renumbering completed successfully.")
    else: # No failures and no actual changes made
         print("# All sheets found already conform to the specified numbering sequence.")