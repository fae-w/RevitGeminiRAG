# Purpose: This script renames Revit view templates by removing suffixes like '(1)'.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ElementId # Good practice, though not explicitly used for renaming here
)
import System # For Exception handling
import re # For regular expressions to find suffixes

# --- Configuration ---
# Regular expression to find suffixes like '(1)', '(2)', etc. at the end of the string.
# Allows for optional whitespace before the parenthesis.
# Example matches: "My Template (1)", "My Template(1)", "My Template   (123)"
suffix_pattern = re.compile(r'\s*\(\d+\)$')

# --- Initialization ---
renamed_count = 0
skipped_no_suffix_count = 0
error_count = 0
processed_templates_count = 0

# --- Step 1: Collect all Views ---
collector = FilteredElementCollector(doc).OfClass(View)

# --- Step 2: Iterate and Rename View Templates ---
for view in collector:
    # Check if the view is a template
    if view.IsTemplate:
        processed_templates_count += 1
        original_name = "Unknown" # Default for error messages
        try:
            original_name = view.Name
            # Strip trailing whitespace from the name before checking the pattern
            name_to_check = original_name.rstrip()

            # --- Step 3: Check for the defined suffix pattern ---
            match = suffix_pattern.search(name_to_check)

            if match:
                # --- Step 4: Extract base name and clean it ---
                # Get the part of the string before the matched suffix
                base_name = name_to_check[:match.start()]
                # Strip potential leading/trailing whitespace from the resulting base name
                new_name = base_name.strip()

                # --- Step 5: Check if renaming is necessary ---
                # Ensure the new name is not empty and is actually different from the original name
                if new_name and new_name != original_name:
                    # print("# Attempting rename: Original='{}', New='{}'".format(original_name, new_name)) # Debug: Escaped braces
                    try:
                        # --- Step 6: Attempt to rename the view template ---
                        view.Name = new_name
                        renamed_count += 1
                        # print("# Renamed view template '{}' to '{}' (ID: {})".format(original_name, new_name, view.Id)) # Debug: Escaped braces
                    except System.ArgumentException as arg_ex:
                        # Handle potential errors like duplicate names
                        error_count += 1
                        print("# Error renaming view template '{0}' (ID: {1}) to '{2}': {3}. New name might already exist or be invalid.".format(original_name, view.Id, new_name, arg_ex.Message)) # Escaped braces
                    except Exception as e:
                        # Handle other potential errors during renaming
                        error_count += 1
                        print("# Error renaming view template '{0}' (ID: {1}) to '{2}': {3}".format(original_name, view.Id, new_name, e)) # Escaped braces
                elif not new_name:
                    # Handle cases where removing the suffix leaves an empty string (unlikely but possible)
                    skipped_no_suffix_count += 1
                    # print("# Skipping view template '{}' (ID: {}): Resulting name would be empty.".format(original_name, view.Id)) # Debug: Escaped braces
                else:
                    # Name didn't change after removing suffix and stripping whitespace (e.g., original was "Base Name " and suffix was "(1)")
                    skipped_no_suffix_count += 1 # Count as skipped as no rename operation occurred
                    # print("# Skipping view template '{}' (ID: {}): Name unchanged after suffix removal/strip.".format(original_name, view.Id)) # Debug: Escaped braces
            else:
                # The view template name does not end with the specified suffix pattern
                skipped_no_suffix_count += 1
                # print("# Skipping view template '{}' (ID: {}): No matching suffix found.".format(original_name, view.Id)) # Debug: Escaped braces

        except Exception as outer_ex:
            # Handle unexpected errors during processing of a specific view template
            error_count += 1
            print("# Unexpected error processing view template '{0}' (ID: {1}): {2}".format(original_name, view.Id, outer_ex)) # Escaped braces

# Optional: Print summary (comment out if not desired)
# print("\n# --- View Template Suffix Removal Summary ---")
# print("# Total View Templates processed: {}".format(processed_templates_count)) # Escaped braces
# print("# Successfully renamed: {}".format(renamed_count)) # Escaped braces
# print("# Skipped (no matching suffix or no change needed): {}".format(skipped_no_suffix_count)) # Escaped braces
# print("# Errors encountered: {}".format(error_count)) # Escaped braces