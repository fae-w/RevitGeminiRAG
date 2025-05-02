# Purpose: This script exports a CSV report of used furniture types and their manufacturers from a Revit model.

﻿import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import HashSet # For unique IDs

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilyInstance, FamilySymbol, ElementType, BuiltInParameter, ElementId

# Set to store unique FamilySymbol IDs of used furniture
used_furniture_type_ids = HashSet[ElementId]()

# Collect all furniture instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType()

# Iterate through instances to find unique types used
for instance in collector:
    if isinstance(instance, FamilyInstance):
        type_id = instance.GetTypeId()
        if type_id is not None and type_id != ElementId.InvalidElementId:
            used_furniture_type_ids.Add(type_id)

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Family Name","Type Name","Manufacturer"')

# Iterate through the unique furniture type IDs found
for type_id in used_furniture_type_ids:
    family_symbol = doc.GetElement(type_id)
    if isinstance(family_symbol, FamilySymbol):
        try:
            # Get Family Name
            family_name = "Unknown Family"
            if family_symbol.Family is not None:
                family_name = family_symbol.Family.Name

            # Get Type Name
            type_name = family_symbol.Name

            # Get Manufacturer parameter
            manufacturer_param = family_symbol.get_Parameter(BuiltInParameter.ALL_MODEL_MANUFACTURER)
            manufacturer = manufacturer_param.AsString() if manufacturer_param and manufacturer_param.HasValue else ""

            # Escape quotes for CSV safety
            safe_family_name = '"' + family_name.replace('"', '""') + '"'
            safe_type_name = '"' + type_name.replace('"', '""') + '"'
            safe_manufacturer = '"' + manufacturer.replace('"', '""') + '"' if manufacturer else '""'

            # Append data row
            csv_lines.append(','.join([safe_family_name, safe_type_name, safe_manufacturer]))
        except Exception as e:
            # print("# Error processing Furniture Type ID {}: {}".format(type_id.IntegerValue, e)) # Optional debug log
            pass # Silently skip types that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::used_furniture_types_report.csv")
    print(file_content)
else:
    print("# No used Furniture instances found in the project.")