# Purpose: This script exports data for unenclosed or zero-area Revit rooms to a CSV format.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, BuiltInParameter
)
# Import Room specifically for type checking and accessing properties
from Autodesk.Revit.DB.Architecture import Room

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Room Name","Room Number","Element ID"')

# Collect all Room elements
# Ensure we filter for instances, not types
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Small tolerance for floating point comparison (Revit uses feet internally)
# 1e-6 square feet is effectively zero for area calculation
tolerance = 1e-6

# Iterate through collected room elements
for element in collector:
    # Ensure it's a Room object before proceeding
    if not isinstance(element, Room):
        continue

    room = element
    is_unenclosed_or_zero_area = False
    room_area = 0.0

    try:
        # Get the calculated area using the Area property
        # A zero or near-zero area indicates the room is not placed,
        # not properly enclosed, or redundant. This covers the user's request.
        room_area = room.Area

        # Check if area is effectively zero
        if room_area < tolerance:
            is_unenclosed_or_zero_area = True
        # Additionally, check if the room has no location point (typically means 'Not Placed')
        # This often correlates with zero area but provides an extra check.
        elif room.Location is None:
            is_unenclosed_or_zero_area = True

        # If the room meets the criteria
        if is_unenclosed_or_zero_area:
            room_name = "N/A"
            room_number = "N/A"
            elem_id_str = str(room.Id.IntegerValue)

            # Get Room Name using BuiltInParameter first
            name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
            if name_param and name_param.HasValue:
                room_name_val = name_param.AsString()
                # Check if the retrieved value is not null or empty before assigning
                if room_name_val:
                    room_name = room_name_val
            elif hasattr(room, 'Name') and room.Name: # Fallback to Name property if parameter fails or is empty
                 room_name = room.Name

            # Get Room Number using BuiltInParameter first
            num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if num_param and num_param.HasValue:
                room_number_val = num_param.AsString()
                # Check if the retrieved value is not null or empty before assigning
                if room_number_val:
                    room_number = room_number_val
            elif hasattr(room, 'Number') and room.Number: # Fallback to Number property if parameter fails or is empty
                 room_number = room.Number

            # Escape double quotes for CSV safety and enclose fields in double quotes
            safe_room_name = '"' + str(room_name).replace('"', '""') + '"'
            safe_room_number = '"' + str(room_number).replace('"', '""') + '"'
            safe_elem_id = '"' + elem_id_str.replace('"', '""') + '"' # ID shouldn't need escaping, but good practice

            # Append data row
            csv_lines.append(','.join([safe_room_name, safe_room_number, safe_elem_id]))

    except Exception as e:
        # Optionally print error for debugging, but script should continue
        # print("Error processing Room {}: {}".format(element.Id, e))
        pass # Skip rooms that cause unexpected errors

# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::unenclosed_or_zero_area_rooms.csv")
    print(file_content)
else:
    # Provide feedback if no matching rooms were found
    print("# No 'Not Enclosed' or Zero Area rooms found in the project.")