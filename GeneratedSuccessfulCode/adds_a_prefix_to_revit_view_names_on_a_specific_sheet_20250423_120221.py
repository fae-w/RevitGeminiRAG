# Purpose: This script adds a prefix to Revit view names on a specific sheet.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, Viewport, View, ElementId, Element
import System # For Exception handling

# --- Configuration ---
target_sheet_number = "A-101" # Case-sensitive sheet number to find
prefix_to_add = "A-101 - " # Prefix to add to the view name

# --- Initialization ---
renamed_count = 0
already_prefixed_count = 0
processed_viewport_count = 0
skipped_not_view_count = 0
failed_count = 0
errors = []
target_sheets_found = []

# --- Step 1: Find the target ViewSheet(s) by SheetNumber ---
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
# Ensure we only get ViewSheet elements and check SheetNumber
for sheet in sheet_collector:
    if isinstance(sheet, ViewSheet) and sheet.IsValidObject and sheet.SheetNumber == target_sheet_number:
        target_sheets_found.append(sheet)

if not target_sheets_found:
    print("# Error: No sheet found with Sheet Number '{}'.".format(target_sheet_number))
else:
    print("# Found {} sheet(s) with number '{}'. Processing views...".format(len(target_sheets_found), target_sheet_number))

    # --- Step 2 & 3: Iterate through sheets, get viewports, get views, and rename ---
    for sheet in target_sheets_found:
        sheet_id_str = str(sheet.Id)
        sheet_name = "Unknown"
        try:
            sheet_name = sheet.Name
        except:
            pass # Keep default Unknown name if fails

        print("# Processing sheet: '{}' (Number: {}, ID: {})".format(sheet_name, sheet.SheetNumber, sheet_id_str))
        try:
            # GetAllViewports returns ElementIds of Viewports
            viewport_ids = sheet.GetAllViewports()
            if not viewport_ids or viewport_ids.Count == 0:
                print("#   Sheet '{}' has no viewports.".format(sheet_name))
                continue

            # --- Iterate through viewports on this sheet ---
            for vp_id in viewport_ids:
                processed_viewport_count += 1
                viewport = None
                view_element = None
                current_name = None

                try:
                    if vp_id == ElementId.InvalidElementId:
                        errors.append("# Skipped: Invalid Viewport ID found on sheet {}.".format(sheet_id_str))
                        continue

                    viewport = doc.GetElement(vp_id)
                    if not viewport or not isinstance(viewport, Viewport):
                        errors.append("# Skipped: Element ID {} on sheet {} is not a valid Viewport.".format(vp_id, sheet_id_str))
                        continue

                    view_id = viewport.ViewId
                    if view_id == ElementId.InvalidElementId:
                        errors.append("# Skipped: Viewport ID {} on sheet {} has an invalid ViewId.".format(vp_id, sheet_id_str))
                        continue

                    view_element = doc.GetElement(view_id)

                    # Check if the element is a valid View
                    if not view_element or not isinstance(view_element, View):
                        skipped_not_view_count += 1
                        errors.append("# Skipped: Element ID {} (from Viewport {}) on sheet {} is not a valid View.".format(view_id, vp_id, sheet_id_str))
                        continue

                    # Get current name
                    try:
                        # Use Element.Name property which works for Views
                        current_name = Element.Name.__get__(view_element)
                    except Exception as name_ex:
                        failed_count += 1
                        errors.append("# Error getting name for View ID {} (from Viewport {}) on sheet {}: {}".format(view_id, vp_id, sheet_id_str, name_ex))
                        continue # Skip if we can't even get the name

                    # Check if already has the prefix
                    if current_name.startswith(prefix_to_add):
                        already_prefixed_count += 1
                        # print("#   View '{}' (ID: {}) already has the prefix.".format(current_name, view_id)) # Optional debug
                        continue # Skip, already named correctly

                    # Construct new name
                    new_name = prefix_to_add + current_name

                    # Attempt rename
                    try:
                        # Use Element.Name property setter
                        Element.Name.__set__(view_element, new_name)
                        renamed_count += 1
                        # print("#   Renamed View '{}' to '{}'".format(current_name, new_name)) # Optional debug
                    except System.ArgumentException as arg_ex:
                        # Handle specific errors like duplicate names
                        failed_count += 1
                        error_msg = "# Rename Error (Sheet {}): View '{}' (ID: {}) to '{}': {} (Likely duplicate name)".format(sheet_id_str, current_name, view_id, new_name, arg_ex.Message)
                        errors.append(error_msg)
                        print(error_msg) # Print immediately
                    except Exception as rename_ex:
                        failed_count += 1
                        error_msg = "# Rename Error (Sheet {}): View '{}' (ID: {}) to '{}': {}".format(sheet_id_str, current_name, view_id, new_name, rename_ex)
                        errors.append(error_msg)
                        print(error_msg) # Print immediately

                except System.Exception as inner_ex: # Catch more specific .NET exceptions if possible
                     # Catch errors during viewport/view retrieval or initial checks
                     failed_count += 1
                     error_msg = "# Unexpected Error processing Viewport ID {} on sheet {}: {}".format(vp_id, sheet_id_str, inner_ex)
                     errors.append(error_msg)
                     print(error_msg) # Print immediately
                except Exception as inner_py_ex: # Catch Python-specific exceptions
                     failed_count += 1
                     error_msg = "# Python Error processing Viewport ID {} on sheet {}: {}".format(vp_id, sheet_id_str, inner_py_ex)
                     errors.append(error_msg)
                     print(error_msg) # Print immediately


        except System.Exception as outer_ex:
            # Catch errors getting viewports for a sheet
            errors.append("# Error getting viewports for sheet '{}' (ID: {}): {}".format(sheet_name, sheet_id_str, outer_ex))
            print("# Warning: Could not process viewports for sheet '{}' (ID: {}). Error: {}".format(sheet_name, sheet_id_str, outer_ex))
        except Exception as outer_py_ex:
            errors.append("# Python Error getting viewports for sheet '{}' (ID: {}): {}".format(sheet_name, sheet_id_str, outer_py_ex))
            print("# Warning: Could not process viewports for sheet '{}' (ID: {}). Python Error: {}".format(sheet_name, sheet_id_str, outer_py_ex))


    # --- Final Summary ---
    print("\n# --- View Renaming Summary for Sheet(s) with Number '{}' ---".format(target_sheet_number))
    print("# Total viewports processed across {} sheet(s): {}".format(len(target_sheets_found), processed_viewport_count))
    print("# Views successfully renamed: {}".format(renamed_count))
    print("# Views already had the prefix '{}': {}".format(prefix_to_add, already_prefixed_count))
    print("# Skipped elements that were not valid Views: {}".format(skipped_not_view_count))
    print("# Views/Viewports failed during processing/rename: {}".format(failed_count))

    # Optional: Print detailed errors/skipped items
    # if errors:
    #     print("\n# --- Encountered Errors/Skipped Items ---")
    #     for error in errors:
    #         print(error)