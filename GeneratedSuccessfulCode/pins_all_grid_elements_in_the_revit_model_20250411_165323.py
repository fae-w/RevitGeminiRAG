# Purpose: This script pins all grid elements in the Revit model.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
from System import Exception # Explicit exception import

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Grid,
    Element,
    BuiltInParameter # If trying to access via BuiltInParameter
)

# --- Script Core Logic ---

# Assumption: The user request "set the 'Instance Locked' parameter to true"
# refers to PINNING the element, which prevents accidental movement or deletion.
# The standard API property for this is Element.Pinned.
# We will use this property instead of searching for a parameter named 'Instance Locked'
# or using BuiltInParameter.ELEMENT_LOCKED_PARAM, as Element.Pinned is the correct method.

# Collect all Grid elements in the project
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType()

grids_to_process = list(collector) # Convert iterator to list

pinned_count = 0
already_pinned_count = 0
error_count = 0
skipped_non_grid_count = 0

for grid in grids_to_process:
    # Ensure it's actually a Grid object and it's valid
    if not isinstance(grid, Grid) or not grid.IsValidObject:
        skipped_non_grid_count += 1
        # print("# Skipping non-Grid or invalid element with ID {{{{}}}}".format(grid.Id)) # Debug
        continue

    try:
        # Check if the grid can be pinned (most model elements can)
        # Although setting Pinned directly usually handles this, CanBeLocked is informative
        # if not grid.CanBeLocked(): # CanBeLocked() might not be directly available on Grid, it's on Element
        #    # Check base Element capability if needed, but usually setting Pinned is sufficient
        #    # print("# Grid ID {{{{}}}} cannot be locked/pinned.".format(grid.Id)) # Debug
        #    continue # Skip if it cannot be pinned

        # Check if the grid is already pinned
        if not grid.Pinned:
            # Pin the grid element
            grid.Pinned = True
            pinned_count += 1
            # print("# Pinned Grid ID {{{{}}}}".format(grid.Id)) # Debug
        else:
            already_pinned_count += 1
            # print("# Grid ID {{{{}}}} was already pinned.".format(grid.Id)) # Debug

    except Exception as e:
        # Log any errors during processing a specific grid
        print("# Error processing Grid ID {{{{}}}}: {{{{}}}}".format(grid.Id, e)) # Debug
        error_count += 1

# Optional: Print summary (commented out)
# print("--- Grid Pinning Summary ---")
# print("Successfully pinned: {{{{}}}}".format(pinned_count))
# print("Already pinned: {{{{}}}}".format(already_pinned_count))
# print("Errors encountered: {{{{}}}}".format(error_count))
# print("Skipped (non-Grid/invalid): {{{{}}}}".format(skipped_non_grid_count))
# print("Total Grids checked: {{{{}}}}".format(len(grids_to_process)))