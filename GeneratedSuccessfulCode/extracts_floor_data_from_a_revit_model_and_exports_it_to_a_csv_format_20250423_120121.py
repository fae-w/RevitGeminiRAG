# Purpose: This script extracts floor data from a Revit model and exports it to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Floor, FloorType, Level, ElementId, BuiltInParameter
from System.Collections.Generic import List
import System

# --- Revit Document and Application Variables ---
# These are assumed to be pre-defined in the execution environment:
# doc = Current Revit Document
# uidoc = Current Revit UIDocument
# app = Revit Application
# uiapp = Revit UIApplication

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Element ID","Element Name","Floor Type","Level Name","Area (sq ft)"')

# Collect all Floor instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

# Iterate through floors and get data
processed_count = 0
for floor in collector:
    # Ensure it's a Floor element (collector might sometimes include other related elements)
    if not isinstance(floor, Floor):
        continue

    try:
        # Get Element ID
        element_id = floor.Id.ToString()

        # Get Element Name (Use Element.Name, fallback to ID)
        element_name = floor.Name
        if not element_name or element_name == "": # Check if name is None or empty string
            element_name = "ID: " + element_id

        # Get Floor Type Name
        floor_type_name = "Unknown Type"
        floor_type_id = floor.GetTypeId()
        if floor_type_id is not None and floor_type_id != ElementId.InvalidElementId:
            floor_type_element = doc.GetElement(floor_type_id) # Get the FloorType element
            if isinstance(floor_type_element, FloorType):
                 # Use Type Name Parameter first, fallback to Element.Name
                 type_name_param = floor_type_element.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                 if type_name_param and type_name_param.HasValue:
                     floor_type_name = type_name_param.AsString()
                 else:
                     floor_type_name = floor_type_element.Name

                 if not floor_type_name or floor_type_name == "":
                     floor_type_name = "Unnamed Type"
        else:
             floor_type_name = "Invalid Type ID"


        # Get Level Name
        level_name = "Unknown Level"
        level_id = floor.LevelId
        if level_id is not None and level_id != ElementId.InvalidElementId:
            level_element = doc.GetElement(level_id)
            if isinstance(level_element, Level):
                 level_name = level_element.Name
                 if not level_name or level_name == "":
                     level_name = "Unnamed Level"
        elif level_id == ElementId.InvalidElementId:
             level_name = "Invalid Level ID" # Or "Not Associated"


        # Get Area
        area_str = "N/A"
        area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
        if area_param and area_param.HasValue:
            area_value_internal = area_param.AsDouble() # Internal units are sq ft
            # Format to 2 decimal places. Using System.String.Format for IronPython compatibility.
            area_str = System.String.Format("{0:.2f}", area_value_internal)

        # Escape quotes for CSV safety and enclose in quotes
        safe_element_id = '"' + element_id.replace('"', '""') + '"'
        safe_element_name = '"' + element_name.replace('"', '""') + '"'
        safe_floor_type_name = '"' + floor_type_name.replace('"', '""') + '"'
        safe_level_name = '"' + level_name.replace('"', '""') + '"'
        safe_area_str = '"' + area_str.replace('"', '""') + '"'

        # Append data row
        csv_lines.append(','.join([safe_element_id, safe_element_name, safe_floor_type_name, safe_level_name, safe_area_str]))
        processed_count += 1

    except Exception as e:
        # Optional: Log errors for debugging - use print for RevitPythonShell or similar console
        # print("Error processing Floor {}: {}".format(floor.Id.ToString(), e))
        pass # Silently skip floors that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final data string
    export_data_string = "\n".join(csv_lines)
    suggested_filename = 'project_floors.csv'
    file_format = 'CSV'
    # Print the export marker and data
    print("EXPORT::{0}::{1}".format(file_format, suggested_filename))
    print(export_data_string)
else:
    # Use print for messages to the user if no data is exported
    print("INFO: No Floor elements found or processed in the project.")