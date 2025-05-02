# Purpose: This script renames Revit section views based on their sheet and detail number.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSection,
    Viewport,
    ViewSheet,
    ElementId,
    BuiltInParameter,
    Element
)
import System # For Exception handling

# --- Configuration ---
# Define the format for the new view name.
# Placeholders: {sheet_number}, {detail_number}
# Example: "SECTION {sheet_number}-{detail_number}"
# Example: "S{sheet_number}_D{detail_number}"
# Example: "{sheet_number}-{detail_number} Section Cut"
new_name_format = "SECTION {sheet_number}-{detail_number}"
# If True, skip renaming if the view is placed on multiple sheets.
# If False, rename based on the *first* sheet found where it's placed.
skip_if_multiple_placements = False

# --- Initialization ---
processed_count = 0
renamed_count = 0
skipped_not_placed_count = 0
skipped_no_sheet_count = 0
skipped_no_detail_num_count = 0
skipped_multiple_placements_count = 0
already_named_count = 0
failed_rename_count = 0
errors = []

# --- Step 1: Collect all ViewSections ---
collector = FilteredElementCollector(doc).OfClass(ViewSection)
all_sections = [v for v in collector if v and v.IsValidObject and isinstance(v, ViewSection) and not v.IsTemplate]

if not all_sections:
    print("# No ViewSection elements found in the project.")
