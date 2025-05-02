# Purpose: This script renumbers Revit sheets sequentially, handling conflicts and providing a summary.

# Purpose: This script renumbers Revit sheets sequentially, handling potential conflicts and providing a summary report.

﻿# Import necessary classes
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, ElementId
import System # For Exception handling

# --- Configuration ---
start_prefix = "A"
start_number = 101
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
            print("# Error sorting sheets by current number: {}. Proceeding with unsorted order.".format(sort_err))
            sorted_sheets = all_sheets_elements # Fallback to original collected order
    else:
        # Use the order returned by the collector (often creation order, but not guaranteed)
        sorted_sheets = all_sheets_elements
        # print("# Proceeding with collector order ({} sheets).".format(len(sorted_sheets))) # Debug


    # --- Step 3: Renumber sheets sequentially ---
    current_number = start_number
    sheets_renumbered_count = 0
    sheets_failed_count = 0
    errors = []
    processed_sheet_ids = set() # To track which sheets have been processed

    # First pass: Apply new numbers, skipping potential conflicts for later
    temp_rename_failures = [] # Store sheets that failed initially

    for sheet in sorted_sheets:
        if sheet.Id in processed_sheet_ids: # Should not happen with list, but safety check
            continue

        new_sheet_number = "{}{}".format(start_prefix, current_number)
        try:
            # Check if the new number is the same as the old one
            if sheet.SheetNumber != new_sheet_number:
                 # Attempt to set the new sheet number
                 sheet.SheetNumber = new_sheet_number
                 # print("# Successfully renamed sheet ID {} ('{}') to {}".format(sheet.Id, old_number, new_sheet_number)) # Debug
                 sheets_renumbered_count += 1
            # else: # No change needed
                 # print("# Sheet ID {} already has number {}".format(sheet.Id, new_sheet_number)) # Debug
                 # No count increment needed if no change occurred

            # Increment number for the next sheet in the sorted list
            current_number += 1
            processed_sheet_ids.add(sheet.Id)

        except System.ArgumentException as arg_ex:
            # This likely means the target number is already in use by another sheet
            # that hasn't been renamed yet. Store it for a potential second pass.
            error_detail = "ArgumentException: {}".format(arg_ex.Message)
            temp_rename_failures.append((sheet, new_sheet_number, error_detail))
            # Do not increment number yet, maybe the next sheet works, or maybe we retry this one
            # Let's still increment the target number for the *next* sheet in the list
            current_number += 1
            processed_sheet_ids.add(sheet.Id) # Mark as processed even if failed initially

        except Exception as e:
            # Catch other potential errors during renaming
            error_msg = "# Unexpected error renaming sheet ID {} ('{}') to '{}': {}. Skipping.".format(
                sheet.Id, sheet.SheetNumber, new_sheet_number, e)
            print(error_msg)
            errors.append(error_msg)
            sheets_failed_count += 1
            # Increment number for the next sheet
            current_number += 1
            processed_sheet_ids.add(sheet.Id)

    # Second pass: Retry sheets that failed due to potential conflicts
    if temp_rename_failures:
        # print("# Retrying {} sheets that failed initial rename attempt.".format(len(temp_rename_failures))) # Debug
        for sheet, target_number, initial_error in temp_rename_failures:
            try:
                # Check if it somehow got the right number already (unlikely but possible)
                if sheet.SheetNumber != target_number:
                    sheet.SheetNumber = target_number
                    # print("# Successfully renamed sheet ID {} on retry to {}".format(sheet.Id, target_number)) # Debug
                    sheets_renumbered_count += 1 # Count success on retry
                # else: # Already has the target number now
                #     pass
            except Exception as e:
                 error_msg = "# Error on retry renaming sheet ID {} ('{}') to '{}': {} (Initial error: {}). Skipping.".format(
                     sheet.Id, sheet.SheetNumber, target_number, e, initial_error)
                 print(error_msg)
                 errors.append(error_msg)
                 sheets_failed_count += 1


    # --- Final Summary ---
    total_processed = sheets_renumbered_count + sheets_failed_count # Includes sheets attempted
    # print("# Renumbering process attempted on {} sheets.".format(len(sorted_sheets))) # Debug
    # print("# Sheets successfully assigned a new number: {}".format(sheets_renumbered_count)) # Optional
    # print("# Sheets failed final assignment: {}".format(sheets_failed_count)) # Optional

    if sheets_failed_count > 0:
        print("# Renumbering finished with {} errors.".format(sheets_failed_count))
        # for err in errors: # Print detailed errors if needed
        #    print(err)
    elif sheets_renumbered_count > 0:
        print("# Renumbering completed. {} sheets had their numbers changed.".format(sheets_renumbered_count))
    elif not temp_rename_failures: # No errors and no renumbering needed
        print("# All sheets already conform to the specified numbering sequence or no changes were needed.")
    else: # Should be covered by failed_count > 0
        print("# Renumbering process completed, but some errors may have occurred initially.")