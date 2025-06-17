# Purpose: This script renames Revit sheets by appending a date suffix derived from the 'Sheet Issue Date' parameter.

﻿# Imports
import clr
clr.AddReference('System')
from System import DateTime, String, Exception, Globalization # Need Globalization
from System.Globalization import CultureInfo # Explicit import for CultureInfo
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, ElementId, BuiltInParameter
import System # Keep this for general Exception and ArgumentException

# --- Configuration ---
# Define the date formats to try parsing. Add more if needed.
# Using CultureInfo.InvariantCulture to avoid locale issues (e.g., MM/dd vs dd/MM)
# Examples: "MM/dd/yyyy", "yyyy-MM-dd", "dd MMM yyyy", "MMMM d, yyyy"
date_formats_to_try = [
    "MM/dd/yyyy", "M/d/yyyy",
    "yyyy-MM-dd", "yyyy-M-d",
    "dd MMM yyyy", "d MMM yyyy", "dd-MMM-yy",
    "MMMM dd, yyyy", "MMMM d, yyyy",
    "yyyy.MM.dd", "dd.MM.yyyy",
    # Add other potential common formats as strings here if necessary
]
date_suffix_format = "yyMMdd" # Format for the appended date suffix
separator = "_" # Separator between original number and date suffix

# --- Initialization ---
processed_count = 0
renamed_count = 0
skipped_no_param_count = 0
skipped_no_value_count = 0
skipped_parse_fail_count = 0
failed_rename_count = 0
already_named_count = 0
errors = [] # Stores errors for summary reporting, especially parse errors

