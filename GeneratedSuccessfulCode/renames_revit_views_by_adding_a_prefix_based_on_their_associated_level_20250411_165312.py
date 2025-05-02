# Purpose: This script renames Revit views by adding a prefix based on their associated level.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    View,
    ElementId,
    BuiltInParameter,
    ViewType # Keep ViewType in case specific view type logic is needed, though not currently used
)
import System # For Exception handling

# --- Configuration ---
target_level_name = "Level 1"
prefix = "L01_"

# --- Initialization ---
target_level_id = ElementId.InvalidElementId
renamed_count = 0
skipped_level_mismatch = 0
skipped_already_prefixed = 0
skipped_no_level = 0
skipped_template = 0
error_count = 0
processed_count = 0

# --- Step 1: Find Target Level ---
level_collector = FilteredElementCollector(doc).OfClass(Level)
target_level = None
# Use LINQ-like FirstOrDefault pattern for efficiency
for level in level_collector:
    if level.Name == target_level_name:
        target_level = level
        target_level_id = level.Id
        break

if not target_level:
    print("# Error: Level named '{}' not found in the document.".format(target_level_name))
    # Script will end here as the rest is inside the 'else' block
else:
    # --- Step 2 & 3: Collect and Filter Views ---
    # Use WhereElementIsNotElementType() to exclude View Types like ViewFamilyType
    view_collector = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType()

    for view in view_collector:
        processed_count += 1
        # Skip view templates
        if view.IsTemplate:
            skipped_template += 1
            continue

        associated_level_id = ElementId.InvalidElementId
        original_name = "Unknown" # Initialize for error context

        try:
            original_name = view.Name

            # Attempt to get the level associated with the view
            # Method 1: GenLevel property (often works for Sections, Elevations, Plans)
            view_gen_level = None
            try:
                # Accessing GenLevel can sometimes throw exceptions on certain view types
                view_gen_level = view.GenLevel
            except Exception as e_get_genlevel:
                # Silently ignore if GenLevel property access fails, proceed to parameter check
                # print("# Debug: Failed to get GenLevel for view '{}' (ID: {}): {}".format(original_name, view.Id, e_get_genlevel)) # Optional debug
                pass

            if view_gen_level and view_gen_level.Id != ElementId.InvalidElementId:
                associated_level_id = view_gen_level.Id
            else:
                # Method 2: Specific Plan View Level Parameter (if GenLevel failed or wasn't valid)
                try:
                    level_param = view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL)
                    # Check if parameter exists, has a value, and the value is a valid ElementId
                    if level_param and level_param.HasValue:
                        param_level_id = level_param.AsElementId()
                        if param_level_id and param_level_id != ElementId.InvalidElementId:
                            associated_level_id = param_level_id
                except Exception as e_planlvl:
                    # Silently ignore parameter access errors
                    # print("# Debug: Failed to get PLAN_VIEW_LEVEL for view '{}' (ID: {}): {}".format(original_name, view.Id, e_planlvl)) # Optional debug
                    pass # No level found via this method either

            # --- Step 4: Check Level and Rename ---
            if associated_level_id != ElementId.InvalidElementId:
                # Check if the found level matches the target level
                if associated_level_id == target_level_id:
                    # Level matches, proceed with rename check
                    if not original_name.startswith(prefix):
                        new_name = prefix + original_name
                        try:
                            # Perform the rename operation
                            view.Name = new_name
                            renamed_count += 1
                            # print("# Renamed view '{}' to '{}'".format(original_name, new_name)) # Optional debug
                        except System.ArgumentException as arg_ex:
                            # Handle specific error for duplicate names
                            error_count += 1
                            print("# Error renaming view '{}' (ID: {}): {}. New name '{}' might already exist.".format(original_name, view.Id, arg_ex.Message, new_name))
                        except Exception as e_rename:
                            # Handle other potential renaming errors
                            error_count += 1
                            print("# Unexpected error renaming view '{}' (ID: {}): {}".format(original_name, view.Id, e_rename))
                    else:
                        # Skip because the prefix already exists
                        skipped_already_prefixed += 1
                        # print("# Skipping view '{}' (ID: {}), already prefixed.".format(original_name, view.Id)) # Optional debug
                else:
                    # View has a level, but it's not the target level
                    skipped_level_mismatch += 1
                    # print("# Skipping view '{}' (ID: {}), associated level ID {} != target ID {}.".format(original_name, view.Id, associated_level_id, target_level_id)) # Optional debug
            else:
                # View does not seem to have an associated level based on checked methods
                skipped_no_level += 1
                # print("# Skipping view '{}' (ID: {}), no associated level found.".format(original_name, view.Id)) # Optional debug

        except Exception as e_outer:
            # Catch errors during accessing view name or other properties
            error_count += 1
            print("# Error processing view (ID: {}), original name may be '{}': {}".format(view.Id, original_name, e_outer))

    # --- Optional Summary Output (Commented out) ---
    # print("--- View Renaming Summary ---")
    # print("Target Level: '{}' (ID: {})".format(target_level_name, target_level_id))
    # print("Prefix Applied: '{}'".format(prefix))
    # print("-----------------------------")
    # print("Total Views Processed (excluding templates): {}".format(processed_count - skipped_template))
    # print("Successfully Renamed: {}".format(renamed_count))
    # print("Skipped (Already Prefixed): {}".format(skipped_already_prefixed))
    # print("Skipped (Different Level): {}".format(skipped_level_mismatch))
    # print("Skipped (No Associated Level Found): {}".format(skipped_no_level))
    # print("Skipped (View Templates): {}".format(skipped_template))
    # print("Errors Encountered: {}".format(error_count))
    # print("-----------------------------")

# Ensure output for level not found case is printed if applicable
# (Handled by the initial if/else structure)