# Purpose: This script renames Revit views by replacing a specific string in their names.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View
)
import System # For Exception handling

# --- Configuration ---
search_string = 'Copy 1'
replace_string = '_Duplicate'

# --- Initialization ---
renamed_count = 0
skipped_count = 0
error_count = 0

# --- Step 1: Collect Views ---
# Use OfClass(View) to get all view types
collector = FilteredElementCollector(doc).OfClass(View)

# Filter out View Templates explicitly
# Also filter out non-view elements that might sneak through OfClass(View) in some cases
# although OfClass should be reliable here. Checking IsTemplate is crucial.
views_to_process = [v for v in collector if isinstance(v, View) and not v.IsTemplate]

# --- Step 2: Iterate and Rename Views ---
for view in views_to_process:
    original_name = "" # Initialize for error handling context
    try:
        original_name = view.Name

        # Check if the name contains the search string (case-sensitive)
        if search_string in original_name:
            # Construct the new name by replacing the search string
            new_name = original_name.replace(search_string, replace_string)

            # Avoid renaming if the new name is the same as the old (unlikely but possible)
            # or if the new name is empty (safety check)
            if new_name != original_name and new_name:
                try:
                    # Attempt to rename the view
                    view.Name = new_name
                    renamed_count += 1
                    # print("# Renamed view '{{}}' to '{{}}'".format(original_name, new_name)) # Optional debug output
                except System.ArgumentException as arg_ex:
                    # Handle potential errors like duplicate names or invalid characters
                    error_count += 1
                    print("# Error renaming view '{{}}' (ID: {{}}): {{}}. New name '{{}}' might already exist or be invalid.".format(original_name, view.Id, arg_ex.Message, new_name))
                except Exception as e_rename:
                    # Handle other potential errors during renaming
                    error_count += 1
                    print("# Unexpected error renaming view '{{}}' (ID: {{}}): {{}}".format(original_name, view.Id, e_rename))
            else:
                # Name contained string but replacement resulted in same name or empty name
                skipped_count += 1
                # print("# Skipping view '{{}}' as replacement resulted in no change or empty name.".format(original_name)) # Optional debug output
        else:
            # Name does not contain the search string, skip renaming
            skipped_count += 1
            # print("# Skipping view '{{}}' as it does not contain '{{}}'".format(original_name, search_string)) # Optional debug output

    except Exception as e_outer:
        # Handle potential errors accessing view properties like Name
        error_count += 1
        print("# Error processing view (ID: {{}}), original name may be unknown: {{}}".format(view.Id, e_outer))

# Optional: Print summary to RevitPythonShell output (comment out if not desired)
# print("--- View Renaming ('{{}}' -> '{{}}') Summary ---".format(search_string, replace_string))
# print("Successfully renamed: {{}}".format(renamed_count))
# print("Skipped (no change needed): {{}}".format(skipped_count))
# print("Errors encountered: {{}}".format(error_count))
# print("Total Views processed: {{}}".format(len(views_to_process)))