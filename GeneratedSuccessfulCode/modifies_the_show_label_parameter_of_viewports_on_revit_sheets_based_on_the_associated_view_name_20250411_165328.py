# Purpose: This script modifies the 'Show Label' parameter of viewports on Revit sheets based on the associated view name.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, Viewport, ViewSheet, View, ElementId, BuiltInParameter, Parameter
import System # For Exception handling

# --- Configuration ---
target_substring = "Drafting" # Case-sensitive substring to find in the View Name
target_value = 0 # 0 for False, 1 for True (for Yes/No parameter)

# --- Initialization ---
processed_sheet_count = 0
processed_viewport_count = 0
modified_count = 0
skipped_no_view_count = 0
skipped_name_mismatch_count = 0
skipped_no_param_count = 0
skipped_readonly_count = 0
already_set_count = 0
failed_count = 0
errors = []

# --- Step 1: Collect all ViewSheets ---
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
all_sheets = list(sheet_collector) # Convert iterator to list

if not all_sheets:
    print("# No ViewSheet elements found in the project.")
else:
    print("# Found {} sheets. Processing viewports on them...".format(len(all_sheets)))

    # --- Step 2: Iterate through Sheets ---
    for sheet in all_sheets:
        processed_sheet_count += 1
        sheet_name = sheet.Name
        sheet_id = sheet.Id

        try:
            # --- Step 3: Get Viewports on the current Sheet ---
            viewport_ids = sheet.GetAllViewports()

            if not viewport_ids:
                # print("# Sheet '{}' (ID: {}) has no viewports.".format(sheet_name, sheet_id)) # Optional Debug
                continue

            # --- Step 4: Iterate through Viewports on the sheet ---
            for viewport_id in viewport_ids:
                processed_viewport_count += 1
                viewport = None
                view_element = None
                view_name = None

                try:
                    viewport = doc.GetElement(viewport_id)
                    if not viewport or not isinstance(viewport, Viewport):
                        # Should not happen if GetAllViewports is used, but good practice to check
                        errors.append("# Skipped: Element ID {} on Sheet '{}' is not a valid Viewport.".format(viewport_id, sheet_name))
                        continue

                    # --- Step 5: Get the associated View ---
                    view_id = viewport.ViewId
                    if view_id == ElementId.InvalidElementId:
                        skipped_no_view_count += 1
                        errors.append("# Skipped: Viewport ID {} on Sheet '{}' has no associated View ID.".format(viewport_id, sheet_name))
                        continue

                    view_element = doc.GetElement(view_id)
                    if not view_element or not isinstance(view_element, View):
                        skipped_no_view_count += 1
                        errors.append("# Skipped: Viewport ID {} on Sheet '{}' refers to an invalid View element (View ID: {}).".format(viewport_id, sheet_name, view_id))
                        continue

                    # --- Step 6: Check the View Name ---
                    try:
                        view_name = view_element.Name
                        if not view_name:
                            view_name = "Unnamed View ({})".format(view_id)

                    except Exception as name_ex:
                        failed_count += 1
                        errors.append("# Error getting name for View ID {}: {}".format(view_id, name_ex))
                        continue # Skip if we can't get the view name

                    # --- Step 7: Check if View Name contains the target substring ---
                    if target_substring in view_name:
                        # --- Step 8: Get and Modify the 'Show Label' Parameter ---
                        try:
                            # BuiltInParameter.VIEWPORT_ATTR_SHOW_LABEL corresponds to "Show Title" checkbox
                            show_label_param = viewport.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_SHOW_LABEL)

                            if show_label_param is None:
                                skipped_no_param_count += 1
                                errors.append("# Skipped: Viewport ID {} (View: '{}') on Sheet '{}' lacks 'VIEWPORT_ATTR_SHOW_LABEL' parameter.".format(viewport_id, view_name, sheet_name))
                                continue

                            # Check if parameter is read-only
                            if show_label_param.IsReadOnly:
                                skipped_readonly_count += 1
                                # Optionally check if the current value is already the target value
                                current_value = show_label_param.AsInteger()
                                if current_value != target_value:
                                    errors.append("# Skipped: Viewport ID {} (View: '{}') on Sheet '{}' 'Show Label' parameter is read-only. Cannot set to {}.".format(viewport_id, view_name, sheet_name, target_value == 0))
                                else:
                                    already_set_count += 1 # It's read-only but already has the desired value
                                continue

                            # Check current value before setting
                            current_value = show_label_param.AsInteger()
                            if current_value == target_value:
                                already_set_count += 1
                                continue # Already set correctly

                            # --- Step 9: Set the parameter value ---
                            success = show_label_param.Set(target_value) # 0 for False, 1 for True
                            if success:
                                modified_count += 1
                                # print("# Modified Viewport ID {} (View: '{}') on Sheet '{}': Set 'Show Label' to {}".format(viewport_id, view_name, sheet_name, target_value == 0)) # Optional verbose log
                            else:
                                # This might happen if Set fails for other reasons (e.g., validation)
                                failed_count += 1
                                errors.append("# Failed: Setting parameter for Viewport ID {} (View: '{}') on Sheet '{}' returned False.".format(viewport_id, view_name, sheet_name))

                        except System.ArgumentException as arg_ex:
                            failed_count += 1
                            error_msg = "# Set Parameter Error: Viewport ID {} (View: '{}') on Sheet '{}': {}. (Parameter: VIEWPORT_ATTR_SHOW_LABEL)".format(viewport_id, view_name, sheet_name, arg_ex.Message)
                            errors.append(error_msg)
                            print(error_msg) # Print immediate errors
                        except Exception as param_ex:
                            failed_count += 1
                            errors.append("# Error accessing/setting parameter for Viewport ID {} (View: '{}') on Sheet '{}': {}".format(viewport_id, view_name, sheet_name, param_ex))

                    else:
                        # View name does not contain the target substring
                        skipped_name_mismatch_count += 1

                except Exception as inner_ex:
                    # Catch unexpected errors during the processing loop for a single viewport
                    failed_count += 1
                    error_msg = "# Unexpected Error processing Viewport ID {} on Sheet '{}': {}".format(viewport_id, sheet_name, inner_ex)
                    errors.append(error_msg)
                    print(error_msg) # Print inner loop errors immediately

        except Exception as outer_ex:
            # Catch errors getting viewports for a sheet
            failed_count += 1
            error_msg = "# Error processing sheet '{}' (ID: {}): {}".format(sheet_name, sheet_id, outer_ex)
            errors.append(error_msg)
            print(error_msg) # Print outer loop errors immediately

    # --- Final Summary ---
    print("\n# --- Viewport 'Show Label' Modification Summary ---")
    print("# Sheets processed: {}".format(processed_sheet_count))
    print("# Viewports processed: {}".format(processed_viewport_count))
    print("# Viewports modified ('Show Label' set to {}): {}".format(target_value == 0, modified_count))
    print("# Viewports skipped (associated View name did not contain '{}'): {}".format(target_substring, skipped_name_mismatch_count))
    print("# Viewports skipped (parameter already had the target value): {}".format(already_set_count))
    print("# Viewports skipped (parameter was read-only): {}".format(skipped_readonly_count))
    print("# Viewports skipped (no valid associated View found): {}".format(skipped_no_view_count))
    print("# Viewports skipped (missing 'VIEWPORT_ATTR_SHOW_LABEL' parameter): {}".format(skipped_no_param_count))
    print("# Operations failed (errors during processing/setting): {}".format(failed_count))

    # # Optional: Print detailed errors if any occurred
    # if errors:
    #     print("\n# --- Encountered Issues/Errors ---")
    #     # Limit printing errors to avoid flooding console for large projects
    #     max_errors_to_print = 20
    #     for i, error in enumerate(errors):
    #         if i < max_errors_to_print:
    #             print(error)
    #         elif i == max_errors_to_print:
    #             print("# ... (additional errors hidden)")
    #             break