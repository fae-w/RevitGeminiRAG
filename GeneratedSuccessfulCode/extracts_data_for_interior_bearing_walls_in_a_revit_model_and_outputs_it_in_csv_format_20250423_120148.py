# Purpose: This script extracts data for interior bearing walls in a Revit model and outputs it in CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, WallType, Wall, BuiltInCategory, WallFunction, ElementId
# Ensure StructuralWallUsage is imported correctly
clr.AddReference('RevitAPI') # Ensure RevitAPI is referenced for Structure namespace
from Autodesk.Revit.DB.Structure import StructuralWallUsage

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Wall Type Name","Wall Instance ID"')

# --- Step 1: Find Wall Types with Function 'Interior' ---
interior_wall_type_ids = set()
wall_type_collector = FilteredElementCollector(doc).OfClass(WallType)
for wall_type in wall_type_collector:
    if isinstance(wall_type, WallType):
        try:
            # Check if the 'Function' parameter is 'Interior'
            func_param = wall_type.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
            if func_param and func_param.AsInteger() == int(WallFunction.Interior):
                 interior_wall_type_ids.add(wall_type.Id)
            # Alternative check using the property (usually preferred if available)
            # if wall_type.Function == WallFunction.Interior:
            #     interior_wall_type_ids.add(wall_type.Id)
        except Exception as e:
            # print("# Error checking function for WallType {{}}: {{}}".format(wall_type.Id, e)) # Debugging
            pass # Silently skip types that cause errors or lack the parameter

# --- Step 2: Find Wall Instances using those types and check Structural Usage ---
found_matches = False
if interior_wall_type_ids: # Proceed only if we found interior wall types
    wall_instance_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    for wall in wall_instance_collector:
        if isinstance(wall, Wall):
            try:
                wall_type_id = wall.WallTypeId
                # Check if the wall's type is one of the interior function types
                if wall_type_id in interior_wall_type_ids:
                    # Check the instance's structural usage parameter
                    # Use the property if available and reliable
                    structural_usage = wall.StructuralUsage
                    # As a fallback, or if property is not available, check the parameter
                    # structural_usage_param = wall.get_Parameter(BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM)
                    # if structural_usage_param and structural_usage_param.AsInteger() == int(StructuralWallUsage.Bearing):
                    #     structural_usage = StructuralWallUsage.Bearing # Set local variable if using parameter check
                    # else:
                    #     structural_usage = StructuralWallUsage.NonBearing # Default or other value

                    if structural_usage == StructuralWallUsage.Bearing:
                        # Found a match! Get type name and instance ID
                        wall_type = doc.GetElement(wall_type_id)
                        if wall_type: # Check if GetElement returned a valid element
                            wall_type_name = wall_type.Name
                            wall_instance_id = wall.Id.IntegerValue

                            # Escape quotes in name for CSV safety
                            safe_name = '"' + wall_type_name.replace('"', '""') + '"'

                            # Append data row
                            csv_lines.append(','.join([safe_name, str(wall_instance_id)]))
                            found_matches = True
                        else:
                            # print("# Warning: Could not retrieve WallType element for ID {{}}.".format(wall_type_id)) # Debugging
                            pass
            except AttributeError:
                 # Handle cases where StructuralUsage might not be available (though it should be for Walls)
                 # print("# Warning: Wall {{}} does not have StructuralUsage property.".format(wall.Id)) # Debugging
                 pass
            except Exception as e:
                # print("# Error processing Wall instance {{}}: {{}}".format(wall.Id, e)) # Debugging
                pass # Silently skip walls that cause errors
else:
    print("# No Wall Types with function 'Interior' found in the project.")

# --- Step 3: Format and Print Export Data ---
if found_matches: # Check if any data was added beyond the header
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::interior_bearing_walls_report.csv")
    print(file_content)
elif not interior_wall_type_ids:
    pass # Message already printed if no interior types were found
else:
    # This means interior types existed, but no instances matched the bearing criteria
    print("# No Wall instances found matching the criteria (Interior Type Function and Bearing Structural Usage).")