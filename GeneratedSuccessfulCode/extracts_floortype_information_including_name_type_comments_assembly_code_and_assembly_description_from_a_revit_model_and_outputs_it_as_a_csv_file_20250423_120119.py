# Purpose: This script extracts FloorType information, including Name, Type Comments, Assembly Code, and Assembly Description, from a Revit model and outputs it as a CSV file.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, FloorType, BuiltInParameter

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Name","Type Comments","Assembly Code","Assembly Description"') # Added more potentially useful info

# Collect all FloorType elements
collector = FilteredElementCollector(doc).OfClass(FloorType)

# Iterate through floor types and get data
for floor_type in collector:
    if isinstance(floor_type, FloorType):
        try:
            name = floor_type.Name

            # Get Type Comments parameter
            type_comments_param = floor_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
            type_comments = type_comments_param.AsString() if type_comments_param and type_comments_param.HasValue else ""

            # Get Assembly Code parameter
            assembly_code_param = floor_type.get_Parameter(BuiltInParameter.UNIFORMAT_CODE)
            assembly_code = assembly_code_param.AsString() if assembly_code_param and assembly_code_param.HasValue else ""

            # Get Assembly Description parameter
            assembly_desc_param = floor_type.get_Parameter(BuiltInParameter.ASSEMBLY_DESCRIPTION)
            assembly_desc = assembly_desc_param.AsString() if assembly_desc_param and assembly_desc_param.HasValue else ""


            # Escape quotes for CSV safety
            safe_name = '"' + name.replace('"', '""') + '"'
            safe_comments = '"' + type_comments.replace('"', '""') + '"' if type_comments else '""'
            safe_code = '"' + assembly_code.replace('"', '""') + '"' if assembly_code else '""'
            safe_desc = '"' + assembly_desc.replace('"', '""') + '"' if assembly_desc else '""'


            # Append data row
            csv_lines.append(','.join([safe_name, safe_comments, safe_code, safe_desc]))
        except Exception as e:
            # print("# Error processing FloorType {{{{}}}}: {{{{}}}}".format(floor_type.Id, e)) # Optional: Log errors for debugging
            pass # Silently skip types that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::project_floor_types.csv")
    print(file_content)
else:
    print("# No FloorType elements found in the project.")