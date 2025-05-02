# Purpose: This script calculates the total volume of concrete structural columns in a Revit model.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilyInstance, ElementId
from Autodesk.Revit.DB import BuiltInParameter
# Import necessary classes from the Structure namespace
from Autodesk.Revit.DB.Structure import StructuralMaterialType, StructuralMaterialTypeFilter

# Initialize total volume
total_concrete_volume_cubic_feet = 0.0
column_count = 0

# Create a filter for elements with Structural Material Type set to Concrete
# This filters based on the instance's 'Structural Material Type' parameter.
concrete_material_filter = StructuralMaterialTypeFilter(StructuralMaterialType.Concrete)

# Create a collector for Structural Column instances and apply the concrete filter
collector = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_StructuralColumns)\
    .WhereElementIsNotElementType()\
    .WherePasses(concrete_material_filter)

# Iterate through the collected concrete columns
for column in collector:
    if isinstance(column, FamilyInstance):
        try:
            # Get the volume parameter (HOST_VOLUME_COMPUTED is common for columns)
            volume_param = column.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED)

            if volume_param and volume_param.HasValue:
                # Get volume in Revit's internal units (cubic feet)
                volume = volume_param.AsDouble()
                total_concrete_volume_cubic_feet += volume
                column_count += 1
            else:
                # Optional: Log columns without volume parameter
                # print("# Column ID {{}} is Concrete but has no Volume parameter.".format(column.Id))
                pass
        except Exception as e:
            # Optional: Log errors for specific elements
            # print("# Error processing Column ID {{}}: {{}}".format(column.Id, str(e)))
            pass # Continue to the next column

# Prepare the data for Excel export (single value)
# Header row
header = "Total Concrete Volume (cubic feet)"
# Data row - format volume to 2 decimal places
data_row = "{:.2f}".format(total_concrete_volume_cubic_feet)

# Combine header and data for CSV-like structure
file_content = "{}\n{}".format(header, data_row)

# Print the export command and data
print("EXPORT::EXCEL::concrete_column_total_volume.xlsx")
print(file_content)

# Optional: Print a message if no concrete columns were found
if column_count == 0:
    print("# No concrete Structural Columns found in the project.")