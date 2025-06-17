# Purpose: This script adds a suffix to Revit level names based on their elevation relative to a specified level.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for System.StringComparison
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ElementId
)
import System # Needed for String comparison methods like EndsWith

# --- Script Core Logic ---

# Suffix to append
suffix = "_Roof Structure"
reference_level_name = "Level 5"

# Find the reference level "Level 5"
level_5 = None
level_5_elevation = None
# Use FilteredElementCollector to find the specific level by name
collector = FilteredElementCollector(doc).OfClass(Level)
# Iterate through levels to find the reference level
for lvl in collector:
    # Compare names, ensuring it's an exact match
    if lvl.Name == reference_level_name:
        level_5 = lvl
        level_5_elevation = lvl.Elevation
        # print("# Found reference level '{}' (ID: {}) at elevation {}".format(level_5.Name, level_5.Id, level_5_elevation)) # Debug
        break # Found the level, stop searching

renamed_count = 0
skipped_already_suffixed = 0
skipped_not_above = 0
error_count = 0
processed_count = 0

if level_5 is None:
    # If the reference level is not found, print a message (or handle as needed)
    print("# Error: Reference level '{}' not found in the project. Cannot perform renaming.".format(reference_level_name))
else:
    # If reference level found, proceed with renaming other levels
    # Get all levels again or convert the previous collector to a list
    all_levels = list(FilteredElementCollector(doc).OfClass(Level))
    processed_count = len(all_levels)

    for level in all_levels:
        try:
            # Skip the reference level itself
            if level.Id == level_5.Id:
                skipped_not_above += 1
                continue

            current_name = level.Name
            current_elevation = level.Elevation

            # Check 1: Is the level's elevation strictly greater than Level 5's elevation?
            is_above_level_5 = current_elevation > level_5_elevation

            # Check 2: Does the name already end with the suffix?
            # Use System.String.EndsWith for a case-sensitive check (Ordinal)
            already_has_suffix = current_name.EndsWith(suffix, System.StringComparison.Ordinal)

            if is_above_level_5:
                if not already_has_suffix:
                    new_name = current_name + suffix
                    try:
                        # Rename the level
                        level.Name = new_name
                        renamed_count += 1
                        # print("# Renamed Level '{}' (ID: {}) to '{}'".format(current_name, level.Id, new_name)) # Debug
                    except Exception as rename_ex:
                        # print("# Error renaming Level '{}' (ID: {}) to '{}': {}".format(current_name, level.Id, new_name, rename_ex)) # Debug
                        error_count += 1
                else:
                    # print("# Skipped Level '{}' (ID: {}): Already has suffix '{}'.".format(current_name, level.Id, suffix)) # Debug
                    skipped_already_suffixed += 1
            else:
                # print("# Skipped Level '{}' (ID: {}): Not above {} elevation ({} <= {}).".format(current_name, level.Id, reference_level_name, current_elevation, level_5_elevation)) # Debug
                skipped_not_above += 1

        except Exception as ex:
            # Catch any other errors during processing of a level
            # print("# Error processing Level '{}' (ID: {}): {}".format(level.Name if level else 'Unknown', level.Id if level else 'Unknown', ex)) # Debug
            error_count += 1

# Optional: Print summary to the console/log (commented out by default)
# if level_5:
#    print("--- Level Renaming Summary ---")
#    print("Reference Level '{}' Elevation: {:.2f}".format(reference_level_name, level_5_elevation))
#    print("Successfully renamed: {}".format(renamed_count))
#    print("Skipped (Already had suffix): {}".format(skipped_already_suffixed))
#    print("Skipped (Not above {} elevation): {}".format(reference_level_name, skipped_not_above))
#    print("Errors encountered: {}".format(error_count))
#    print("Total Levels processed: {}".format(processed_count))