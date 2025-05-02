# Purpose: This script updates the 'Mark' parameter of windows on a specific Revit level with a sequential prefix.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Level,
    FamilyInstance, # Windows are typically FamilyInstances
    Element, # Use Element for broader type checking if needed, but FamilyInstance is more specific
    ElementId,
    BuiltInParameter,
    Parameter
)

# --- Configuration ---
target_level_name = "Level 2"
mark_prefix = "W-"
start_number = 201
target_parameter = BuiltInParameter.ALL_MODEL_MARK # 'Mark' parameter for instances

# --- Initialization ---
target_level_id = ElementId.InvalidElementId
updated_count = 0
skipped_level_mismatch = 0
skipped_not_instance = 0
skipped_no_param = 0
skipped_read_only = 0
error_count = 0
counter = start_number # Initialize sequential counter

# --- Step 1: Find Target Level ---
level_collector = FilteredElementCollector(doc).OfClass(Level)
target_level = None
# Find the level by name
for level in level_collector:
    if level.Name == target_level_name:
        target_level = level
        target_level_id = level.Id
        break

if target_level_id == ElementId.InvalidElementId:
    print("# Error: Level named '{}' not found in the document.".format(target_level_name))
    # No further action possible if level not found
else:
    # --- Step 2 & 3: Collect and Filter Windows ---
    # Use WhereElementIsNotElementType() to get instances
    window_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()

    # Filter windows that are hosted on the target level
    windows_on_target_level = []
    total_windows_checked = 0
    for window in window_collector:
        total_windows_checked += 1
        # Ensure it's a FamilyInstance to access LevelId reliably
        if isinstance(window, FamilyInstance):
            try:
                window_level_id = window.LevelId
                if window_level_id == target_level_id:
                    windows_on_target_level.append(window)
                else:
                    skipped_level_mismatch += 1
            except Exception as e_level:
                # Handle cases where LevelId might not be accessible
                error_count += 1
                print("# Error checking level for element ID {}: {}".format(window.Id, e_level))
                skipped_level_mismatch += 1 # Treat as mismatch if level check fails
        else:
            # If somehow a non-FamilyInstance gets through the filter
            skipped_not_instance += 1
            skipped_level_mismatch += 1 # Also count as level mismatch for simplicity

    # --- Step 4 & 5: Update Mark Parameter ---
    if not windows_on_target_level:
        print("# Info: No windows found on level '{}'.".format(target_level_name))
    else:
        # Optional: Sort windows if consistent numbering is critical (e.g., by location or ID)
        # Sorting by ElementId provides a consistent order run-to-run
        # windows_on_target_level.sort(key=lambda w: w.Id.IntegerValue)

        for window in windows_on_target_level:
            try:
                mark_param = window.get_Parameter(target_parameter)

                if mark_param is None:
                    skipped_no_param += 1
                    # print("# Info: Window ID {} does not have parameter '{}'. Skipping.".format(window.Id, target_parameter)) # Debug
                    continue

                if mark_param.IsReadOnly:
                    skipped_read_only += 1
                    # print("# Info: Parameter '{}' for Window ID {} is read-only. Skipping.".format(target_parameter, window.Id)) # Debug
                    continue

                # Construct the new sequential Mark value
                new_mark = mark_prefix + str(counter)

                # Set the new value for the Mark parameter
                # The Set method requires a string for Text parameters like Mark
                set_result = mark_param.Set(new_mark)

                if set_result:
                    updated_count += 1
                    counter += 1 # Increment counter only on successful update
                    # print("# Updated Mark for Window ID {} to '{}'".format(window.Id, new_mark)) # Debug
                else:
                    # This case might happen if the value is disallowed (e.g., duplicate mark if enforced)
                    error_count += 1
                    print("# Error: Failed to set Mark for Window ID {} to '{}'. Parameter.Set returned False.".format(window.Id, new_mark))

            except SystemException as param_ex:
                error_count += 1
                print("# Error processing Window ID {}: {}".format(window.Id, param_ex.Message))

        # --- Final Summary --- (Optional: uncomment if needed)
        # print("# --- Window Mark Update Summary ---")
        # print("# Target Level: '{}' (ID: {})".format(target_level_name, target_level_id))
        # print("# Total Windows Checked: {}".format(total_windows_checked))
        # print("# Windows Found on Level: {}".format(len(windows_on_target_level)))
        # print("# Successfully Updated: {}".format(updated_count))
        # print("# Skipped (Not on Target Level): {}".format(skipped_level_mismatch))
        # print("# Skipped (Not FamilyInstance): {}".format(skipped_not_instance))
        # print("# Skipped (No Mark Param): {}".format(skipped_no_param))
        # print("# Skipped (Mark Read-Only): {}".format(skipped_read_only))
        # print("# Errors Encountered: {}".format(error_count))
        # if error_count > 0:
        #     print("# Review errors printed above for details.")

# Ensure output for level not found case is printed if applicable (handled by the initial if/else)