# --- Step 1: Collect all ViewSheets ---
collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure elements are valid ViewSheets before processing
all_sheets = [sheet for sheet in collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

if not all_sheets:
    print("# No ViewSheet elements found in the project.")
else:
    print("# Found {} sheets. Processing to add '{}YYMMDD' suffix based on 'Sheet Issue Date'...".format(len(all_sheets), separator))

    # --- Step 2: Iterate and attempt rename ---
    for sheet in all_sheets:
        processed_count += 1
        original_sheet_number = None
        date_param_value_str = None
        parsed_date = None
        new_sheet_number = None
        sheet_id_str = "Unknown ID" # Placeholder in case ID retrieval fails

        try:
            sheet_id_str = sheet.Id.ToString() # Get ID early for error messages
            original_sheet_number = sheet.SheetNumber

            # --- Get 'Sheet Issue Date' parameter ---
            # Prefer BuiltInParameter first
            date_param = sheet.get_Parameter(BuiltInParameter.SHEET_ISSUE_DATE)

            # Fallback to lookup by name if BuiltInParameter is not found or invalid
            # (InvalidElementId check is good practice though less common for BuiltInParams)
            if date_param is None or date_param.Id == ElementId.InvalidElementId:
                 date_param = sheet.LookupParameter("Sheet Issue Date")

            # Check if parameter was found and has a value
            if date_param is None:
                skipped_no_param_count += 1
                continue # Skip this sheet - parameter doesn't exist
            elif not date_param.HasValue:
                 skipped_no_value_count += 1
                 continue # Skip this sheet - parameter exists but is empty

            date_param_value_str = date_param.AsString()

            # Double-check if AsString() returned null or empty
            if String.IsNullOrEmpty(date_param_value_str):
                skipped_no_value_count += 1
                continue # Skip this sheet - parameter value is effectively empty

            # --- Parse the date string ---
            parse_success = False
            # Placeholder variable necessary for TryParseExact/TryParse in IronPython
            # where 'out' parameters work via tuple return (success_flag, parsed_value)
            parsed_date_temp = DateTime.MinValue

            for fmt in date_formats_to_try:
                 # Using TryParseExact for specific formats with InvariantCulture (culture-neutral)
                 success, parsed_date_temp = DateTime.TryParseExact(date_param_value_str, fmt, CultureInfo.InvariantCulture, Globalization.DateTimeStyles.AllowWhiteSpaces)
                 if success:
                     parsed_date = parsed_date_temp
                     parse_success = True
                     break # Stop trying formats once one works

            # Fallback: Try general Parse using InvariantCulture if specific formats failed
            if not parse_success:
                 try:
                      # Try parsing using the invariant culture first to be safer
                      parsed_date = DateTime.Parse(date_param_value_str, CultureInfo.InvariantCulture, Globalization.DateTimeStyles.AllowWhiteSpaces)
                      parse_success = True
                 except Exception:
                      # Optional: Could try DateTime.Parse with current culture as a last resort, but risks ambiguity
                      # try:
                      #     parsed_date = DateTime.Parse(date_param_value_str, CultureInfo.CurrentCulture, Globalization.DateTimeStyles.AllowWhiteSpaces)
                      #     parse_success = True
                      # except: pass
                      pass # General parse failed

            if not parse_success:
                skipped_parse_fail_count += 1
                # Store specific parse error details for later summary
                errors.append("# Parse Error: Sheet '{}' (ID: {}), Date='{}'".format(original_sheet_number, sheet_id_str, date_param_value_str))
                continue # Skip this sheet - cannot parse date

            # --- Format date and construct new name ---
            date_suffix = parsed_date.ToString(date_suffix_format)
            proposed_suffix = separator + date_suffix
            new_sheet_number = original_sheet_number + proposed_suffix

            # --- Check if rename is needed (avoids unnecessary transaction entries) ---
            # Also handles cases where the original number somehow already had the correct suffix
            if original_sheet_number.endswith(proposed_suffix):
                 already_named_count += 1
                 continue # Skip, already has the correct suffix

            # --- Rename the sheet ---
            # Double check it's actually different before attempting API call
            if new_sheet_number != original_sheet_number:
                try:
                    # THE ACTUAL RENAMING ACTION
                    sheet.SheetNumber = new_sheet_number
                    renamed_count += 1
                    # print("# Renamed Sheet '{}' to '{}'".format(original_sheet_number, new_sheet_number)) # Optional success message per sheet
                except System.ArgumentException as arg_ex:
                    # Specific handling for common errors like duplicate numbers
                    failed_rename_count += 1
                    error_msg = "# Rename Error: Sheet '{}' (ID: {}) to '{}': {}. (Is number already in use?)".format(original_sheet_number, sheet_id_str, new_sheet_number, arg_ex.Message)
                    errors.append(error_msg)
                    print(error_msg) # Print rename errors immediately for visibility
                except Exception as e:
                    # Catch other potential API errors during renaming
                    failed_rename_count += 1
                    error_msg = "# Rename Error: Sheet '{}' (ID: {}) to '{}': {}".format(original_sheet_number, sheet_id_str, new_sheet_number, e)
                    errors.append(error_msg)
                    print(error_msg) # Print rename errors immediately

        except Exception as outer_e:
            # Catch unexpected errors during the processing loop for a sheet (e.g., accessing properties)
            failed_rename_count += 1 # Count as failure if error prevents potential rename
            error_msg = "# Unexpected Error processing sheet ID {}: {}".format(sheet_id_str, outer_e)
            # Try to include original number if available
            if original_sheet_number:
                 error_msg = "# Unexpected Error processing sheet '{}' (ID: {}): {}".format(original_sheet_number, sheet_id_str, outer_e)
            errors.append(error_msg)
            print(error_msg) # Print outer loop errors immediately


    # --- Final Summary ---
    print("\n# --- Renaming Summary ---")
    print("# Total sheets checked: {}".format(processed_count))
    print("# Sheets successfully renamed: {}".format(renamed_count))
    print("# Sheets already had correct date suffix: {}".format(already_named_count))
    print("# Sheets skipped (No 'Sheet Issue Date' parameter found): {}".format(skipped_no_param_count))
    print("# Sheets skipped (Parameter was empty or had no value): {}".format(skipped_no_value_count))
    print("# Sheets skipped (Could not parse date value): {}".format(skipped_parse_fail_count))
    print("# Sheets failed during rename attempt (e.g., duplicates, errors): {}".format(failed_rename_count))

    # Report specific parse errors if any occurred, as these are common issues
    if skipped_parse_fail_count > 0:
        print("\n# --- Date Parse Errors Details ---")
        parse_errors_found = False
        for error in errors:
            if error.startswith("# Parse Error:"):
                print(error)
                parse_errors_found = True
        if not parse_errors_found:
             print("# (No specific parse error details were logged)") # Should not happen if count > 0

    # Optionally report other errors if needed
    # other_errors = [e for e in errors if not e.startswith("# Parse Error:")]
    # if other_errors:
    #     print("\n# --- Other Errors Encountered ---")
    #     for error in other_errors:
    #          print(error)