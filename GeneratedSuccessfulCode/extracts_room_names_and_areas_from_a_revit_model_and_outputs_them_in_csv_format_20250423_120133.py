# Purpose: This script extracts room names and areas from a Revit model and outputs them in CSV format.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI') # Assumed standard reference
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Parameter, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System # For string formatting

# List to hold CSV lines (Excel can open CSV easily)
csv_lines = []
# Add header row
csv_lines.append('"Room Name","Area (sq ft)"')

# Collect all Room elements that are placed (have area > 0)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Iterate through rooms and get data
processed_count = 0
for element in collector:
    # Ensure the element is a Room and check if it's placed (Area > 0)
    # Unplaced rooms have Area = 0 and often lack valid Name/Number parameters
    if isinstance(element, Room):
        room = element
        try:
            # Use the Area property from SpatialElement to check if room is placed
            area_internal = room.Area
            if area_internal > 1e-6: # Use a small tolerance instead of exact 0.0
                # Get Room Name using the Name property inherited from Element/SpatialElement
                # Fallback to ROOM_NAME parameter if Name property is unexpectedly empty.
                name = element.Name
                if not name or name == "":
                     name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
                     if name_param and name_param.HasValue:
                         name = name_param.AsString()
                     else: # If no name parameter found either, use a placeholder
                         name = "Unnamed Room ({})".format(room.Id.ToString())

                # Area is already retrieved (in internal units, square feet)
                # Format to 2 decimal places using System.String.Format for IronPython compatibility
                area_str = System.String.Format("{0:.2f}", area_internal)

                # Escape double quotes in name for CSV compatibility and enclose fields in quotes
                safe_name = '"' + name.replace('"', '""') + '"'
                safe_area = '"' + area_str + '"' # Area shouldn't contain quotes, but good practice

                csv_lines.append(safe_name + ',' + safe_area)
                processed_count += 1
        except Exception as e:
            # Optional: Print errors for debugging in RevitPythonShell or pyRevit console
            # print("Error processing room {}: {}".format(element.Id.ToString(), e))
            pass # Silently skip rooms that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final output for export as CSV (Excel compatible)
    file_content = "\n".join(csv_lines)
    # Indicate CSV format, which Excel opens readily. Suggest .csv extension.
    print("EXPORT::CSV::room_names_areas.csv")
    print(file_content)
else:
    # If only the header exists, print a message indicating no rooms were found/processed
    print("# No placed room elements found or processed.")