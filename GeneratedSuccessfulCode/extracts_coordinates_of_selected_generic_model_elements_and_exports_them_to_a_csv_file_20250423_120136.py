# Purpose: This script extracts coordinates of selected generic model elements and exports them to a CSV file.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, GenericForm, LocationPoint, XYZ,
    Element, ElementId, BuiltInParameter
)
from System.Collections.Generic import List
import System

# --- Revit Document and Application Variables ---
# These are assumed to be pre-defined in the execution environment:
# doc = Current Revit Document
# uidoc = Current Revit UIDocument
# app = Revit Application
# uiapp = Revit UIApplication

# Get selected element IDs
try:
    selected_ids = uidoc.Selection.GetElementIds()
except Exception as e:
    print("# Error: Failed to get selected element IDs. {}".format(e))
    selected_ids = List[ElementId]() # Assign empty list to prevent further errors

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Element ID","X (Project Base Point)","Y (Project Base Point)","Z (Project Base Point)"')

processed_count = 0

# Iterate through selected elements
if selected_ids and selected_ids.Count > 0:
    for element_id in selected_ids:
        try:
            element = doc.GetElement(element_id)
            if element is None:
                continue

            # Check if it's a Generic Model using Category
            element_category = element.Category
            if element_category and element_category.Id.IntegerValue == BuiltInCategory.OST_GenericModel.IntegerValue:
                location = element.Location
                # Check if the element has a point location
                if isinstance(location, LocationPoint):
                    try:
                        point = location.Point # This point is relative to the project internal origin (usually the Project Base Point)
                        x_coord = point.X
                        y_coord = point.Y
                        z_coord = point.Z

                        # Format coordinates (e.g., 3 decimal places) using System.String.Format for IronPython
                        x_str = System.String.Format("{0:.3f}", x_coord)
                        y_str = System.String.Format("{0:.3f}", y_coord)
                        z_str = System.String.Format("{0:.3f}", z_coord)

                        # Get Element ID as string
                        element_id_str = element.Id.ToString()

                        # Escape quotes for CSV safety and enclose in quotes
                        safe_element_id = '"' + element_id_str.replace('"', '""') + '"'
                        safe_x = '"' + x_str.replace('"', '""') + '"'
                        safe_y = '"' + y_str.replace('"', '""') + '"'
                        safe_z = '"' + z_str.replace('"', '""') + '"'

                        # Append data row
                        csv_lines.append(','.join([safe_element_id, safe_x, safe_y, safe_z]))
                        processed_count += 1
                    except Exception as loc_ex:
                        # Handle potential errors getting location point or coordinates
                        # print("# DEBUG: Error processing location for element {}: {}".format(element.Id.ToString(), loc_ex))
                        pass # Silently skip elements where location retrieval fails
                # else: # Optionally inform if a selected Generic Model doesn't have a LocationPoint
                    # print("# INFO: Selected Generic Model Element {} does not have a single point location.".format(element.Id.ToString()))

        except Exception as el_ex:
            # Handle potential errors getting element or its category
            # print("# DEBUG: Error processing element ID {}: {}".format(element_id.ToString(), el_ex))
            pass # Silently skip elements that cause errors during processing

# Check if we gathered any data
if processed_count > 0:
    # Format the final data string
    export_data_string = "\n".join(csv_lines)
    suggested_filename = 'generic_model_coordinates.csv'
    file_format = 'CSV'
    # Print the export marker and data
    print("EXPORT::{0}::{1}".format(file_format, suggested_filename))
    print(export_data_string)
else:
    # Use print for messages to the user if no data is exported
    print("# INFO: No selected Generic Model elements with point locations found or processed.")