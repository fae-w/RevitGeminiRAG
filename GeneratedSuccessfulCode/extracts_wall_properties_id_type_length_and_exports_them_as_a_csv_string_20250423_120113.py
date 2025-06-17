# Purpose: This script extracts wall properties (ID, type, length) and exports them as a CSV string.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall, BuiltInParameter, UnitTypeId, UnitUtils

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Wall ID","Wall Type","Length (m)"')

# Collect all Wall elements (instances)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

# Iterate through walls and get data
for wall in collector:
    if isinstance(wall, Wall):
        try:
            wall_id = wall.Id.IntegerValue
            wall_type_name = wall.Name # This gets the instance name, usually corresponds to type name for system families unless specifically renamed

            # Get length parameter
            length_param = wall.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)
            length_meters_str = "N/A"
            if length_param:
                length_internal = length_param.AsDouble() # Length in internal units (decimal feet)
                # Convert length from internal units (feet) to meters
                length_meters = UnitUtils.ConvertFromInternalUnits(length_internal, UnitTypeId.Meters)
                length_meters_str = "{:.2f}".format(length_meters) # Format to 2 decimal places
            else:
                # Try getting length from the location curve if parameter fails
                if wall.Location and isinstance(wall.Location, LocationCurve):
                     curve_length_internal = wall.Location.Curve.Length
                     length_meters = UnitUtils.ConvertFromInternalUnits(curve_length_internal, UnitTypeId.Meters)
                     length_meters_str = "{:.2f}".format(length_meters)

            # Escape quotes in type name for CSV safety
            safe_type_name = '"' + wall_type_name.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([str(wall_id), safe_type_name, length_meters_str]))
        except Exception as e:
            # print("# Error processing Wall {}: {}".format(wall.Id, e)) # Optional: Log errors for debugging
            pass # Silently skip walls that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::wall_lengths_meters.csv")
    print(file_content)
else:
    print("# No Wall elements found or processed.")