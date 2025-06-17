# Purpose: This script renames empty Revit sheets by adding a suffix to their names.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, ElementId, View
import System # For Exception handling

# --- Configuration ---
suffix_to_add = " [EMPTY]" # Note the leading space

# --- Initialization ---
processed_count = 0
renamed_count = 0
already_named_count = 0
skipped_not_empty_count = 0
failed_rename_count = 0
errors = []

# --- Step 1: Collect all ViewSheets ---
collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure elements are valid ViewSheets before processing
all_sheets = [sheet for sheet in collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

if not all_sheets:
    print("# No ViewSheet elements found in the project.")
else:
    print("# Found {} sheets. Processing to identify and rename empty ones...".format(len(all_sheets)))

    # --- Step 2: Iterate through sheets and check for placed views ---
    for sheet in all_sheets:
        processed_count += 1
        current_name = None
        sheet_id_str = "Unknown ID" # Placeholder

        try:
            sheet_id_str = sheet.Id.ToString() # Get ID for logging

            # --- Get placed views (excluding schedules as per GetAllPlacedViews documentation) ---
            placed_view_ids = sheet.GetAllPlacedViews() # Returns ISet<ElementId>

            # Check if the sheet contains any views returned by this method
            if placed_view_ids is not None and placed_view_ids.Count > 0:
                skipped_not_empty_count += 1
                continue # Skip this sheet, it's not empty

            # --- Sheet is considered empty (no views returned by GetAllPlacedViews) ---
            try:
                current_name = sheet.Name
            except Exception as name_ex:
                failed_rename_count += 1
                errors.append("# Error getting name for Sheet ID {}: {}".format(sheet_id_str, name_ex))
                continue # Skip if we can't get the name

            # Check if the name already ends with the suffix
            if current_name.endswith(suffix_to_add):
                already_named_count += 1
                continue # Skip, already has the suffix

            # Construct the new name
            new_name = current_name + suffix_to_add

            # --- Attempt to rename the sheet (Name property) ---
            try:
                # THE ACTUAL RENAMING ACTION
                sheet.Name = new_name
                renamed_count += 1
                # print("# Renamed Sheet '{}' (ID: {}) to '{}'".format(current_name, sheet_id_str, new_name)) # Optional verbose log
            except System.ArgumentException as arg_ex:
                # Specific handling for common errors like invalid characters or potential duplicates (less likely for names)
                failed_rename_count += 1
                error_msg = "# Rename Error (Name): Sheet '{}' (ID: {}) to '{}': {}".format(current_name, sheet_id_str, new_name, arg_ex.Message)
                errors.append(error_msg)
                print(error_msg) # Print rename errors immediately
            except Exception as rename_ex:
                # Catch other potential API errors during renaming
                failed_rename_count += 1
                error_msg = "# Rename Error (Name): Sheet '{}' (ID: {}) to '{}': {}".format(current_name, sheet_id_str, new_name, rename_ex)
                errors.append(error_msg)
                print(error_msg) # Print rename errors immediately

        except Exception as outer_ex:
            # Catch unexpected errors during the processing loop for a sheet
            failed_rename_count += 1 # Count as failure if error prevents potential rename
            error_msg = "# Unexpected Error processing sheet ID {}: {}".format(sheet_id_str, outer_ex)
            if current_name: # Add name if already retrieved
                 error_msg = "# Unexpected Error processing sheet '{}' (ID: {}): {}".format(current_name, sheet_id_str, outer_ex)
            errors.append(error_msg)
            print(error_msg) # Print outer loop errors immediately

    # --- Final Summary ---
    print("\n# --- Sheet Renaming Summary ---")
    print("# Total sheets checked: {}".format(processed_count))
    print("# Sheets successfully renamed (added '{}'): {}".format(suffix_to_add, renamed_count))
    print("# Sheets skipped (already had the suffix): {}".format(already_named_count))
    print("# Sheets skipped (were not empty): {}".format(skipped_not_empty_count))
    print("# Sheets failed during processing/rename: {}".format(failed_rename_count))

    # # Optional: Print detailed errors if any occurred
    # if errors:
    #     print("\n# --- Encountered Errors ---")
    #     for error in errors:
    #         print(error)