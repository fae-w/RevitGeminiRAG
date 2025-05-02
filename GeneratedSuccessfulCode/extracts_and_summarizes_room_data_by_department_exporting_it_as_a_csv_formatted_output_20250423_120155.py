# Purpose: This script extracts and summarizes room data by department, exporting it as a CSV formatted output.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for Dictionary

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    SpatialElement
)
# Import Room class specifically from Architecture namespace
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Error: {}".format(e))

from System.Collections.Generic import Dictionary
import System # For string formatting

# Dictionary to store data: { DepartmentName: [Count, TotalArea] }
department_summary = Dictionary[str, list]()

# Collect all Room elements
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Iterate through rooms and aggregate data
processed_room_count = 0
for element in collector:
    # Ensure element is a valid Room object and is placed (has area)
    if isinstance(element, Room):
        room = element
        try:
            # Check if the room is placed (has a non-zero area)
            room_area_internal = room.Area
            if room_area_internal > 1e-6: # Use a small tolerance for floating point comparison
                processed_room_count += 1

                # Get the 'Department' parameter
                department_param = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)
                department_name = "(No Department)" # Default if parameter is missing or empty

                if department_param and department_param.HasValue:
                    value_str = department_param.AsString()
                    if value_str and value_str.strip(): # Check if not None and not just whitespace
                         department_name = value_str.strip()
                    # else: keep "(No Department)"

                # Update the summary dictionary
                if department_summary.ContainsKey(department_name):
                    department_summary[department_name][0] += 1 # Increment count
                    department_summary[department_name][1] += room_area_internal # Add area
                else:
                    # Add new department entry: [count=1, area]
                    department_summary.Add(department_name, [1, room_area_internal])

        except Exception as e:
            # Optional: Print errors for debugging
            # print("Error processing Room ID {}: {}".format(element.Id, e))
            pass # Continue to next room

# Prepare CSV lines for export
csv_lines = []
# Add header row
csv_lines.append('"Department","Room Count","Total Area (sq ft)"')

# Sort departments alphabetically for consistent output
sorted_departments = sorted(department_summary.Keys)

# Format data from the dictionary
for department_name in sorted_departments:
    count, total_area = department_summary[department_name]
    # Format area to 2 decimal places using System.String.Format
    area_str = System.String.Format("{0:.2f}", total_area)

    # Escape double quotes in department name for CSV and enclose in quotes
    safe_department_name = '"' + department_name.replace('"', '""') + '"'

    # Add data row
    csv_lines.append(safe_department_name + ',' + str(count) + ',"' + area_str + '"')

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export as CSV (Excel compatible)
    file_content = "\n".join(csv_lines)
    # Indicate EXCEL format, suggest .xlsx extension. Data is CSV formatted.
    print("EXPORT::EXCEL::room_department_summary.xlsx")
    print(file_content)
else:
    # If only the header exists, print a message indicating no rooms were found/processed
    print("# No placed room elements with department information found or processed.")

# Optional: Print summary to console for debugging
# print("# Processed {} placed rooms.".format(processed_room_count))
# print("# Found {} unique departments.".format(department_summary.Count))