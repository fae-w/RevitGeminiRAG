# Purpose: This script automatically sets the 'Approved By' parameter on Revit sheets based on the 'Checked By' parameter.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling and String
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, Parameter, StorageType, Element
import System # For Exception and String
from System import String # Explicit import for String utilities

# --- Configuration ---
checked_by_param_name = "Checked By"
approved_by_param_name = "Approved By"
approved_by_value_to_set = "Project Manager"

# --- Initialization ---
processed_count = 0
updated_count = 0
skipped_checked_missing_or_empty_count = 0
skipped_approved_missing_count = 0
skipped_approved_readonly_count = 0
failed_update_count = 0
errors = [] # Stores errors for summary reporting

# --- Step 1: Collect all ViewSheets ---
collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure elements are valid ViewSheets before processing
all_sheets = [sheet for sheet in collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

if not all_sheets:
    print("# No ViewSheet elements found in the project.")
else:
    print("# Found {{}} sheets. Processing parameters '{{}}' and '{{}}'...".format(len(all_sheets), checked_by_param_name, approved_by_param_name))

    # --- Step 2: Iterate and attempt update ---
    for sheet in all_sheets:
        processed_count += 1
        sheet_identifier = "Unknown Sheet" # Placeholder
        try:
            sheet_identifier = "'{}' (ID: {})".format(sheet.SheetNumber, sheet.Id)

            # --- Get the parameters ---
            checked_by_param = sheet.LookupParameter(checked_by_param_name)
            approved_by_param = sheet.LookupParameter(approved_by_param_name)

            # --- Check the 'Checked By' parameter ---
            checked_by_is_valid = False
            if checked_by_param is not None and checked_by_param.HasValue:
                # Further check if the value is not null or whitespace
                checked_by_value_str = None
                try:
                    if checked_by_param.StorageType == StorageType.String:
                         checked_by_value_str = checked_by_param.AsString()
                    else:
                         # Try AsValueString for non-string types, might include units
                         checked_by_value_str = checked_by_param.AsValueString()
                except Exception:
                     # Fallback if AsValueString fails
                     try:
                         checked_by_value_str = checked_by_param.AsString()
                     except Exception:
                         pass # Could not get string value

                if not String.IsNullOrWhiteSpace(checked_by_value_str):
                    checked_by_is_valid = True

            # --- Apply logic based on 'Checked By' status ---
            if not checked_by_is_valid:
                skipped_checked_missing_or_empty_count += 1
                # print("# Skip Info: Sheet {} - Parameter '{}' is missing, empty, or whitespace.".format(sheet_identifier, checked_by_param_name)) # Optional Debug
                continue # Skip this sheet

            # --- Check and Set the 'Approved By' parameter ---
            if approved_by_param is None:
                skipped_approved_missing_count += 1
                # errors.append("# Skip Info: Sheet {} - Parameter '{}' not found.".format(sheet_identifier, approved_by_param_name))
                continue # Skip this sheet - 'Approved By' parameter doesn't exist

            if approved_by_param.IsReadOnly:
                skipped_approved_readonly_count += 1
                # errors.append("# Skip Info: Sheet {} - Parameter '{}' is read-only.".format(sheet_identifier, approved_by_param_name))
                continue # Skip this sheet - parameter is read-only

            # --- Attempt to set the value ---
            try:
                # Check current value to avoid unnecessary sets (optional)
                current_approved_by_value = approved_by_param.AsString() # Assuming it's text
                if current_approved_by_value == approved_by_value_to_set:
                    # Already has the correct value, treat as processed but not 'updated' this run
                    # print("# Skip Info: Sheet {} - Parameter '{}' already set to '{}'.".format(sheet_identifier, approved_by_param_name, approved_by_value_to_set)) # Optional Debug
                    continue


                # THE ACTUAL VALUE SETTING ACTION
                result = approved_by_param.Set(approved_by_value_to_set)

                if result: # Set() returns true on success for most simple types
                    updated_count += 1
                    # print("# Updated Sheet {} - Set '{}' to '{}'".format(sheet_identifier, approved_by_param_name, approved_by_value_to_set)) # Optional success message per sheet
                else:
                    # This case might be rare for simple string Set(), but capture it
                    failed_update_count += 1
                    error_msg = "# Update Warning: Sheet {} - Setting '{}' to '{}' returned false.".format(sheet_identifier, approved_by_param_name, approved_by_value_to_set)
                    errors.append(error_msg)
                    print(error_msg) # Print update warnings immediately

            except Exception as e:
                # Catch errors during the Set() operation
                failed_update_count += 1
                error_msg = "# Update Error: Sheet {} - Failed to set '{}' to '{}': {}".format(sheet_identifier, approved_by_param_name, approved_by_value_to_set, e)
                errors.append(error_msg)
                print(error_msg) # Print update errors immediately

        except Exception as outer_e:
            # Catch unexpected errors during the processing loop for a sheet
            failed_update_count += 1 # Count as failure if error prevents potential update
            error_msg = "# Unexpected Error processing sheet {}: {}".format(sheet_identifier, outer_e)
            errors.append(error_msg)
            print(error_msg) # Print outer loop errors immediately

    # --- Final Summary ---
    print("\n# --- Parameter Update Summary ---")
    print("# Total sheets checked: {}".format(processed_count))
    print("# Sheets successfully updated ('{}' set to '{}'): {}".format(approved_by_param_name, approved_by_value_to_set, updated_count))
    print("# Sheets skipped ('{}' was missing, empty, or whitespace): {}".format(checked_by_param_name, skipped_checked_missing_or_empty_count))
    print("# Sheets skipped ('{}' parameter not found): {}".format(approved_by_param_name, skipped_approved_missing_count))
    print("# Sheets skipped ('{}' parameter was read-only): {}".format(approved_by_param_name, skipped_approved_readonly_count))
    print("# Sheets where update failed or caused an error: {}".format(failed_update_count))

    # Optional: Print detailed errors if needed
    # if errors:
    #     print("\n# --- Errors Encountered During Update ---")
    #     # Filter out skip infos if only showing actual errors
    #     actual_errors = [e for e in errors if e.startswith("# Update Error:") or e.startswith("# Update Warning:") or e.startswith("# Unexpected Error:")]
    #     if actual_errors:
    #         for error in actual_errors:
    #             print(error)
    #     else:
    #         print("# (No critical errors reported, only skip information or update warnings)")