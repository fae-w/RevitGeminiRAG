# Purpose: This script converts the names of all rooms in a Revit project to uppercase.

﻿# Mandatory Imports
import clr
# No specific .NET types needed beyond Revit API
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory
    # ParameterTypeId # Not strictly necessary if using .Name property
)
# Room class is in DB.Architecture
from Autodesk.Revit.DB.Architecture import Room

# --- Script Core Logic ---

# Collect all Room elements in the project
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

rooms_to_process = list(collector) # Convert iterator to list for stable processing

renamed_count = 0
skipped_count = 0
error_count = 0

for room in rooms_to_process:
    # Ensure it's actually a Room object (though collector should handle this)
    if not isinstance(room, Room):
        # print("# Skipping non-Room element with ID {}".format(room.Id)) # Debug
        continue

    try:
        # Get the current name
        # The simplest way is often the .Name property
        current_name = room.Name

        # Alternative using Parameter (more verbose, usually not needed for Name)
        # name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
        # if name_param and name_param.HasValue:
        #    current_name = name_param.AsString()
        # else:
        #    # Handle case where name parameter is missing or empty
        #    # print("# Warning: Could not read name parameter for Room ID {}".format(room.Id)) # Debug
        #    error_count += 1
        #    continue

        if current_name:
            # Convert to uppercase
            uppercase_name = current_name.upper()

            # Check if rename is actually needed
            if current_name != uppercase_name:
                # Rename the room
                room.Name = uppercase_name
                renamed_count += 1
                # print("# Renamed Room ID {} from '{}' to '{}'".format(room.Id, current_name, uppercase_name)) # Debug
            else:
                # print("# Skipped Room ID {}: Name '{}' is already uppercase.".format(room.Id, current_name)) # Debug
                skipped_count += 1
        else:
            # Handle rooms with no name or null name gracefully
            # print("# Skipped Room ID {}: Current name is empty or null.".format(room.Id)) # Debug
            skipped_count += 1

    except Exception as e:
        # Log any errors during processing a specific room
        # print("# Error processing Room ID {}: {}".format(room.Id, e)) # Debug
        error_count += 1

# Optional: Print summary (commented out)
# print("--- Room Renaming Summary ---")
# print("Successfully renamed to uppercase: {}".format(renamed_count))
# print("Skipped (already uppercase or no name): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Rooms processed: {}".format(len(rooms_to_process)))