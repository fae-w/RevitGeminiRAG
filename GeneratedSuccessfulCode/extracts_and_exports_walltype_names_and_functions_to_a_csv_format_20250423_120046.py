# Purpose: This script extracts and exports WallType names and functions to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, WallType, WallFunction

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Name","Function"')

# Collect all WallType elements
collector = FilteredElementCollector(doc).OfClass(WallType)

# Iterate through wall types and get data
for wall_type in collector:
    if isinstance(wall_type, WallType):
        try:
            name = wall_type.Name
            # Get the WallFunction enum and convert to string
            function_enum = wall_type.Function
            function_str = function_enum.ToString()

            # Escape quotes in name for CSV safety
            safe_name = '"' + name.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_name, function_str]))
        except Exception as e:
            # print("# Error processing WallType {}: {}".format(wall_type.Id, e)) # Optional: Log errors for debugging
            pass # Silently skip types that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::wall_type_functions.csv")
    print(file_content)
else:
    print("# No WallType elements found in the project.")