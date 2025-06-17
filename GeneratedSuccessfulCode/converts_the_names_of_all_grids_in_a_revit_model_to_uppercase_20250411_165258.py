# Purpose: This script converts the names of all Grids in a Revit model to uppercase.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
from System import Exception # Explicit exception import

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Grid,
    Element # Base class, good practice
)

# --- Script Core Logic ---

# Assumption: "Grid heads" refers to the name displayed in the grid bubble,
# which corresponds to the 'Name' property of the Grid element itself.

# Collect all Grid elements in the project
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType()

grids_to_process = list(collector) # Convert iterator to list for stable processing

renamed_count = 0
skipped_count = 0
error_count = 0

for grid in grids_to_process:
    # Ensure it's actually a Grid object
    if not isinstance(grid, Grid):
        # This check might be redundant due to the collector, but adds safety
        # print("# Skipping non-Grid element with ID {{}}".format(grid.Id)) # Debug
        continue

    try:
        # Get the current name using the .Name property
        current_name = grid.Name

        if current_name:
            # Convert to uppercase
            uppercase_name = current_name.upper()

            # Check if rename is actually needed
            if current_name != uppercase_name:
                # Rename the grid
                grid.Name = uppercase_name
                renamed_count += 1
                # print("# Renamed Grid ID {{}} from '{{}}' to '{{}}'".format(grid.Id, current_name, uppercase_name)) # Debug
            else:
                # print("# Skipped Grid ID {{}}: Name '{{}}' is already uppercase.".format(grid.Id, current_name)) # Debug
                skipped_count += 1
        else:
            # Handle grids with no name or null name gracefully
            # print("# Skipped Grid ID {{}}: Current name is empty or null.".format(grid.Id)) # Debug
            skipped_count += 1

    except Exception as e:
        # Log any errors during processing a specific grid
        current_name_for_error = "<Error Retrieving>"
        try:
            current_name_for_error = grid.Name
        except: pass
        print("# Error processing Grid ID {{}} (Name: '{{}}'): {{}}".format(grid.Id, current_name_for_error, e)) # Debug
        error_count += 1

# Optional: Print summary (commented out)
# print("--- Grid Renaming Summary ---")
# print("Successfully renamed to uppercase: {{}}".format(renamed_count))
# print("Skipped (already uppercase or no name): {{}}".format(skipped_count))
# print("Errors encountered: {{}}".format(error_count))
# print("Total Grids processed: {{}}".format(len(grids_to_process)))