# Purpose: This script extracts wall type properties and exports them to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, WallType, WallKind

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Name","Kind","Width (ft)"')

# Collect all WallType elements
collector = FilteredElementCollector(doc).OfClass(WallType)

# Iterate through wall types and get data
for wall_type in collector:
    if isinstance(wall_type, WallType):
        try:
            name = wall_type.Name
            # Get the WallKind enum and convert to string
            kind_enum = wall_type.Kind
            kind_str = kind_enum.ToString()

            # Get the width (thickness) in internal units (decimal feet)
            # Handle cases where width might not be applicable (e.g., Curtain Wall)
            width_internal = 0.0
            try:
                width_internal = wall_type.Width
            except Exception:
                pass # Keep width as 0.0 if Width property is not accessible

            # Format width to 4 decimal places (already in feet)
            width_str = "{{:.4f}}".format(width_internal)

            # Escape quotes in name for CSV safety
            safe_name = '"' + name.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_name, kind_str, width_str]))
        except Exception as e:
            # print("# Error processing WallType {{}}: {{}}".format(wall_type.Id, e)) # Optional: Log errors for debugging
            pass # Silently skip types that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::project_wall_types.csv")
    print(file_content)
else:
    print("# No WallType elements found in the project.")