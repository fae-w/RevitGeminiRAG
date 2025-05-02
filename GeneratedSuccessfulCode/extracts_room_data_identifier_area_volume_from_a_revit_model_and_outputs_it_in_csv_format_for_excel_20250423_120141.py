# Purpose: This script extracts room data (identifier, area, volume) from a Revit model and outputs it in CSV format for Excel.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Parameter, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System # For string formatting

# List to hold CSV lines (for Excel export)
csv_lines = []
# Add header row
csv_lines.append('"Room Identifier","Area (sq ft)","Volume (cu ft)"')

# Collect all Room elements that are placed (have area > 0)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Iterate through rooms and get data
processed_count = 0
for element in collector:
    # Ensure the element is a Room
    if isinstance(element, Room):
        room = element
        try:
            # Use the Area property from SpatialElement to check if room is placed
            area_internal = room.Area
            # Only process rooms with a non-negligible area (i.e., placed rooms)
            if area_internal > 1e-6:
                # Get Room Number
                number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                if number_param and number_param.HasValue and number_param.AsString() != "":
                    number = number_param.AsString()
                else:
                    number = "Num?" # Placeholder if number is not set or empty

                # Get Room Name using the Name property inherited from Element
                # Fallback to ROOM_NAME parameter if Name property is unexpectedly empty.
                name = element.Name
                if not name or name == "":
                     name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
                     if name_param and name_param.HasValue and name_param.AsString() != "":
                         name = name_param.AsString()
                     else: # If no name found either, use a placeholder
                         name = "Name?"

                # Create combined Room Identifier
                room_identifier = "{0}-{1}".format(number, name) # Use standard string formatting

                # Area is already retrieved (in internal units, square feet)
                # Format to 2 decimal places using System.String.Format for IronPython compatibility
                area_str = System.String.Format("{0:.2f}", area_internal)

                # Get Volume
                volume_internal = room.Volume # Direct property for Volume
                volume_str = System.String.Format("{0:.2f}", volume_internal)

                # Escape double quotes in identifier for CSV compatibility and enclose fields in quotes
                safe_identifier = '"' + room_identifier.replace('"', '""') + '"'
                safe_area = '"' + area_str + '"'
                safe_volume = '"' + volume_str + '"'

                csv_lines.append(safe_identifier + ',' + safe_area + ',' + safe_volume)
                processed_count += 1
        except Exception as e:
            # Optional: Print errors for debugging in RevitPythonShell or pyRevit console
            # print("Error processing room {0}: {1}".format(element.Id.ToString(), e)) # Use standard string formatting
            pass # Silently skip rooms that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final output for export as CSV (Excel compatible)
    file_content = "\n".join(csv_lines)
    # Indicate EXCEL format, suggest .xlsx extension. Data is CSV formatted.
    print("EXPORT::EXCEL::room_identifiers.xlsx")
    print(file_content)
else:
    # If only the header exists, print a message indicating no rooms were found/processed
    print("# No placed room elements found or processed.")