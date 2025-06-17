# Purpose: This script replaces a specified character in Revit level names.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, Level

# --- Script Core Logic ---

# Character to find and replace
char_to_find = '.'
char_to_replace = '_'

# Collect all Level elements in the project
collector = FilteredElementCollector(doc).OfClass(Level)

# Convert iterator to a list to avoid potential modification issues during iteration
levels_to_process = list(collector)

renamed_count = 0
skipped_count = 0
error_count = 0

for level in levels_to_process:
    if not isinstance(level, Level):
        # Should not happen with OfClass(Level), but good practice
        continue

    try:
        current_name = level.Name
        if not current_name:
            # Skip levels with no name or empty name
            skipped_count += 1
            continue

        # Check if the character to find exists in the name
        if char_to_find in current_name:
            # Perform the replacement
            new_name = current_name.replace(char_to_find, char_to_replace)

            # Only rename if the name actually changed
            if new_name != current_name:
                try:
                    # Attempt to set the new name
                    level.Name = new_name
                    renamed_count += 1
                    # print("# Renamed Level ID {} from '{}' to '{}'".format(level.Id, current_name, new_name)) # Debug
                except Exception as rename_ex:
                    # Catch potential errors during the rename operation (e.g., duplicate name)
                    # print("# Error renaming Level ID {}: {}".format(level.Id, rename_ex)) # Debug
                    error_count += 1
            else:
                # This case should technically not be hit if char_to_find was in current_name,
                # but included for completeness.
                skipped_count += 1
        else:
            # The character was not found, no rename needed
            skipped_count += 1
            # print("# Skipped Level ID {}: Name '{}' does not contain '{}'".format(level.Id, current_name, char_to_find)) # Debug

    except Exception as e:
        # Catch any other errors during processing a specific level
        # print("# Error processing Level ID {}: {}".format(level.Id, e)) # Debug
        error_count += 1

# Optional: Print summary (commented out by default)
# print("--- Level Renaming Summary ---")
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (no change needed or no name): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Levels processed: {}".format(len(levels_to_process)))