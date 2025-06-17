# Purpose: This script extracts room names and rounded areas from a Revit model and outputs them in CSV format for Excel.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Parameter, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System # For Math.Round

# List to hold CSV lines (for Excel export)
csv_lines = []
# Add header row - requested no units for area
csv_lines.append('"Room Name","Area"')

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
                # Get Room Name using the Name property inherited from Element
                # Fallback to ROOM_NAME parameter if Name property is unexpectedly empty.
                name = element.Name
                if not name or name == "":
                     name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
                     if name_param and name_param.HasValue:
                         name = name_param.AsString()
                     else: # If no name parameter found either, use a placeholder
                         name = "Unnamed Room ({0})".format(room.Id.ToString()) # Use standard string formatting

                # Round the area (which is in internal units, sq ft) to the nearest whole number
                rounded_area = int(System.Math.Round(area_internal))
                area_str = str(rounded_area) # Convert rounded integer to string

                # Escape double quotes in name for CSV compatibility and enclose fields in quotes
                safe_name = '"' + name.replace('"', '""') + '"'
                safe_area = '"' + area_str + '"' # Area is numeric, less likely to need quotes, but good practice

                csv_lines.append(safe_name + ',' + safe_area)
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
    print("EXPORT::EXCEL::room_names_rounded_areas.xlsx")
    print(file_content)
else:
    # If only the header exists, print a message indicating no rooms were found/processed
    print("# No placed room elements found or processed.")