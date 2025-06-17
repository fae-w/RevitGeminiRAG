# Purpose: This script identifies exterior walls in a Revit model that have a zero or missing thermal resistance (R-value) and exports the data to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall, BuiltInParameter, WallFunction, ElementId

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Element ID","Type Name"')

# Collect all Wall elements (instances)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

# Iterate through walls
for wall in collector:
    if isinstance(wall, Wall):
        try:
            # Check Wall Function parameter
            function_param = wall.get_Parameter(BuiltInParameter.WALL_FUNCTION_PARAM)
            is_exterior = False
            if function_param and function_param.HasValue:
                # WallFunction enum values: Exterior = 0, Interior = 1, etc.
                if function_param.AsInteger() == int(WallFunction.Exterior):
                    is_exterior = True

            # If it's not exterior, skip this wall
            if not is_exterior:
                continue

            # Check Thermal Resistance (R) parameter
            r_value_param = wall.get_Parameter(BuiltInParameter.WALL_ATTR_THERMAL_RESISTANCE_PARAM)
            r_value = -1.0 # Default to a value indicating not found or invalid
            has_r_value = False

            if r_value_param and r_value_param.HasValue:
                try:
                    # Check if storage type is Double before calling AsDouble
                    if r_value_param.StorageType == Autodesk.Revit.DB.StorageType.Double:
                        r_value = r_value_param.AsDouble()
                        has_r_value = True
                    # else: handle other storage types if necessary, but R-value should be Double
                except Exception:
                    # Parameter exists but cannot be read as double, treat as invalid/empty for this check
                    has_r_value = False
            else:
                # Parameter doesn't exist or has no value
                has_r_value = False

            # Include wall if R-value parameter is missing, has no value, or is zero
            if not has_r_value or (has_r_value and abs(r_value) < 0.0001): # Check if value is effectively zero
                element_id = wall.Id.IntegerValue
                wall_type = doc.GetElement(wall.GetTypeId())
                type_name = "Unknown"
                if wall_type:
                    type_name = wall_type.Name

                # Escape quotes in type name for CSV safety
                safe_type_name = '"' + type_name.replace('"', '""') + '"'

                # Append data row
                csv_lines.append(','.join([str(element_id), safe_type_name]))

        except Exception as e:
            # Optional: print("Error processing Wall {}: {}".format(wall.Id, e))
            pass # Silently skip walls that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::exterior_walls_zero_r_value.csv")
    print(file_content)
else:
    print("# No exterior walls found matching the criteria (Function=Exterior and Thermal Resistance=0 or Empty).")