# Purpose: This script extracts Mark, Base Level, and Top Level information from structural columns in a Revit model and outputs it as a CSV.

﻿import clr
import System
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    Level,
    BuiltInParameter,
    ElementId,
    Element
)
# Import Structure namespace for StructuralType comparison if needed, though category filter might suffice
# from Autodesk.Revit.DB import Structure

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Mark","Base Level Name","Top Level Name"')

# Function to safely get level name
def get_level_name(doc, level_id):
    if level_id and level_id != ElementId.InvalidElementId:
        level_elem = doc.GetElement(level_id)
        if level_elem and isinstance(level_elem, Level):
            return Element.Name.__get__(level_elem)
        else:
            return "Level Not Found ({})".format(level_id.ToString())
    else:
        return "No Associated Level"

# Collect all Structural Column instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType()

# Iterate through columns and get data
for column in collector:
    if isinstance(column, FamilyInstance):
        try:
            # Get Mark parameter
            mark_param = column.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            mark = mark_param.AsString() if mark_param and mark_param.HasValue else ""

            # Get Base Level Name
            base_level_param = column.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
            base_level_id = ElementId.InvalidElementId
            if base_level_param and base_level_param.HasValue:
                base_level_id = base_level_param.AsElementId()
            base_level_name = get_level_name(doc, base_level_id)

            # Get Top Level Name
            top_level_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
            top_level_id = ElementId.InvalidElementId
            if top_level_param and top_level_param.HasValue:
                top_level_id = top_level_param.AsElementId()
            top_level_name = get_level_name(doc, top_level_id)

            # Escape quotes for CSV safety
            safe_mark = '"' + mark.replace('"', '""') + '"'
            safe_base_level_name = '"' + base_level_name.replace('"', '""') + '"'
            safe_top_level_name = '"' + top_level_name.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_mark, safe_base_level_name, safe_top_level_name]))

        except Exception as e:
            # Optional: Log errors for debugging specific columns
            # print("# Error processing Column ID {}: {}".format(column.Id.ToString(), e))
            pass # Silently skip columns that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::structural_column_levels.csv")
    print(file_content)
else:
    print("# No Structural Column elements found or processed in the project.")