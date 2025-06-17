# Purpose: This script renames unbounded Revit rooms (area of zero) to a specified name.

﻿# Mandatory Imports
import clr
# No specific .NET types needed beyond Revit API
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId # Not strictly needed but good practice
    # BuiltInParameter # Can use .Area property directly
)
# Room class is in DB.Architecture
from Autodesk.Revit.DB.Architecture import Room

# --- Script Core Logic ---

# Define the target name for unbounded rooms
new_name = "UNBOUNDED_Room_XYZ"
# Define the area threshold (0.0 in internal units - square feet)
zero_area_threshold = 0.0
# Small tolerance for floating point comparison, although 0.0 area is usually exact
tolerance = 1e-9

# Collect all Room elements in the project
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

rooms_to_process = list(collector) # Convert iterator to list for stable processing

renamed_count = 0
skipped_count = 0
error_count = 0

for room in rooms_to_process:
    # Ensure it's actually a Room object
    if not isinstance(room, Room):
        continue

    try:
        # Get the room's area using the .Area property
        # This property returns the area in Revit's internal units (square feet)
        current_area = room.Area

        # Check if the area is effectively zero
        # Compare absolute value against a small tolerance, or check for exact zero
        # Using a small tolerance is generally safer for float comparisons
        # if abs(current_area - zero_area_threshold) < tolerance:
        # For unplaced/unbounded rooms, area is often exactly 0.0, so direct comparison might suffice
        if current_area == 0.0:
            # Check if the room already has the target name
            current_name = room.Name
            if current_name != new_name:
                # Rename the room (Transaction managed externally)
                room.Name = new_name
                renamed_count += 1
                # print("# Renamed Room ID {} (Area: {}) to '{}'".format(room.Id, current_area, new_name)) # Debug
            else:
                # print("# Skipped Room ID {}: Already named '{}'".format(room.Id, new_name)) # Debug
                skipped_count += 1
        else:
            # print("# Skipped Room ID {}: Area ({}) is not zero.".format(room.Id, current_area)) # Debug
            skipped_count += 1

    except Exception as e:
        # Log any errors during processing a specific room
        # print("# Error processing Room ID {}: {}".format(room.Id, e)) # Debug
        error_count += 1

# Optional: Print summary (commented out)
# print("--- Room Renaming Summary ---")
# print("Renamed rooms with zero area: {}".format(renamed_count))
# print("Skipped (non-zero area or already named): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Rooms processed: {}".format(len(rooms_to_process)))