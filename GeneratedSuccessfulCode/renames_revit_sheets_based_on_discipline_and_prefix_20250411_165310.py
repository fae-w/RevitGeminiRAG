# Purpose: This script renames Revit sheets based on discipline and prefix.

﻿# Import necessary classes
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    BuiltInParameter,
    ElementId,
    Parameter
)
import System # For Exception handling

# --- Configuration ---
target_discipline_name = "Structural" # Case-sensitive discipline name
old_prefix = "ST-"
new_prefix = "S-"

# --- Initialization ---
sheets_to_process = []
processed_count = 0
discipline_match_count = 0
prefix_match_count = 0
renamed_count = 0
failed_count = 0
errors = []

# --- Step 1: Collect all ViewSheets ---
collector = FilteredElementCollector(doc).OfClass(ViewSheet)
all_sheets_elements = [sheet for sheet in collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

# --- Step 2: Filter sheets by Discipline and Prefix, prepare for renaming ---
for sheet in all_sheets_elements:
    processed_count += 1
    sheet_discipline = None
    original_sheet_number = None

    try:
        # Get the Discipline parameter
        discipline_param = sheet.get_Parameter(BuiltInParameter.VIEW_DISCIPLINE)
        if discipline_param and discipline_param.HasValue:
            discipline_id = discipline_param.AsElementId()
            if discipline_id != ElementId.InvalidElementId:
                discipline_element = doc.GetElement(discipline_id)
                if discipline_element:
                    # Get the name of the Discipline element
                    sheet_discipline = discipline_element.Name
                else:
                    # Handle cases where the ID is valid but the element isn't found (unlikely)
                    # errors.append("# Warning: Could not find Discipline element for ID {} on sheet ID {}".format(discipline_id, sheet.Id))
                    pass # Silently continue
            else:
                # Handle cases where discipline ID is invalid (e.g., not set)
                # errors.append("# Warning: Invalid Discipline ID for sheet ID {}".format(sheet.Id))
                pass # Silently continue
        else:
             # Handle cases where sheet has no Discipline parameter or no value set
             # errors.append("# Warning: Could not get Discipline parameter or value for sheet ID {}".format(sheet.Id))
             pass # Silently continue

        # Check if the discipline matches
        if sheet_discipline == target_discipline_name:
            discipline_match_count += 1
            try:
                original_sheet_number = sheet.SheetNumber
            except Exception as e:
                # errors.append("# Warning: Could not retrieve SheetNumber for sheet ID {}. Skipping. Error: {}".format(sheet.Id, e))
                continue # Skip this sheet if number cannot be retrieved

            # Check if the sheet number starts with the old prefix
            if original_sheet_number and original_sheet_number.startswith(old_prefix):
                prefix_match_count += 1
                # Construct the new sheet number by replacing the prefix
                new_sheet_number = new_prefix + original_sheet_number[len(old_prefix):]

                # Add to the list for processing
                sheets_to_process.append({
                    "sheet": sheet,
                    "old_number": original_sheet_number,
                    "new_number": new_sheet_number
                })
            # else: # Optional: Log sheets in correct discipline but wrong prefix
                # print("# Info: Sheet '{}' (ID: {}) in '{}' discipline does not start with '{}'".format(original_sheet_number, sheet.Id, target_discipline_name, old_prefix))

        # else: # Optional: Log sheets not in the target discipline
            # print("# Info: Sheet '{}' (ID: {}) is not in '{}' discipline (Discipline: {})".format(sheet.SheetNumber if sheet.SheetNumber else 'N/A', sheet.Id, target_discipline_name, sheet_discipline if sheet_discipline else 'Not Set/Found'))


    except Exception as ex:
        # Catch errors during parameter checking for a sheet
        error_msg = "# Error processing sheet ID {}: {}".format(sheet.Id, ex)
        errors.append(error_msg)
        # print(error_msg) # Optional immediate print
        failed_count += 1 # Count as failure if initial check fails

# --- Step 3: Attempt Renaming ---
if not sheets_to_process:
    print("# No sheets found matching criteria: Discipline '{}' AND starting with prefix '{}'.".format(target_discipline_name, old_prefix))
else:
    print("# Found {} sheets matching criteria. Attempting to rename...".format(len(sheets_to_process)))

    for item in sheets_to_process:
        sheet = item["sheet"]
        old_num = item["old_number"]
        new_num = item["new_number"]

        # Double-check: Skip if old and new numbers are somehow the same
        if old_num == new_num:
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
print("# Sheets in '{}' discipline: {}".format(target_discipline_name, discipline_match_count))
print("# Sheets matching discipline AND prefix '{}': {}".format(old_prefix, prefix_match_count))
print("# Sheets successfully renamed: {}".format(renamed_count))
print("# Sheets failed to rename (incl. initial check errors): {}".format(failed_count))

# Errors were already printed when they occurred.
# if failed_count > 0:
#     print("# Review errors above for details on failures.")