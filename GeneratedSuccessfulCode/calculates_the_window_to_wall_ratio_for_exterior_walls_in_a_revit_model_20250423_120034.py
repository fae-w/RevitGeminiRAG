# Purpose: This script calculates the window-to-wall ratio for exterior walls in a Revit model.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall, FamilyInstance,
    BuiltInParameter, WallFunction, HostObjectUtils, ElementId, StorageType
)
import math # For checking values close to zero

# Dictionary to store wall areas {wall_element_id: {'gross_area': float, 'window_area': float}}
wall_data = {}

# Collect all Wall instances
wall_collector = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

# --- Pass 1: Identify exterior walls and get their gross area ---
for wall in wall_collector:
    if not isinstance(wall, Wall):
        continue
    try:
        # Check if wall is exterior using instance parameter
        function_param = wall.get_Parameter(BuiltInParameter.WALL_FUNCTION_PARAM)
        is_exterior = False
        if function_param and function_param.HasValue and function_param.StorageType == StorageType.Integer:
            if function_param.AsInteger() == int(WallFunction.Exterior):
                is_exterior = True

        if is_exterior:
            # Get gross wall area (area before openings subtraction)
            area_param = wall.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            gross_area = 0.0
            if area_param and area_param.HasValue and area_param.StorageType == StorageType.Double:
                gross_area = area_param.AsDouble()

            # Initialize data for this wall if it has a positive area
            if gross_area > 1e-6: # Use tolerance for floating point comparison
                 wall_data[wall.Id] = {'gross_area': gross_area, 'window_area': 0.0}

    except Exception as e:
        # print("Error processing wall {}: {}".format(wall.Id, e)) # Debug info if needed
        pass # Silently skip walls that cause errors

# --- Pass 2: Find windows hosted in these exterior walls and sum their areas ---
for wall_id in wall_data.keys():
    wall = doc.GetElement(wall_id)
    if not wall:
        continue

    try:
        # Find elements hosted by this wall (windows, doors, openings, etc.)
        hosted_element_ids = HostObjectUtils.GetHostedElementIds(wall)
        if not hosted_element_ids:
            continue

        for hosted_id in hosted_element_ids:
            hosted_element = doc.GetElement(hosted_id)

            # Check if the hosted element is a Window
            if hosted_element and hosted_element.Category and \
               hosted_element.Category.Id.IntegerValue == int(BuiltInCategory.OST_Windows):

                window_area = 0.0
                # Calculate window area from Width and Height parameters
                # These are common instance parameters for windows
                width_param = hosted_element.get_Parameter(BuiltInParameter.WINDOW_WIDTH)
                height_param = hosted_element.get_Parameter(BuiltInParameter.WINDOW_HEIGHT)

                # Ensure parameters exist, have values, and are doubles
                if (width_param and width_param.HasValue and width_param.StorageType == StorageType.Double and
                    height_param and height_param.HasValue and height_param.StorageType == StorageType.Double):

                    width = width_param.AsDouble()
                    height = height_param.AsDouble()

                    # Ensure width and height are positive before calculating area
                    if width > 1e-6 and height > 1e-6:
                        window_area = width * height

                # Add calculated window area to the host wall's total
                # Check if wall_id is still in wall_data (should be)
                if wall_id in wall_data:
                    wall_data[wall_id]['window_area'] += window_area

    except Exception as e:
         # print("Error processing hosted elements for wall {}: {}".format(wall.Id, e)) # Debug info if needed
         pass # Skip walls if error occurs finding/processing hosted elements

# --- Prepare data for export ---
csv_lines = []
# Add header row (CSV format for Excel)
csv_lines.append("Wall ID,Window-to-Wall Ratio")

# Calculate WWR and format output rows
# Sort by Wall ID for consistent output
sorted_wall_ids = sorted(wall_data.keys(), key=lambda x: x.IntegerValue)

for wall_id in sorted_wall_ids:
    data = wall_data[wall_id]
    gross_area = data['gross_area']
    total_window_area = data['window_area']

    wwr = 0.0
    # Calculate ratio, avoid division by zero or near-zero
    if gross_area > 1e-6:
        wwr = total_window_area / gross_area
        # WWR should ideally be between 0 and 1, but report calculated value unless negative
        wwr = max(0.0, wwr)

    # Format the row: Wall Element ID (Integer), WWR (3 decimal places)
    csv_lines.append("{0},{1:.3f}".format(wall_id.IntegerValue, wwr))


# --- Print Export block ---
if len(csv_lines) > 1: # Check if any data rows were added beyond the header
    file_content = "\n".join(csv_lines)
    # Specify EXCEL format, filename suggestion, and print data
    print("EXPORT::EXCEL::wall_wwr_report.xlsx")
    print(file_content)
else:
    # If no exterior walls or no windows in exterior walls were found/processed
    print("# No exterior walls with windows found or processed successfully.")