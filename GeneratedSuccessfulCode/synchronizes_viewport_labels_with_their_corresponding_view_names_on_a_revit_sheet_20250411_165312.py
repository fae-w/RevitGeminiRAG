# Purpose: This script synchronizes viewport labels with their corresponding view names on a Revit sheet.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, Viewport, ViewSheet, View, ElementId, BuiltInParameter
import System # For Exception handling

# --- Initialization ---
processed_count = 0
renamed_count = 0
skipped_readonly_count = 0
skipped_no_view_count = 0
skipped_no_param_count = 0
failed_count = 0
errors = []

# --- Step 1: Get the Active Sheet ---
active_view = uidoc.ActiveView
if not isinstance(active_view, ViewSheet):
    print("# Error: The active view is not a sheet. Please open a sheet view and run the script again.")
else:
    active_sheet = active_view
    active_sheet_id = active_sheet.Id
    print("# Processing Viewports on active sheet: '{}' (ID: {})".format(active_sheet.Name, active_sheet_id))

    # --- Step 2: Collect all Viewports on the active sheet ---
    viewport_collector = FilteredElementCollector(doc, active_sheet_id).OfClass(Viewport)
    all_viewports = list(viewport_collector) # Convert iterator to list for counting

    if not all_viewports:
        print("# No Viewports found on the active sheet.")
    else:
        print("# Found {} Viewports on the sheet. Attempting to rename based on their View Name...".format(len(all_viewports)))

        # --- Step 3: Iterate through Viewports and attempt rename ---
        for viewport in all_viewports:
            processed_count += 1
            viewport_id_str = viewport.Id.ToString()
            view_name = None
            view_id = ElementId.InvalidElementId

            try:
                # --- Step 4: Get the associated View ---
                view_id = viewport.ViewId
                if view_id == ElementId.InvalidElementId:
                    skipped_no_view_count += 1
                    errors.append("# Skipped: Viewport ID {} does not have an associated View ID.".format(viewport_id_str))
                    continue

                view_element = doc.GetElement(view_id)
                if not view_element or not isinstance(view_element, View):
                    skipped_no_view_count += 1
                    errors.append("# Skipped: Viewport ID {} refers to an invalid or non-View element (View ID: {}).".format(viewport_id_str, view_id))
                    continue

                # --- Step 5: Get the View Name ---
                try:
                    view_name = view_element.Name
                    if not view_name: # Handle potential empty names, though unlikely for views
                         view_name = "Unnamed View ({})".format(view_id)
                         # print("# Warning: View ID {} has an empty name.".format(view_id)) # Optional Warning
                except Exception as name_ex:
                    failed_count += 1
                    errors.append("# Error getting name for View ID {}: {}".format(view_id, name_ex))
                    continue # Skip if we can't get the view name

                # --- Step 6: Get the Viewport's "View Name" parameter ---
                # This parameter controls the label text displayed on the sheet for the view name.
                # Note: This is DIFFERENT from the Viewport element's own Name property.
                try:
                    name_param = viewport.get_Parameter(BuiltInParameter.VIEWPORT_VIEW_NAME)

                    if name_param is None:
                        skipped_no_param_count += 1
                        errors.append("# Skipped: Viewport ID {} does not have the 'VIEWPORT_VIEW_NAME' parameter.".format(viewport_id_str))
                        continue

                    # --- Step 7: Check if the parameter is read-only ---
                    if name_param.IsReadOnly:
                        skipped_readonly_count += 1
                        # Optional: Check if the current value already matches
                        current_vp_name = name_param.AsString()
                        if current_vp_name != view_name:
                             errors.append("# Skipped: Viewport ID {} 'VIEWPORT_VIEW_NAME' parameter is read-only. Cannot set to '{}'. Current value: '{}'".format(viewport_id_str, view_name, current_vp_name))
                        continue

                    # --- Step 8: Set the Viewport's parameter to the View's Name ---
                    # Only set if different to avoid unnecessary changes
                    current_vp_name_val = name_param.AsString()
                    if current_vp_name_val != view_name:
                        try:
                            # THE ACTUAL RENAMING ACTION (setting the parameter)
                            success = name_param.Set(view_name)
                            if success:
                                renamed_count += 1
                                # print("# Renamed Viewport ID {} label to '{}'".format(viewport_id_str, view_name)) # Optional verbose log
                            else:
                                # This might happen if Set fails for other reasons (e.g., validation)
                                failed_count += 1
                                errors.append("# Failed: Setting parameter 'VIEWPORT_VIEW_NAME' for Viewport ID {} to '{}' returned False.".format(viewport_id_str, view_name))
                        except System.ArgumentException as arg_ex:
                            # Handle specific errors like invalid characters or other constraints
                            failed_count += 1
                            error_msg = "# Rename Error (Parameter Set): Viewport ID {} to '{}': {}. (Parameter: VIEWPORT_VIEW_NAME)".format(viewport_id_str, view_name, arg_ex.Message)
                            errors.append(error_msg)
                            print(error_msg) # Print immediate errors
                        except Exception as set_ex:
                            failed_count += 1
                            error_msg = "# Rename Error (Parameter Set): Viewport ID {} to '{}': {}. (Parameter: VIEWPORT_VIEW_NAME)".format(viewport_id_str, view_name, set_ex)
                            errors.append(error_msg)
                            print(error_msg) # Print immediate errors
                    # else: # Value already matches, do nothing
                    #     pass

                except Exception as param_ex:
                     failed_count += 1
                     errors.append("# Error accessing parameter for Viewport ID {}: {}".format(viewport_id_str, param_ex))

            except Exception as outer_ex:
                 # Catch unexpected errors during the processing loop for a viewport
                 failed_count += 1
                 error_msg = "# Unexpected Error processing Viewport ID {}: {}".format(viewport_id_str, outer_ex)
                 errors.append(error_msg)
                 print(error_msg) # Print outer loop errors immediately

        # --- Final Summary ---
        print("\n# --- Viewport Label Renaming Summary ---")
        print("# Total Viewports found on sheet: {}".format(len(all_viewports)))
        print("# Viewports processed: {}".format(processed_count))
        print("# Viewport labels successfully set to match View Name: {}".format(renamed_count))
        print("# Viewports skipped (parameter was read-only): {}".format(skipped_readonly_count))
        print("# Viewports skipped (no valid associated View found): {}".format(skipped_no_view_count))
        print("# Viewports skipped (missing 'VIEWPORT_VIEW_NAME' parameter): {}".format(skipped_no_param_count))
        print("# Viewports failed during processing/parameter setting: {}".format(failed_count))

        # # Optional: Print detailed errors if any occurred
        # if errors:
        #     print("\n# --- Encountered Issues/Errors ---")
        #     for error in errors:
        #         print(error)