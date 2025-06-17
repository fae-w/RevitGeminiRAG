# Purpose: This script extracts floor element data from a Revit model and outputs it as a CSV string.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Floor, FloorType, Level, ElementId, BuiltInParameter

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Element ID","Element Name","Floor Type","Level Name","Area (sq ft)"')

# Collect all Floor instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

# Iterate through floors and get data
for floor in collector:
    if isinstance(floor, Floor):
        try:
            # Get Element ID
            element_id = floor.Id.ToString()

            # Get Element Name (might be the type name by default, or user-modified)
            element_name = floor.Name

            # Get Floor Type Name
            floor_type_name = "Unknown Type"
            floor_type_element = doc.GetElement(floor.GetTypeId()) # Get the FloorType element
            if isinstance(floor_type_element, FloorType):
                floor_type_name = floor_type_element.Name

            # Get Level Name
            level_name = "Unknown Level"
            level_id = floor.LevelId
            if level_id is not None and level_id != ElementId.InvalidElementId:
                level_element = doc.GetElement(level_id)
                if isinstance(level_element, Level):
                    level_name = level_element.Name
            elif level_id == ElementId.InvalidElementId:
                 level_name = "Invalid Level ID"
            else:
                 level_name = "No Associated Level"


            # Get Area
            area_str = "N/A"
            area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                area_value_internal = area_param.AsDouble() # Internal units are sq ft
                area_str = "{:.2f}".format(area_value_internal) # Format to 2 decimal places

            # Escape quotes for CSV safety
            safe_element_id = '"' + element_id.replace('"', '""') + '"'
            safe_element_name = '"' + element_name.replace('"', '""') + '"'
            safe_floor_type_name = '"' + floor_type_name.replace('"', '""') + '"'
            safe_level_name = '"' + level_name.replace('"', '""') + '"'
            safe_area_str = '"' + area_str.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_element_id, safe_element_name, safe_floor_type_name, safe_level_name, safe_area_str]))

        except Exception as e:
            # print("# Error processing Floor {}: {}".format(floor.Id, e)) # Optional: Log errors for debugging
            pass # Silently skip floors that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::project_floors_list.csv")
    print(file_content)
else:
    print("# No Floor elements found in the project.")