# Purpose: This script renames Revit view templates by adding a prefix to names containing a specific search string.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ElementId # Although not explicitly used for renaming, good practice
)
import System # For Exception handling

# --- Configuration ---
search_string = "Architectural" # Case-sensitive search string
new_prefix = "ARCH - "

# --- Initialization ---
renamed_count = 0
error_count = 0
already_correct_count = 0 # Count templates that already start with the prefix
skipped_count = 0 # Count templates that don't contain the search string

# --- Step 1: Collect all Views ---
collector = FilteredElementCollector(doc).OfClass(View)

# --- Step 2: Iterate and Rename View Templates ---
for view in collector:
    # Check if the view is a template
    if view.IsTemplate:
        try:
            original_name = view.Name

            # Check if the name contains the search string (case-sensitive)
            if search_string in original_name:
                # Construct the new name
                new_name = new_prefix + original_name

                # Check if renaming is necessary (avoids unnecessary operations)
                if original_name != new_name:
                    # Attempt to rename the view template
                    view.Name = new_name
                    renamed_count += 1
                    # print("# Renamed view template '{{}}' to '{{}}' (ID: {{}})".format(original_name, new_name, view.Id)) # Debug
                else:
                    # Already has the desired prefix/name structure (perhaps from a previous run or manual naming)
                    already_correct_count += 1
                    # print("# View template '{{}}' already follows the naming pattern.".format(original_name)) # Debug
            else:
                # Does not contain the search string, skip renaming
                skipped_count += 1
                # print("# Skipping view template '{{}}' as it does not contain '{{}}'".format(original_name, search_string)) # Debug

        except System.ArgumentException as arg_ex:
            # Handle potential errors like duplicate names
            error_count += 1
            print("# Error renaming view template '{{}}' (ID: {{}}): {{}}. New name might already exist.".format(original_name, view.Id, arg_ex.Message))
        except Exception as e:
            # Handle other potential errors during renaming
            error_count += 1
            print("# Unexpected error processing view template '{{}}' (ID: {{}}): {{}}".format(original_name, view.Id, e))

# Optional: Print summary (comment out if not desired)
# print("--- View Template Renaming Summary ---")
# print("Successfully renamed: {{}}".format(renamed_count))
# print("Already had correct format: {{}}".format(already_correct_count))
# print("Skipped (did not contain '{{}}'): {{}}".format(search_string, skipped_count))
# print("Errors encountered: {{}}".format(error_count))
# print("Total View Templates processed: {{}}".format(renamed_count + already_correct_count + skipped_count + error_count))