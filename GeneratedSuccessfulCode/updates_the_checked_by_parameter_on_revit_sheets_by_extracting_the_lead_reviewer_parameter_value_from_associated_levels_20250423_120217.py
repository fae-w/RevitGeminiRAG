# Purpose: This script updates the 'Checked By' parameter on Revit sheets by extracting the 'Lead Reviewer' parameter value from associated levels.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling and String
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    View,
    Level,
    Parameter,
    StorageType,
    ElementId,
    BuiltInParameter,
    Element
)
import System # For Exception and String
from System import String # Explicit import for String utilities

# --- Configuration ---
checked_by_param_name = "Checked By"
lead_reviewer_param_name = "Lead Reviewer" # Custom parameter on Level elements

# --- Initialization ---
processed_sheet_count = 0
updated_sheet_count = 0
skipped_no_view_or_level_count = 0
skipped_level_param_missing_or_empty_count = 0
skipped_sheet_param_missing_count = 0
skipped_sheet_param_readonly_count = 0
failed_update_count = 0
errors = [] # Stores errors for summary reporting

# --- Step 1: Collect all ViewSheets ---
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure elements are valid ViewSheets before processing
all_sheets = [sheet for sheet in sheet_collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

if not all_sheets:
    print("# No ViewSheet elements found in the project.")
else:
    print("# Found {0} sheets. Processing parameters '{1}' and '{2}'...".format(len(all_sheets), checked_by_param_name, lead_reviewer_param_name))

    # --- Step 2: Iterate through each sheet ---
    for sheet in all_sheets:
        processed_sheet_count += 1
        sheet_identifier = "Unknown Sheet" # Placeholder
        lead_reviewer_value = None
        level_found = False

        try:
            sheet_identifier = "'{0}' (ID: {1})".format(sheet.SheetNumber, sheet.Id)

            # --- Step 2a: Find the associated Level and 'Lead Reviewer' value ---
            placed_view_ids = sheet.GetAllPlacedViews()
            if not placed_view_ids:
                skipped_no_view_or_level_count += 1
                # print("# Skip Info: Sheet {0} - No views placed.".format(sheet_identifier)) # Optional Debug
                continue # Skip sheets with no views

            for view_id in placed_view_ids:
                view = doc.GetElement(view_id)
                if not view or not isinstance(view, View):
                    continue # Skip if element is not a valid View

                # Get the Level associated with the view
                level_id_param = view.get_Parameter(BuiltInParameter.VIEW_LEVEL_ID) # More reliable than GenLevel maybe
                level_id = ElementId.InvalidElementId
                if level_id_param and level_id_param.HasValue:
                    level_id = level_id_param.AsElementId()

                # Check if the level ID is valid
                if level_id != ElementId.InvalidElementId:
                    level = doc.GetElement(level_id)
                    if level and isinstance(level, Level):
                        level_found = True # Found a view associated with a level
                        # --- Look up the 'Lead Reviewer' parameter on the Level ---
                        lead_reviewer_param = level.LookupParameter(lead_reviewer_param_name)

                        if lead_reviewer_param is not None and lead_reviewer_param.HasValue:
                            lead_reviewer_value_str = None
                            try:
                                if lead_reviewer_param.StorageType == StorageType.String:
                                    lead_reviewer_value_str = lead_reviewer_param.AsString()
                                else:
                                    # Try AsValueString for non-string types
                                    lead_reviewer_value_str = lead_reviewer_param.AsValueString()
                            except Exception:
                                # Fallback if AsValueString fails
                                try:
                                    lead_reviewer_value_str = lead_reviewer_param.AsString() # Try AsString again
                                except Exception:
                                    pass # Could not get string value

                            # Check if the extracted value is meaningful
                            if not String.IsNullOrWhiteSpace(lead_reviewer_value_str):
                                lead_reviewer_value = lead_reviewer_value_str
                                break # Found a valid Lead Reviewer value, stop checking views on this sheet
                            else:
                                # Found the param but it's empty, continue checking other views just in case
                                pass
                        else:
                             # Level exists, but no 'Lead Reviewer' param or no value, continue checking other views
                             pass
                # If level_id is invalid or level element is not found, check next view
            # End of view loop for this sheet

            # --- Step 2b: Process the sheet based on found data ---
            if lead_reviewer_value is None:
                if level_found:
                    # We found a level-associated view, but no valid 'Lead Reviewer' value
                    skipped_level_param_missing_or_empty_count += 1
                    # print("# Skip Info: Sheet {0} - Found associated Level(s), but '{1}' param missing, empty, or whitespace.".format(sheet_identifier, lead_reviewer_param_name)) # Optional Debug
                else:
                    # No view on the sheet had a valid associated level
                    skipped_no_view_or_level_count += 1
                    # print("# Skip Info: Sheet {0} - No views found with an associated Level.".format(sheet_identifier)) # Optional Debug
                continue # Skip this sheet

            # --- Step 2c: Get and set the 'Checked By' parameter on the sheet ---
            checked_by_param = sheet.LookupParameter(checked_by_param_name)

            if checked_by_param is None:
                skipped_sheet_param_missing_count += 1
                # errors.append("# Skip Info: Sheet {0} - Parameter '{1}' not found on sheet.".format(sheet_identifier, checked_by_param_name))
                continue # Skip this sheet

            if checked_by_param.IsReadOnly:
                skipped_sheet_param_readonly_count += 1
                # errors.append("# Skip Info: Sheet {0} - Parameter '{1}' is read-only.".format(sheet_identifier, checked_by_param_name))
                continue # Skip this sheet

            # --- Attempt to set the value ---
            try:
                # Check current value to avoid unnecessary sets (optional)
                current_checked_by_value = checked_by_param.AsString() # Assuming it's text
                if current_checked_by_value == lead_reviewer_value:
                    # print("# Skip Info: Sheet {0} - Parameter '{1}' already set to '{2}'.".format(sheet_identifier, checked_by_param_name, lead_reviewer_value)) # Optional Debug
                    continue

                # THE ACTUAL VALUE SETTING ACTION
                result = checked_by_param.Set(lead_reviewer_value)

                if result: # Set() returns true on success for most simple types
                    updated_sheet_count += 1
                    # print("# Updated Sheet {0} - Set '{1}' to '{2}'".format(sheet_identifier, checked_by_param_name, lead_reviewer_value)) # Optional success message per sheet
                else:
                    # This case might be rare for simple string Set(), but capture it
                    failed_update_count += 1
                    error_msg = "# Update Warning: Sheet {0} - Setting '{1}' to '{2}' returned false.".format(sheet_identifier, checked_by_param_name, lead_reviewer_value)
                    errors.append(error_msg)
                    print(error_msg) # Print update warnings immediately

            except Exception as e:
                # Catch errors during the Set() operation
                failed_update_count += 1
                error_msg = "# Update Error: Sheet {0} - Failed to set '{1}' to '{2}': {3}".format(sheet_identifier, checked_by_param_name, lead_reviewer_value, e)
                errors.append(error_msg)
                print(error_msg) # Print update errors immediately

        except Exception as outer_e:
            # Catch unexpected errors during the processing loop for a sheet
            failed_update_count += 1 # Count as failure if error prevents potential update
            error_msg = "# Unexpected Error processing sheet {0}: {1}".format(sheet_identifier, outer_e)
            errors.append(error_msg)
            print(error_msg) # Print outer loop errors immediately

    # --- Final Summary ---
    print("\n# --- Parameter Update Summary ---")
    print("# Total sheets checked: {0}".format(processed_sheet_count))
    print("# Sheets successfully updated ('{0}' populated): {1}".format(checked_by_param_name, updated_sheet_count))
    print("# Sheets skipped (no view found or no view had associated Level): {0}".format(skipped_no_view_or_level_count))
    print("# Sheets skipped (Level found, but '{0}' param missing/empty on Level): {1}".format(lead_reviewer_param_name, skipped_level_param_missing_or_empty_count))
    print("# Sheets skipped ('{0}' param missing on Sheet): {1}".format(checked_by_param_name, skipped_sheet_param_missing_count))
    print("# Sheets skipped ('{0}' param read-only on Sheet): {1}".format(checked_by_param_name, skipped_sheet_param_readonly_count))
    print("# Sheets where update failed or caused an error: {0}".format(failed_update_count))

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