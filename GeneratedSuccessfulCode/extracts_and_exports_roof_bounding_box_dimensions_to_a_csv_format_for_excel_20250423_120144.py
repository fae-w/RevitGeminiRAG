# Purpose: This script extracts and exports roof bounding box dimensions to a CSV format for Excel.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')

from Autodesk.Revit.DB import (
    Element,
    RoofBase,
    BoundingBoxXYZ,
    UnitUtils,
    UnitTypeId,
    ElementId
)
from System.Collections.Generic import List

# List to hold CSV lines for Excel export
csv_lines = []
# Add header row
csv_lines.append('"Roof ID","Roof Type","Length (mm)","Width (mm)","Height (mm)"')

# Get selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected. Please select one or more Roof elements.")
else:
    processed_count = 0
    # Iterate through selected elements
    for element_id in selected_ids:
        element = doc.GetElement(element_id)

        # Check if the element is a Roof
        if isinstance(element, RoofBase):
            try:
                # Get the bounding box (model-aligned)
                bbox = element.get_BoundingBox(None) # Pass None for model-aligned box

                if bbox and bbox.Min and bbox.Max:
                    # Calculate dimensions in internal units (feet)
                    length_ft = bbox.Max.X - bbox.Min.X
                    width_ft = bbox.Max.Y - bbox.Min.Y
                    height_ft = bbox.Max.Z - bbox.Min.Z

                    # Convert dimensions to millimeters
                    length_mm = UnitUtils.ConvertFromInternalUnits(length_ft, UnitTypeId.Millimeters)
                    width_mm = UnitUtils.ConvertFromInternalUnits(width_ft, UnitTypeId.Millimeters)
                    height_mm = UnitUtils.ConvertFromInternalUnits(height_ft, UnitTypeId.Millimeters)

                    # Get Roof ID and Type Name
                    roof_id = element.Id.IntegerValue
                    # Use the Element.Name, which often corresponds to the Type name for system families like roofs
                    roof_type_name = element.Name
                    # Escape quotes in type name for CSV safety
                    safe_type_name = '"' + roof_type_name.replace('"', '""') + '"'

                    # Format the data row, using .format() for IronPython compatibility
                    row = '{},{},{:.2f},{:.2f},{:.2f}'.format(
                        roof_id,
                        safe_type_name,
                        length_mm,
                        width_mm,
                        height_mm
                    )
                    csv_lines.append(row)
                    processed_count += 1
                else:
                    # print("# Warning: Could not retrieve valid bounding box for Roof ID {}.".format(element.Id.IntegerValue)) # Optional warning
                    pass # Silently skip if bbox is invalid

            except Exception as e:
                # print("# Error processing Roof ID {}: {}".format(element.Id.IntegerValue, str(e))) # Optional error logging
                pass # Silently skip roofs that cause errors
        # else: # Element is not a roof, ignore silently based on request
        #    pass

    # Check if we gathered any data
    if processed_count > 0:
        # Format the final output for export
        file_content = "\n".join(csv_lines)
        print("EXPORT::EXCEL::roof_boundingbox_dimensions_mm.xlsx")
        print(file_content)
    elif len(selected_ids) > 0:
         print("# No Roof elements found among the selected items.")
    # else case handled by initial check