else:
    print("# Found {} ViewSections. Processing to rename based on sheet placement...".format(len(all_sections)))

    # --- Step 2: Iterate through each ViewSection ---
    for section_view in all_sections:
        processed_count += 1
        original_name = "Unknown"
        view_id_str = section_view.Id.ToString()

        try:
            original_name = section_view.Name

            # --- Step 3: Find Viewports associated with this ViewSection ---
            viewport_collector = FilteredElementCollector(doc).OfClass(Viewport)
            # Filter viewports by the ViewId they display
            # Using ElementParameterFilter requires .NET list or specific constructor
            # Easier to filter in Python loop for this case
            viewports_for_section = []
            for vp in viewport_collector:
                if vp.ViewId == section_view.Id:
                    viewports_for_section.append(vp)

            if not viewports_for_section:
                skipped_not_placed_count += 1
                # print(f"# Skipping View '{original_name}' (ID: {view_id_str}): Not placed on any sheet.") # Debug
                continue # Skip this section, it's not on any sheet

            # --- Handle multiple placements if configured ---
            if len(viewports_for_section) > 1 and skip_if_multiple_placements:
                skipped_multiple_placements_count += 1
                # print(f"# Skipping View '{original_name}' (ID: {view_id_str}): Placed on multiple sheets ({len(viewports_for_section)}).") # Debug
                continue

            # --- Process the first found viewport ---
            # If skip_if_multiple_placements is False, we just use the first one.
            target_viewport = viewports_for_section[0]
            sheet_number = None
            detail_number = None

            # --- Get Sheet Number ---
            sheet_id = target_viewport.SheetId
            if sheet_id == ElementId.InvalidElementId:
                skipped_no_sheet_count += 1
                errors.append("# Error: Viewport ID {} for View '{}' (ID: {}) has an invalid SheetId.".format(target_viewport.Id, original_name, view_id_str))
                continue # Skip, cannot find the sheet

            sheet = doc.GetElement(sheet_id)
            if not sheet or not isinstance(sheet, ViewSheet):
                skipped_no_sheet_count += 1
                errors.append("# Error: Could not retrieve valid ViewSheet with ID {} for View '{}' (ID: {}).".format(sheet_id, original_name, view_id_str))
                continue # Skip, invalid sheet element

            try:
                sheet_number = sheet.SheetNumber
                if System.String.IsNullOrEmpty(sheet_number):
                     skipped_no_sheet_count += 1
                     errors.append("# Warning: Sheet '{}' (ID: {}) has no Sheet Number. Skipping rename for View '{}' (ID: {}).".format(sheet.Name, sheet_id, original_name, view_id_str))
                     continue # Skip if sheet number is empty
            except Exception as e:
                 skipped_no_sheet_count += 1
                 errors.append("# Error getting SheetNumber for Sheet ID {}: {}. Skipping rename for View '{}' (ID: {}).".format(sheet_id, e, original_name, view_id_str))
                 continue


            # --- Get Detail Number ---
            detail_num_param = target_viewport.get_Parameter(BuiltInParameter.VIEWPORT_DETAIL_NUMBER)
            if detail_num_param is None or not detail_num_param.HasValue:
                skipped_no_detail_num_count += 1
                # print(f"# Skipping View '{original_name}' (ID: {view_id_str}): Viewport ID {target_viewport.Id} has no Detail Number.") # Debug
                continue # Skip, detail number parameter not found or empty

            detail_number = detail_num_param.AsString()
            if System.String.IsNullOrEmpty(detail_number):
                 skipped_no_detail_num_count += 1
                 # print(f"# Skipping View '{original_name}' (ID: {view_id_str}): Viewport ID {target_viewport.Id} has empty Detail Number.") # Debug
                 continue # Skip if detail number is empty string

            # --- Construct the new name ---
            try:
                new_name = new_name_format.format(sheet_number=sheet_number, detail_number=detail_number)
            except Exception as format_ex:
                failed_rename_count += 1
                errors.append("# Error formatting new name for View '{}' (ID: {}): {}. Format string: '{}'".format(original_name, view_id_str, format_ex, new_name_format))
                continue # Skip if formatting fails

            # --- Check if rename is necessary ---
            if new_name == original_name:
                already_named_count += 1
                continue # Skip, already has the target name

            # --- Attempt to rename the ViewSection ---
            try:
                section_view.Name = new_name
                renamed_count += 1
                # print(f"# Renamed View '{original_name}' to '{new_name}' (ID: {view_id_str})") # Debug success
            except System.ArgumentException as arg_ex:
                # Handle specific errors like duplicate names
                failed_rename_count += 1
                error_msg = "# Rename Error: View '{}' (ID: {}) to '{}': {}. (Likely duplicate name)".format(original_name, view_id_str, new_name, arg_ex.Message)
                errors.append(error_msg)
                print(error_msg) # Print immediately
            except Exception as rename_ex:
                failed_rename_count += 1
                error_msg = "# Rename Error: View '{}' (ID: {}) to '{}': {}".format(original_name, view_id_str, new_name, rename_ex)
                errors.append(error_msg)
                print(error_msg) # Print immediately

        except Exception as outer_ex:
            # Catch errors during the main processing loop for a section
            failed_rename_count += 1
            error_msg = "# Unexpected Error processing View '{}' (ID: {}): {}".format(original_name if original_name != "Unknown" else "ID", view_id_str, outer_ex)
            errors.append(error_msg)
            print(error_msg) # Print immediately


    # --- Final Summary ---
    print("\n# --- ViewSection Renaming Summary ---")
    print("# Total ViewSections checked: {}".format(processed_count))
    print("# Sections successfully renamed: {}".format(renamed_count))
    print("# Sections already had the target name: {}".format(already_named_count))
    print("# Sections skipped (Not placed on any sheet): {}".format(skipped_not_placed_count))
    if skip_if_multiple_placements:
        print("# Sections skipped (Placed on multiple sheets): {}".format(skipped_multiple_placements_count))
    print("# Sections skipped (Could not find Sheet or Sheet Number): {}".format(skipped_no_sheet_count))
    print("# Sections skipped (Viewport had no Detail Number): {}".format(skipped_no_detail_num_count))
    print("# Sections failed during rename attempt (e.g., duplicates, errors): {}".format(failed_rename_count))

    # Print specific errors if any occurred
    #if errors:
    #    print("\n# --- Encountered Errors/Warnings ---")
    #    for error in errors:
    #        print(error)