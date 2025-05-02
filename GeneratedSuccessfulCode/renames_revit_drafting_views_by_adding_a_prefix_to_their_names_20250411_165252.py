# Purpose: This script renames Revit drafting views by adding a prefix to their names.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewType,
    ViewDrafting # Directly filter for drafting views
)
import System # For Exception handling

# --- Configuration ---
prefix = "DET_"

# --- Initialization ---
renamed_count = 0
skipped_count = 0
error_count = 0

# --- Step 1: Collect Drafting Views ---
# Use OfClass(ViewDrafting) for efficiency and correctness
collector = FilteredElementCollector(doc).OfClass(ViewDrafting)

# Filter out View Templates explicitly if needed, though OfClass(ViewDrafting)
# should generally not return templates. Better safe than sorry.
drafting_views = [v for v in collector if not v.IsTemplate]

# --- Step 2: Iterate and Rename Drafting Views ---
for view in drafting_views:
    original_name = "" # Initialize for error handling context
    try:
        original_name = view.Name

        # Check if the name already starts with the desired prefix (case-sensitive)
        if not original_name.startswith(prefix):
            # Construct the new name
            new_name = prefix + original_name

            try:
                # Attempt to rename the view
                view.Name = new_name
                renamed_count += 1
                # print("# Renamed view '{}' to '{}'".format(original_name, new_name)) # Debug comment
            except System.ArgumentException as arg_ex:
                # Handle potential errors like duplicate names
                error_count += 1
                print("# Error renaming view '{}' (ID: {}): {}. New name '{}' might already exist.".format(original_name, view.Id, arg_ex.Message, new_name))
            except Exception as e_rename:
                # Handle other potential errors during renaming
                error_count += 1
                print("# Unexpected error renaming view '{}' (ID: {}): {}".format(original_name, view.Id, e_rename))
        else:
            # Name already starts with the prefix, skip renaming
            skipped_count += 1
            # print("# Skipping view '{}' as it already starts with '{}'".format(original_name, prefix)) # Debug comment

    except Exception as e_outer:
        # Handle potential errors accessing view properties like Name
        error_count += 1
        print("# Error processing view (ID: {}), original name may be unknown: {}".format(view.Id, e_outer))

# Optional: Print summary to RevitPythonShell output (comment out if not desired)
# print("--- Drafting View Renaming Summary ---")
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (already prefixed): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Drafting Views processed: {}".format(renamed_count + skipped_count + error_count))