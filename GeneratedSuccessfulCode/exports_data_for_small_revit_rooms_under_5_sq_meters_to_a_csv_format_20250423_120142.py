# Purpose: This script exports data for small Revit rooms (under 5 sq meters) to a CSV format.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Parameter, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System # For string formatting

# Define the area threshold in square feet (5 square meters)
# 1 meter = 3.28084 feet
# 1 sq meter = 3.28084 * 3.28084 sq feet
threshold_sqft = 5.0 * (3.28084 * 3.28084) # Approximately 53.81955 sq ft

# List to hold CSV lines (for Excel export)
csv_lines = []
# Add header row - Specify unit in header
csv_lines.append('"Room Name","Room Number","Area (sq ft)"')

# Collect all Room elements that are placed
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Iterate through rooms and get data
processed_count = 0
for element in collector:
    # Ensure the element is a Room
    if isinstance(element, Room):
        room = element
        try:
            # Use the Area property from SpatialElement to check if room is placed and get area
            area_internal = room.Area
            # Only process rooms with a non-negligible area AND area less than the threshold
            if area_internal > 1e-6 and area_internal < threshold_sqft:
                # Get Room Name using the Name property inherited from Element
                # Fallback to ROOM_NAME parameter if Name property is unexpectedly empty.
                name = element.Name
                if not name or name == "":
                     name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
                     if name_param and name_param.HasValue:
                         name = name_param.AsString()
                     else: # If no name found either, use a placeholder
                         name = "Unnamed Room ({{0}})".format(room.Id.ToString()) # Use standard string formatting

                # Get Room Number
                number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                if number_param and number_param.HasValue:
                    number = number_param.AsString()
                else:
                    number = "N/A" # Placeholder if number is not set

                # Area is already retrieved (in internal units, square feet)
                # Format precisely using System.String.Format (e.g., 6 decimal places)
                area_str = System.String.Format("{{0:.6f}}", area_internal)

                # Escape double quotes in name and number for CSV compatibility and enclose fields in quotes
                safe_name = '"' + name.replace('"', '""') + '"'
                safe_number = '"' + number.replace('"', '""') + '"'
                safe_area = '"' + area_str + '"' # Area shouldn't contain quotes, but good practice

                csv_lines.append(safe_name + ',' + safe_number + ',' + safe_area)
                processed_count += 1
        except Exception as e:
            # Optional: Print errors for debugging in RevitPythonShell or pyRevit console
            # print("Error processing room {{0}}: {{1}}".format(element.Id.ToString(), e)) # Use standard string formatting
            pass # Silently skip rooms that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final output for export as CSV (Excel compatible)
    file_content = "\n".join(csv_lines)
    # Indicate EXCEL format, suggest .xlsx extension. Data is CSV formatted.
    print("EXPORT::EXCEL::small_rooms_report.xlsx")
    print(file_content)
else:
    # If only the header exists, print a message indicating no rooms met the criteria
    print("# No placed room elements found with Area less than 5 square meters.")