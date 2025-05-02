# Purpose: This script renames unnamed reference planes in a Revit model.

﻿# Mandatory Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ReferencePlane
)
# No clr needed for basic element property access

# --- Script Core Logic ---

# Counter for generating unique names for unnamed reference planes
ref_plane_counter = 1
renamed_count = 0
skipped_count = 0
error_count = 0

# Collect all ReferencePlane elements in the document
collector = FilteredElementCollector(doc).OfClass(ReferencePlane)
reference_planes = list(collector) # Convert iterator to list

# Iterate through the collected reference planes
for rp in reference_planes:
    try:
        # Get the current name of the reference plane
        current_name = rp.Name

        # Check if the name is null, empty, or consists only of whitespace
        # Using strip() handles names that might contain only spaces
        if current_name is None or not current_name.strip():
            # Generate the new name using the counter
            new_name = "RefPlane_{}".format(ref_plane_counter)

            try:
                # Attempt to assign the new name
                # Revit will automatically handle potential duplicate names
                # by appending a suffix if 'RefPlane_XYZ' already exists,
                # but our logic assumes we are naming previously unnamed ones.
                rp.Name = new_name
                renamed_count += 1
                ref_plane_counter += 1 # Increment counter only after a successful assignment attempt

            except Exception as rename_ex:
                # Log error if renaming fails for some reason
                # print("# Error renaming Reference Plane (ID: {}) to '{}': {}".format(rp.Id, new_name, rename_ex)) # Debug line
                error_count += 1
        else:
            # The reference plane already has a name, skip it
            skipped_count += 1
            # print("# Skipped Reference Plane (ID: {}), already named: '{}'".format(rp.Id, current_name)) # Debug line

    except Exception as ex:
        # Log error if accessing the reference plane or its name fails
        # print("# Error processing Reference Plane (ID: {}): {}".format(rp.Id if rp else 'Unknown', ex)) # Debug line
        error_count += 1

# Optional: Print summary to console (useful for debugging in RPS or pyRevit output)
# print("--- Reference Plane Renaming Summary ---")
# print("Successfully renamed unnamed planes: {}".format(renamed_count))
# print("Skipped (already named): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Reference Planes processed: {}".format(len(reference_planes)))