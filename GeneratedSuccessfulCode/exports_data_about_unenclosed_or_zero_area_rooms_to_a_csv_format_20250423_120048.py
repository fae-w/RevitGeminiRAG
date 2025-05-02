# Purpose: This script exports data about unenclosed or zero-area rooms to a CSV format.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, BuiltInParameter
)
# Import Room specifically for type checking if desired, though BuiltInCategory is primary filter
from Autodesk.Revit.DB.Architecture import Room
# Import ForgeTypeId if needing newer parameter access methods (optional fallback)
# try:
#     from Autodesk.Revit.DB import ParameterTypeId
# except ImportError:
#     ParameterTypeId = None # Handle older Revit versions gracefully

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Room Name","Room Number","Element ID"')

# Collect all Room elements
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Small tolerance for floating point comparison
tolerance = 1e-6

# Iterate through collected room elements
for element in collector:
    # Ensure it's a Room object
    if not isinstance(element, Room):
        continue

    room = element
    is_unenclosed_or_zero_area = False
    room_area = 0.0

    try:
        # Get the calculated area using the Area property (most reliable for checking placement/enclosure status)
        room_area = room.Area

        # Check if area is effectively zero
        if room_area < tolerance:
            is_unenclosed_or_zero_area = True
        # Check if the room is unplaced (Location is None is another indicator, often correlated with 0 Area)
        # elif room.Location is None: # This check might be redundant if Area check covers it
        #    is_unenclosed_or_zero_area = True

        # If the room meets the criteria
        if is_unenclosed_or_zero_area:
            room_name = "N/A"
            room_number = "N/A"
            elem_id_str = str(room.Id.IntegerValue)

            # Get Room Name using BuiltInParameter first
            name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
            if name_param and name_param.HasValue:
                room_name = name_param.AsString()
            elif hasattr(room, 'Name'): # Fallback to Name property
                 room_name = room.Name
            # Add ForgeTypeId fallback if needed and available
            # elif ParameterTypeId and hasattr(ParameterTypeId, 'ElemRoomName'):
            #     try:
            #         name_param_forge = room.get_Parameter(ParameterTypeId.ElemRoomName)
            #         if name_param_forge and name_param_forge.HasValue:
            #              room_name = name_param_forge.AsString()
            #     except Exception: pass # Ignore ForgeTypeId errors

            # Get Room Number using BuiltInParameter first
            num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if num_param and num_param.HasValue:
                room_number = num_param.AsString()
            elif hasattr(room, 'Number'): # Fallback to Number property
                 room_number = room.Number
            # Add ForgeTypeId fallback if needed and available
            # elif ParameterTypeId and hasattr(ParameterTypeId, 'ElemRoomNumber'):
            #     try:
            #         num_param_forge = room.get_Parameter(ParameterTypeId.ElemRoomNumber)
            #         if num_param_forge and num_param_forge.HasValue:
            #              room_number = num_param_forge.AsString()
            #     except Exception: pass # Ignore ForgeTypeId errors


            # Escape quotes for CSV safety and enclose in quotes
            safe_room_name = '"' + str(room_name).replace('"', '""') + '"'
            safe_room_number = '"' + str(room_number).replace('"', '""') + '"'
            safe_elem_id = '"' + elem_id_str.replace('"', '""') + '"' # ID shouldn't need escaping, but good practice

            # Append data row
            csv_lines.append(','.join([safe_room_name, safe_room_number, safe_elem_id]))

    except Exception as e:
        # print("Error processing Room {}: {}".format(element.Id, e)) # Optional debug
        # Add error row to CSV? Or just skip? Skipping for now.
        pass


# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::unenclosed_or_zero_area_rooms.csv")
    print(file_content)
else:
    # Provide feedback if no matching rooms were found
    print("# No 'Not Enclosed' or Zero Area rooms found in the project.")