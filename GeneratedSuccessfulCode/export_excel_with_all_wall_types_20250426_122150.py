# Purpose: This script extracts all WallType elements and their basic properties,
#          then exports the data to an Excel-compatible format (CSV data).

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, WallType, WallKind

# List to hold CSV lines for Excel export
csv_lines = []
# Add header row
csv_lines.append('"Name","Kind","Width (ft)"')

# Collect all WallType elements
# WallType elements are ElementTypes, so no need for WhereElementIsNotElementType()
# Using OfClass(WallType) is the correct way to get types.
collector = FilteredElementCollector(doc).OfClass(WallType)

# Iterate through wall types and get data
for wall_type in collector:
    # Double-check it's actually a WallType (though OfClass should ensure this)
    if isinstance(wall_type, WallType):
        try:
            name = wall_type.Name
            # Get the WallKind enum and convert to string
            kind_enum = wall_type.Kind
            kind_str = kind_enum.ToString()

            # Get the width (thickness) in internal units (decimal feet)
            # Handle cases where width might not be applicable (e.g., Curtain Wall)
            width_str = "N/A" # Default value if width cannot be obtained
            try:
                # The Width property exists directly on WallType
                width_internal = wall_type.Width
                # Format width to 4 decimal places (already in feet)
                width_str = "{:.4f}".format(width_internal)
            except Exception:
                # This might happen for certain wall types like Curtain walls
                # where Width isn't directly defined in the same way.
                # Keep width_str as "N/A"
                pass

            # Escape quotes in name for CSV safety
            safe_name = '"' + name.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_name, kind_str, width_str]))
        except Exception as e:
            # Optional: Log errors for debugging specific types
            # print("# Error processing WallType ID {}: {}".format(wall_type.Id.ToString(), e))
            # Append row with error indication if needed, or skip
            try:
                 safe_name_err = '"' + name.replace('"', '""') + '"' if name else '""'
                 error_message = '"Error Processing: {}"'.format(str(e).replace('"', '""'))
                 csv_lines.append(','.join([safe_name_err, error_message, error_message]))
            except:
                 csv_lines.append('"Error","Could not process WallType {}",""'.format(wall_type.Id.ToString()))
            pass # Continue processing other types

# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::EXCEL::all_wall_types.xlsx")
    print(file_content)
else:
    print("# No WallType elements found in the project.")