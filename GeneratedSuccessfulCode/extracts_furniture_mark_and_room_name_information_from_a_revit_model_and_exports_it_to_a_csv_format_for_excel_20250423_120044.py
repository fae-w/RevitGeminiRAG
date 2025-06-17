# Purpose: This script extracts furniture mark and room name information from a Revit model and exports it to a CSV format for Excel.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, FamilyInstance,
    BuiltInParameter, LocationPoint, XYZ
)
from Autodesk.Revit.DB.Architecture import Room # Room is in Architecture namespace
import System # For string formatting, although not strictly needed here

# List to hold CSV lines for Excel export
csv_lines = []
# Add header row
csv_lines.append('"Furniture Mark","Room Name"')

# Collect all Furniture instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType()

# Iterate through furniture instances
processed_count = 0
for inst in collector:
    if isinstance(inst, FamilyInstance):
        furniture_mark = "N/A"
        room_name = "Not in Room / Error" # Default value

        try:
            # Get Furniture Mark
            mark_param = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            if mark_param and mark_param.HasValue:
                furniture_mark = mark_param.AsString()
                if not furniture_mark: # Handle empty string case
                    furniture_mark = "N/A"
            else:
                # Check if the instance itself has a Mark property (less common for Mark)
                if hasattr(inst, 'Mark') and inst.Mark:
                     furniture_mark = inst.Mark
                else: # If no parameter and no property, mark as N/A
                    furniture_mark = "N/A"


            # --- Method 1: Use FamilyInstance.Room property (preferred for simplicity) ---
            found_room = None
            if hasattr(inst, 'Room') and inst.Room is not None:
                # This property gets the room for the instance in the last phase
                found_room = inst.Room
            # --- Method 2: Use GetRoomAtPoint as a fallback (if Room property fails or is None) ---
            else:
                 location = inst.Location
                 if location and isinstance(location, LocationPoint):
                     point = location.Point
                     # Check if the point is valid before querying
                     if point:
                         # Use GetRoomAtPoint for the document's default phase (last phase)
                         found_room = doc.GetRoomAtPoint(point)

            # If a room was found by either method
            if found_room and isinstance(found_room, Room):
                 # Get Room Name using Name property, fallback to parameter
                 if hasattr(found_room, 'Name') and found_room.Name:
                     room_name = found_room.Name
                 else:
                     name_param = found_room.get_Parameter(BuiltInParameter.ROOM_NAME)
                     if name_param and name_param.HasValue:
                         room_name = name_param.AsString()
                     else:
                         room_name = "Unnamed Room ({0})".format(found_room.Id.ToString()) # Use ID if name fails
                 if not room_name: # Handle empty name string
                     room_name = "Unnamed Room ({0})".format(found_room.Id.ToString())
            else:
                # If still no room found, keep default 'Not in Room / Error'
                pass # room_name remains default

            # Escape double quotes for CSV/Excel compatibility
            safe_mark = '"' + str(furniture_mark).replace('"', '""') + '"'
            safe_room_name = '"' + str(room_name).replace('"', '""') + '"'

            # Append data row
            csv_lines.append(safe_mark + ',' + safe_room_name)
            processed_count += 1

        except Exception as e:
            # Optional: Print errors during development/debugging
            # print("Error processing Furniture Instance {0}: {1}".format(inst.Id.ToString(), str(e)))
            try:
                 # Try to add row with error indication
                 safe_mark_error = '"' + str(furniture_mark).replace('"', '""') + '"'
                 safe_room_error = '"' + "Error Processing Instance {0}".format(inst.Id.ToString()) + '"'
                 csv_lines.append(safe_mark_error + ',' + safe_room_error)
            except:
                pass # Ignore if even error logging fails

# Check if we gathered any data
if processed_count > 0:
    # Format the final output for export as Excel (using CSV data)
    file_content = "\n".join(csv_lines)
    print("EXPORT::EXCEL::furniture_room_locations.xlsx")
    print(file_content)
else:
    # If only the header exists, print a message indicating no furniture was found/processed
    print("# No furniture instances found or processed.")