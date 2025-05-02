# Purpose: This script renames Revit sheets based on a specified parameter value.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling and String
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, ElementId, Parameter, StorageType
import System # For Exception and ArgumentException
from System import String # Explicit import for String utilities

# --- Configuration ---
custom_parameter_name = "Drawing Type" # The name of the custom parameter to use for the new sheet number

# --- Initialization ---
processed_count = 0
renamed_count = 0
skipped_no_param_count = 0
skipped_no_value_count = 0
skipped_already_named_count = 0
failed_rename_count = 0
errors = [] # Stores errors for summary reporting

# --- Step 1: Collect all ViewSheets ---
collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure elements are valid ViewSheets before processing
all_sheets = [sheet for sheet in collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

if not all_sheets:
    print("# No ViewSheet elements found in the project.")
else:
    print("# Found {} sheets. Processing to rename based on '{}' parameter...".format(len(all_sheets), custom_parameter_name))

    # --- Step 2: Iterate and attempt rename ---
    for sheet in all_sheets:
        processed_count += 1
        original_sheet_number = None
        new_sheet_number_value = None
        sheet_id_str = "Unknown ID" # Placeholder in case ID retrieval fails

        try:
            sheet_id_str = sheet.Id.ToString() # Get ID early for error messages
            original_sheet_number = sheet.SheetNumber

            # --- Get the custom parameter ---
            drawing_type_param = sheet.LookupParameter(custom_parameter_name)

            # --- Check if parameter exists and has a value ---
            if drawing_type_param is None:
                skipped_no_param_count += 1
                # errors.append("# Skip Info: Sheet '{}' (ID: {}) - Parameter '{}' not found.".format(original_sheet_number, sheet_id_str, custom_parameter_name))
                continue # Skip this sheet - parameter doesn't exist
            elif not drawing_type_param.HasValue:
                skipped_no_value_count += 1
                # errors.append("# Skip Info: Sheet '{}' (ID: {}) - Parameter '{}' is empty.".format(original_sheet_number, sheet_id_str, custom_parameter_name))
                continue # Skip this sheet - parameter exists but is empty

            # --- Get the parameter value as string ---
            # Ensure the parameter storage type is suitable (usually Text for names)
            if drawing_type_param.StorageType == StorageType.String:
                new_sheet_number_value = drawing_type_param.AsString()
            else:
                # If it's not a string type, try getting its value representation
                # AsValueString() often works for various types but might include units
                # If specific formatting is needed for numeric/other types, handle it here
                try:
                    new_sheet_number_value = drawing_type_param.AsValueString()
                except Exception:
                     # Fallback to AsString just in case AsValueString fails
                     new_sheet_number_value = drawing_type_param.AsString()


            # --- Validate the retrieved value ---
            if String.IsNullOrEmpty(new_sheet_number_value) or new_sheet_number_value.isspace():
                skipped_no_value_count += 1
                # errors.append("# Skip Info: Sheet '{}' (ID: {}) - Parameter '{}' value is null or whitespace.".format(original_sheet_number, sheet_id_str, custom_parameter_name))
                continue # Skip this sheet - parameter value is effectively empty or just spaces

            # Trim whitespace from the parameter value before using it
            new_sheet_number_value = new_sheet_number_value.strip()

            # --- Check if rename is needed ---
            if new_sheet_number_value == original_sheet_number:
                skipped_already_named_count += 1
                continue # Skip, already has the correct number

            # --- Rename the sheet ---
            try:
                # THE ACTUAL RENAMING ACTION
                sheet.SheetNumber = new_sheet_number_value
                renamed_count += 1
                # print("# Renamed Sheet '{}' to '{}'".format(original_sheet_number, new_sheet_number_value)) # Optional success message per sheet
            except System.ArgumentException as arg_ex:
                # Specific handling for common errors like duplicate numbers or invalid characters
                failed_rename_count += 1
                error_msg = "# Rename Error: Sheet '{}' (ID: {}) to '{}': {}. (Is number already in use or invalid?)".format(original_sheet_number, sheet_id_str, new_sheet_number_value, arg_ex.Message)
                errors.append(error_msg)
                print(error_msg) # Print rename errors immediately for visibility
            except Exception as e:
                # Catch other potential API errors during renaming
                failed_rename_count += 1
                error_msg = "# Rename Error: Sheet '{}' (ID: {}) to '{}': {}".format(original_sheet_number, sheet_id_str, new_sheet_number_value, e)
                errors.append(error_msg)
                print(error_msg) # Print rename errors immediately

        except Exception as outer_e:
            # Catch unexpected errors during the processing loop for a sheet
            failed_rename_count += 1 # Count as failure if error prevents potential rename
            error_msg = "# Unexpected Error processing sheet ID {}: {}".format(sheet_id_str, outer_e)
            # Try to include original number if available
            if original_sheet_number:
                 error_msg = "# Unexpected Error processing sheet '{}' (ID: {}): {}".format(original_sheet_number, sheet_id_str, outer_e)
            errors.append(error_msg)
            print(error_msg) # Print outer loop errors immediately


    # --- Final Summary ---
    print("\n# --- Sheet Renaming Summary ---")
    print("# Total sheets checked: {}".format(processed_count))
    print("# Sheets successfully renamed: {}".format(renamed_count))
    print("# Sheets skipped (already had the correct number): {}".format(skipped_already_named_count))
    print("# Sheets skipped (Parameter '{}' not found): {}".format(custom_parameter_name, skipped_no_param_count))
    print("# Sheets skipped (Parameter '{}' was empty or whitespace): {}".format(custom_parameter_name, skipped_no_value_count))
    print("# Sheets failed during rename attempt (e.g., duplicates, invalid chars, errors): {}".format(failed_rename_count))

    # Optional: Print detailed errors if needed
    # if errors:
    #     print("\n# --- Errors Encountered ---")
    #     # Filter out skip infos if only showing actual errors
    #     actual_errors = [e for e in errors if e.startswith("# Rename Error:") or e.startswith("# Unexpected Error:")]
    #     if actual_errors:
    #         for error in actual_errors:
    #             print(error)
    #     else:
    #         print("# (No critical errors reported, only skip information)")