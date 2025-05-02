# Purpose: This script renames orphaned Revit floor plan views that are not associated with a level.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewPlan,
    ViewType,
    Level,
    ElementId,
    BuiltInParameter
)
import System # For Exception handling

# --- Initialization ---
orphan_counter = 1
renamed_count = 0
skipped_associated = 0
skipped_not_floorplan = 0
skipped_template = 0
error_count = 0

# --- Script Core Logic ---

# Collect ViewPlan elements (potential floor plans)
collector = FilteredElementCollector(doc).OfClass(ViewPlan)

# Iterate through the collected views
for view in collector:
    # 1. Filter: Check if it's a Floor Plan and not a template
    if view.ViewType != ViewType.FloorPlan:
        skipped_not_floorplan += 1
        continue
    if view.IsTemplate:
        skipped_template += 1
        continue

    # 2. Check Level Association
    is_associated_with_level = False
    try:
        level_param = view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL)
        # Check if parameter exists, has a value, and the value is a valid ElementId
        if level_param and level_param.HasValue:
            level_id = level_param.AsElementId()
            # Check if the ID is valid and not the 'invalid' ElementId
            if level_id and level_id != ElementId.InvalidElementId:
                # Optional but recommended: Verify the ID actually points to a Level element
                level_element = doc.GetElement(level_id)
                if level_element and isinstance(level_element, Level):
                    is_associated_with_level = True
                    # print(f"# Debug: View '{view.Name}' (ID: {view.Id}) is associated with Level ID {level_id}") # Escaped Debug
                # else: # Debugging case where ID exists but element doesn't or isn't a Level
                    # print(f"# Debug: View '{view.Name}' (ID: {view.Id}) has Level ID {level_id}, but GetElement returned {level_element}") # Escaped Debug
                    # This case is treated as 'not associated'

    except Exception as e_check:
        # Log error during check, treat as 'not associated' for safety
        # print(f"# Warning: Error checking level association for view '{view.Name}' (ID: {view.Id}): {e_check}") # Escaped Debug
        error_count += 1 # Count errors during the check phase
        # Continue to next view if check fails critically? Or assume orphaned? Let's assume orphaned.
        is_associated_with_level = False # Ensure it's false if check failed

    # 3. Rename if NOT associated with a level
    if not is_associated_with_level:
        original_name = view.Name
        new_name_base = "ORPHANED_PLAN"
        # Try to generate a unique name using a counter
        rename_attempt_successful = False
        max_attempts = 1000 # Limit attempts to avoid infinite loops if naming scheme fails
        current_attempt = 0
        while not rename_attempt_successful and current_attempt < max_attempts:
            new_name = "{}_{:03d}".format(new_name_base, orphan_counter)
            if new_name == original_name: # Skip if name already matches pattern (unlikely but possible)
                 # print(f"# Skipping view '{original_name}' (ID: {view.Id}), already named correctly.") # Escaped Debug
                 break # Exit the while loop for this view

            try:
                # Perform the rename operation
                view.Name = new_name
                renamed_count += 1
                orphan_counter += 1 # Increment counter only on successful rename
                rename_attempt_successful = True
                # print(f"# Renamed orphaned view '{original_name}' (ID: {view.Id}) to '{new_name}'") # Escaped Debug
            except System.ArgumentException as arg_ex:
                # Handle potential duplicate name errors by incrementing counter and trying again
                # print(f"# Info: Name '{new_name}' likely exists. Trying next counter for view '{original_name}'. Error: {arg_ex.Message}") # Escaped Debug
                orphan_counter += 1
                current_attempt += 1
            except Exception as e_rename:
                # Handle other potential renaming errors
                # print(f"# Error renaming view '{original_name}' (ID: {view.Id}) to '{new_name}': {e_rename}") # Escaped Debug
                error_count += 1
                break # Stop trying to rename this view if a non-duplicate error occurs

        if not rename_attempt_successful and current_attempt >= max_attempts:
            # print(f"# Error: Could not find a unique name for orphaned view '{original_name}' (ID: {view.Id}) after {max_attempts} attempts.") # Escaped Debug
            error_count += 1
    else:
        # Skip because it IS associated with a level
        skipped_associated += 1
        # print(f"# Skipping view '{view.Name}' (ID: {view.Id}) as it is associated with a level.") # Escaped Debug


# Optional: Print summary to RevitPythonShell output (comment out if not desired)
# print("--- Orphaned Floor Plan Renaming Summary ---")
# print(f"Successfully renamed: {renamed_count}") # Escaped
# print(f"Skipped (Associated with Level): {skipped_associated}") # Escaped
# print(f"Skipped (Not FloorPlan Type): {skipped_not_floorplan}") # Escaped
# print(f"Skipped (View Template): {skipped_template}") # Escaped
# print(f"Errors encountered (check or rename): {error_count}") # Escaped
# print(f"Total ViewPlans processed: {len(list(collector))}") # Escaped