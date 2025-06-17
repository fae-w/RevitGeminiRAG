# Purpose: This script extracts floor area and perimeter data from Revit and exports it to a CSV file.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Floor, ElementId, BuiltInParameter, UnitUtils, ForgeTypeId, UnitTypeId
import System

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Element ID","Area (sq m)","Perimeter (m)"')

# Collect all Floor instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

# Define unit types for conversion using ForgeTypeId
unit_sq_meters = UnitTypeId.SquareMeters # Use ForgeTypeId for units (Revit 2021+)
unit_meters = UnitTypeId.Meters        # Use ForgeTypeId for units (Revit 2021+)

# Iterate through floors and get data
processed_count = 0
for floor in collector:
    # Ensure it's a Floor element (redundant with OfCategory but safe)
    if not isinstance(floor, Floor):
        continue

    try:
        # Get Element ID
        element_id = floor.Id.ToString()

        # Get Area (Internal units: sq ft)
        area_str = "N/A"
        area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
        if area_param and area_param.HasValue:
            area_value_internal = area_param.AsDouble()
            # Convert area from internal units (sq ft) to square meters
            # Use ForgeTypeId with UnitUtils
            area_value_meters = UnitUtils.ConvertFromInternalUnits(area_value_internal, unit_sq_meters)
            # Format to 2 decimal places
            area_str = System.String.Format("{0:.2f}", area_value_meters) # Corrected formatting

        # Get Perimeter (Internal units: ft)
        perimeter_str = "N/A"
        perimeter_param = floor.get_Parameter(BuiltInParameter.HOST_PERIMETER_COMPUTED)
        if perimeter_param and perimeter_param.HasValue:
            perimeter_value_internal = perimeter_param.AsDouble()
            # Convert perimeter from internal units (ft) to meters
            # Use ForgeTypeId with UnitUtils
            perimeter_value_meters = UnitUtils.ConvertFromInternalUnits(perimeter_value_internal, unit_meters)
            # Format to 2 decimal places
            perimeter_str = System.String.Format("{0:.2f}", perimeter_value_meters) # Corrected formatting

        # Escape quotes for CSV safety and enclose in quotes
        safe_element_id = '"' + element_id.replace('"', '""') + '"'
        safe_area_str = '"' + area_str.replace('"', '""') + '"'
        safe_perimeter_str = '"' + perimeter_str.replace('"', '""') + '"'

        # Append data row
        csv_lines.append(','.join([safe_element_id, safe_area_str, safe_perimeter_str]))
        processed_count += 1

    except Exception as e:
        # Optional: Log errors for debugging
        # print("Error processing Floor {0}: {1}".format(floor.Id.ToString(), e.message))
        pass # Silently skip floors that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final data string
    export_data_string = "\n".join(csv_lines)
    suggested_filename = 'floor_area_perimeter_report.csv'
    file_format = 'CSV'
    # Print the export marker and data
    print("EXPORT::{0}::{1}".format(file_format, suggested_filename))
    print(export_data_string)
else:
    # Use print for messages to the user if no data is exported
    print("# INFO: No Floor elements found or processed in the project.")