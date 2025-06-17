# Purpose: This script exports room names and areas from a Revit model to a CSV format.

# Purpose: This script exports the names and areas of placed rooms in a Revit model to a CSV file.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI') # Assumed standard reference
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Parameter, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append("Room Name,Area (sq ft)")

# Collect all Room elements that are placed (have area > 0)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Iterate through rooms and get data
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
                # This usually holds the user-defined name for Rooms.
                # Fallback to ROOM_NAME parameter if Name property is unexpectedly empty.
                name = element.Name
                if not name:
                     name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
                     if name_param:
                         name = name_param.AsString()
                     else: # If no name parameter found either, use a placeholder
                         name = "Unnamed Room ({})".format(room.Id) # Escaped format

                # Area is already retrieved (in internal units, square feet)
                area_str = "{:.2f}".format(area_internal) # Escaped format specifier

                # Escape commas and double quotes in name for CSV compatibility
                safe_name = '"' + name.replace('"', '""') + '"'
                csv_lines.append(f"{safe_name},{area_str}") # Escaped f-string variables
        except Exception as e:
            # print(f"# Debug: Error processing room {element.Id}: {e}") # Escaped - uncomment for debugging
            pass # Skip rooms that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::room_areas.csv") # <-- The marker line
    print(file_content)                 # <-- The data content string
else:
    # If only the header exists, print a message indicating no rooms were found/processed
    print("# No placed room elements found or processed.")