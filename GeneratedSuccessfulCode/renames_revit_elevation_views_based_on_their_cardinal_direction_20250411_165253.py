# Purpose: This script renames Revit elevation views based on their cardinal direction.

﻿# Mandatory Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewType,
    XYZ,
    ElementId # Import even if not directly used in final code, good practice
)
# No clr needed for standard DB classes
# No math needed if using IsAlmostEqualTo

# --- Script Core Logic ---

# Initialize suffix counters for each direction and an 'OTHER' category
suffix_counters = {'N': 1, 'S': 1, 'E': 1, 'W': 1, 'OTHER': 1}
renamed_count = 0
error_count = 0
skipped_count = 0
already_correct_count = 0

# Collect Elevation views (non-templates)
collector = FilteredElementCollector(doc).OfClass(View)
# Filter for Elevation type and ensure it's not a template
elevation_views = [v for v in collector if v.ViewType == ViewType.Elevation and not v.IsTemplate]

# Define cardinal direction vectors for comparison
north = XYZ(0, 1, 0)
south = XYZ(0, -1, 0)
east = XYZ(1, 0, 0)
west = XYZ(-1, 0, 0)
# Tolerance for vector comparison using IsAlmostEqualTo
# A larger tolerance might be needed if views are slightly off-axis
vector_comparison_tolerance = 0.01

# Iterate through the collected elevation views
for view in elevation_views:
    original_name = view.Name
    try:
        view_direction = view.ViewDirection
        direction_str = 'OTHER' # Default direction category

        # Normalize the direction vector for reliable comparison, check if it's valid
        if view_direction and view_direction.GetLength() > vector_comparison_tolerance:
            normalized_direction = view_direction.Normalize()

            # Compare normalized direction with cardinal directions
            if normalized_direction.IsAlmostEqualTo(north, vector_comparison_tolerance):
                direction_str = 'N'
            elif normalized_direction.IsAlmostEqualTo(south, vector_comparison_tolerance):
                direction_str = 'S'
            elif normalized_direction.IsAlmostEqualTo(east, vector_comparison_tolerance):
                direction_str = 'E'
            elif normalized_direction.IsAlmostEqualTo(west, vector_comparison_tolerance):
                direction_str = 'W'
            # else: It remains 'OTHER' if not close to any cardinal direction

        else:
            # Handle views with zero or near-zero view direction (unlikely but possible)
            # print("# Warning: Skipping view '{}' (ID: {}) due to invalid/zero view direction.".format(original_name, view.Id)) # Debug comment
            skipped_count += 1
            continue # Skip to the next view

        # Get the current suffix for this determined direction
        # Use try-except just in case direction_str is unexpected, though unlikely with current logic
        try:
             suffix = suffix_counters[direction_str]
        except KeyError:
             # print("# Warning: Unexpected direction category found for view '{}'. Using 'OTHER'.".format(original_name)) # Debug comment
             direction_str = 'OTHER'
             suffix = suffix_counters[direction_str]


        # Construct the new name using the pattern 'ELEV_Direction_Suffix'
        # Use zero-padding for the suffix (e.g., 01, 02, ..., 10) for better sorting in Project Browser
        new_name = "ELEV_{}_{:02d}".format(direction_str, suffix)

        # Increment the suffix counter for this direction for the *next* view
        # Increment happens regardless of whether rename occurs, to ensure sequential numbering
        suffix_counters[direction_str] += 1

        # Check if renaming is actually necessary
        if original_name != new_name:
            try:
                # Attempt to rename the view
                view.Name = new_name
                renamed_count += 1
                # print("# Renamed view '{}' (ID: {}) to '{}'".format(original_name, view.Id, new_name)) # Debug comment
            except Exception as e_rename:
                # Handle potential errors during renaming (e.g., duplicate names if script run weirdly)
                # print("# Error renaming view '{}' (ID: {}) to '{}': {}".format(original_name, view.Id, new_name, e_rename)) # Debug comment
                error_count += 1
                # Decrement counter if rename failed, so the number can be reused? Or just log error. Let's just log error.
        else:
             already_correct_count += 1
             # print("# View '{}' already has the correct name/format.".format(original_name)) # Debug comment


    except Exception as e_main:
        # Catch errors during view processing (e.g., accessing ViewDirection)
        # print("# Error processing view '{}' (ID: {}): {}".format(original_name, view.Id, e_main)) # Debug comment
        error_count += 1

# Optional: Print summary to RevitPythonShell output (comment out if not desired)
# print("--- Elevation View Renaming Summary ---")
# print("Successfully renamed: {}".format(renamed_count))
# print("Already had correct name/format: {}".format(already_correct_count))
# print("Skipped (Invalid/Zero Direction): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Elevation Views Found: {}".format(len(elevation_views)))