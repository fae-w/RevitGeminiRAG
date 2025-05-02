# Purpose: This script calculates the total length of walls of a specified type in a Revit model.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall, BuiltInParameter, UnitTypeId, UnitUtils, WallType

# Target wall type name
target_wall_type_name = "Generic - 200mm"

# Initialize total length (in internal units - decimal feet)
total_length_internal = 0.0

# Collect all Wall elements (instances)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

# Iterate through walls
for wall in collector:
    if isinstance(wall, Wall):
        try:
            # Get the wall type
            wall_type = doc.GetElement(wall.GetTypeId())
            if wall_type and isinstance(wall_type, WallType):
                # Check if the wall type name matches the target
                if wall_type.Name == target_wall_type_name:
                    # Get the length parameter
                    length_param = wall.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)
                    if length_param:
                        length_internal = length_param.AsDouble() # Length in internal units (decimal feet)
                        total_length_internal += length_internal
                    else:
                        # Fallback: try getting length from the location curve if parameter fails
                        if wall.Location and isinstance(wall.Location, LocationCurve):
                             curve_length_internal = wall.Location.Curve.Length
                             total_length_internal += curve_length_internal

        except Exception as e:
            # print("# Error processing Wall {}: {}".format(wall.Id, e)) # Optional: Log errors for debugging
            pass # Silently skip walls that cause errors

# Convert total length from internal units (feet) to meters
total_length_meters = UnitUtils.ConvertFromInternalUnits(total_length_internal, UnitTypeId.Meters)
total_length_feet = total_length_internal # Keep the value in feet as well for potential alternative reporting

# Format the output strings
report_lines = []
report_lines.append("Wall Length Report")
report_lines.append("==================")
report_lines.append("Target Wall Type: {}".format(target_wall_type_name))
report_lines.append("Total Length (Meters): {:.2f} m".format(total_length_meters))
report_lines.append("Total Length (Feet): {:.2f} ft".format(total_length_feet)) # Also report in feet

# Format the final output for export
file_content = "\n".join(report_lines)
# Sanitize filename from type name
safe_filename_part = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in target_wall_type_name)
filename_suggestion = "total_wall_length_{}.txt".format(safe_filename_part)

print("EXPORT::TXT::{}".format(filename_suggestion))
print(file_content)