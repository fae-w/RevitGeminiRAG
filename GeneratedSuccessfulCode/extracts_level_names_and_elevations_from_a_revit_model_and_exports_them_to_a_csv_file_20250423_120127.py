# Purpose: This script extracts level names and elevations from a Revit model and exports them to a CSV file.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import FilteredElementCollector, Level, BuiltInCategory, ElementId
import System

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Level Name","Elevation (ft)"')

# Collect all Level elements
collector = FilteredElementCollector(doc).OfClass(Level) # Use OfClass(Level) for better type safety

# Counter for processed levels
processed_count = 0

# Iterate through levels and get data
for level in collector:
    if isinstance(level, Level):
        try:
            # Get Level Name
            level_name = level.Name
            if not level_name or level_name == "":
                level_name = "Unnamed Level ID: " + level.Id.ToString()

            # Get Level Elevation (already in internal units - feet)
            elevation_internal = level.Elevation
            # Format elevation to 2 decimal places using System.String.Format for IronPython
            elevation_str = System.String.Format("{0:.2f}", elevation_internal)

            # Escape quotes for CSV safety and enclose in quotes
            safe_level_name = '"' + level_name.replace('"', '""') + '"'
            safe_elevation_str = '"' + elevation_str.replace('"', '""') + '"' # Usually numbers don't need quotes, but for consistency

            # Append data row
            csv_lines.append(','.join([safe_level_name, safe_elevation_str]))
            processed_count += 1

        except Exception as e:
            # Optional: Log errors for debugging
            # print("# Error processing Level {}: {}".format(level.Id.ToString(), e))
            pass # Silently skip levels that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final data string
    export_data_string = "\n".join(csv_lines)
    suggested_filename = 'project_levels.csv'
    file_format = 'CSV'
    # Print the export marker and data
    print("EXPORT::{0}::{1}".format(file_format, suggested_filename))
    print(export_data_string)
else:
    # Use print for messages to the user if no data is exported
    print("# No Level elements found in the project.")