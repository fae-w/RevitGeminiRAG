# Purpose: This script extracts the gross volume of selected mass elements in Revit and exports the data to a CSV format for Excel.

﻿import clr
clr.AddReference('RevitAPI')
import System # Required for String formatting

# Import necessary classes from Revit API namespaces
from Autodesk.Revit.DB import (
    Element,
    ElementId,
    MassInstanceUtils,
    BuiltInCategory,
    Category
)
# System.Collections.Generic is often implicitly handled by IronPython, but explicit can be safer if needed
# from System.Collections.Generic import List

# List to hold CSV data rows for Excel export
csv_lines = []

# Add header row
csv_lines.append('"Element ID","Volume (cu ft)"')

# Get selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

# Check if any elements are selected
if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected.")
else:
    processed_mass_count = 0
    # Iterate through selected elements
    for element_id in selected_ids:
        element = doc.GetElement(element_id)
        if not element:
            continue

        # Check if the element is a Mass element (check category)
        element_category = element.Category
        if element_category and element_category.Id.IntegerValue == int(BuiltInCategory.OST_Mass):
            try:
                # Get the gross volume using MassInstanceUtils
                # This method specifically works with mass instances
                volume_cuft = MassInstanceUtils.GetGrossVolume(doc, element_id)

                # Format the data for CSV
                element_id_str = str(element_id.IntegerValue)
                # Use System.String.Format for reliable decimal formatting
                volume_str = System.String.Format("{0:.2f}", volume_cuft)

                # Escape quotes just in case (though unlikely for ID and volume)
                safe_id = '"' + element_id_str.replace('"', '""') + '"'
                safe_volume = '"' + volume_str.replace('"', '""') + '"'

                # Append data row
                csv_lines.append(safe_id + ',' + safe_volume)
                processed_mass_count += 1

            except Exception as e:
                # Handle potential errors, e.g., if GetGrossVolume fails for some reason
                # This might happen if the element is a mass but not a valid instance for volume calculation
                # print("# Could not get volume for Mass element ID {0}: {1}".format(element_id.IntegerValue, e)) # Debugging message
                # Append error row or skip
                error_id_str = str(element_id.IntegerValue)
                safe_id_err = '"' + error_id_str.replace('"', '""') + '"'
                csv_lines.append(safe_id_err + ',"Error: Could not calculate volume"')


    # Check if any mass data rows were actually generated
    if processed_mass_count > 0 and len(csv_lines) > 1:
        # Join lines into a single string for export
        file_content = "\n".join(csv_lines)
        # Print the export marker and data for Excel
        print("EXPORT::EXCEL::selected_mass_volumes.xlsx")
        print(file_content)
    elif processed_mass_count == 0 and len(selected_ids) > 0:
         # Message if elements were selected but none were valid masses or had errors
         print("# No valid Mass elements found among the selection, or volume calculation failed for all selected masses.")
    # Implicitly handles the case where selection was empty initially (message printed earlier)