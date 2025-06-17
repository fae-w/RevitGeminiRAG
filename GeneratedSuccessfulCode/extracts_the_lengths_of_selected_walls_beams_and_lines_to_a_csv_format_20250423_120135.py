# Purpose: This script extracts the lengths of selected walls, beams, and lines to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall, FamilyInstance, CurveElement,
    BuiltInParameter, UnitTypeId, UnitUtils, LocationCurve, ElementId
)
from System.Collections.Generic import List # Required for GetElementIds

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Element ID","Element Type","Length (ft)"')

# Get current selection
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected.")
else:
    processed_elements = 0
    for element_id in selected_ids:
        element = doc.GetElement(element_id)
        if not element:
            continue

        length_internal = -1.0
        element_type_name = "Unknown"

        try:
            # Attempt to get element type name first
            type_id = element.GetTypeId()
            if type_id != ElementId.InvalidElementId:
                elementType = doc.GetElement(type_id)
                if elementType:
                    element_type_name = elementType.Name

            # Check if it's a Wall
            if isinstance(element, Wall):
                length_param = element.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)
                if length_param and length_param.HasValue:
                    length_internal = length_param.AsDouble()
                elif element.Location and isinstance(element.Location, LocationCurve):
                     length_internal = element.Location.Curve.Length

            # Check if it's a Beam (Structural Framing)
            elif element.Category and element.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFraming) and isinstance(element, FamilyInstance):
                 length_param = element.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)
                 if length_param and length_param.HasValue:
                     length_internal = length_param.AsDouble()
                 elif element.Location and isinstance(element.Location, LocationCurve):
                     length_internal = element.Location.Curve.Length

            # Check if it's a Line (Model or Detail)
            elif isinstance(element, CurveElement):
                # CurveElement itself might not have a reliable "Type Name", use category name or a generic description
                element_type_name = element.Category.Name if element.Category else "Line"
                if element.GeometryCurve:
                    length_internal = element.GeometryCurve.Length

            # If length was successfully retrieved
            if length_internal >= 0.0:
                element_id_int = element.Id.IntegerValue
                length_ft_str = "{:.2f}".format(length_internal)

                # Escape quotes in type name for CSV safety
                safe_type_name = '"' + element_type_name.replace('"', '""') + '"'

                # Append data row
                csv_lines.append(','.join([str(element_id_int), safe_type_name, length_ft_str]))
                processed_elements += 1

        except Exception as e:
            # print("# Error processing element {}: {}".format(element.Id, e)) # Optional debug
            pass # Silently skip elements that cause errors or don't match criteria

    # Check if we gathered any data
    if processed_elements > 0:
        # Format the final output for export
        file_content = "\n".join(csv_lines)
        print("EXPORT::CSV::selected_element_lengths.csv")
        print(file_content)
    else:
        print("# No eligible Wall, Beam, or Line elements with retrievable lengths found in the selection.")