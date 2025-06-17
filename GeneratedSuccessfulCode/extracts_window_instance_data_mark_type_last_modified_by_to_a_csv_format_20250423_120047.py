# Purpose: This script extracts window instance data (Mark, Type, Last Modified By) to a CSV format.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    Element,
    FamilyInstance,
    ElementType,
    ElementId
)
# System references are not strictly needed here as we cannot filter by time accurately
# clr.AddReference('System')
# from System import DateTime, TimeSpan

# CSV data storage
csv_lines = []
# Add header row
csv_lines.append('"Mark","Type","Last Modified By"')

# Note: Filtering elements based on modification time within the last 24 hours
# using standard Revit parameters is generally unreliable.
# The 'Last Modified By' parameter (BuiltInParameter.EDITED_BY) reflects the user
# who last *saved to central* after modifying the element in a workshared model.
# It does not store the actual timestamp of the modification.
# This script lists all windows and includes the 'Last Modified By' information available.

# Collector for window instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()

# Iterate through windows
for window in collector:
    # Ensure the element is a FamilyInstance (covers most standard windows)
    if isinstance(window, FamilyInstance):
        mark_val = "N/A"
        type_name = "N/A"
        last_modified_by = "N/A"

        try:
            # 1. Get Mark parameter
            mark_param = window.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            if mark_param and mark_param.HasValue:
                mark_val = mark_param.AsString()
                if not mark_val: # Handle empty string marks explicitly if needed
                    mark_val = "<blank>" # Or keep as "" based on preference

            # 2. Get Type Name
            type_id = window.GetTypeId()
            if type_id != ElementId.InvalidElementId:
                window_type_elem = doc.GetElement(type_id)
                if window_type_elem:
                    # Use BuiltInParameter for Type Name for robustness
                    type_name_param = window_type_elem.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                    if type_name_param and type_name_param.HasValue:
                        type_name = type_name_param.AsString()
                    elif hasattr(window_type_elem, 'Name'): # Fallback to Name property
                        type_name = window_type_elem.Name
                    # If type name is still None or empty, keep "N/A"
                    if not type_name:
                         type_name = "N/A"

            # 3. Get Last Modified By parameter (Worksharing specific)
            modified_by_param = window.get_Parameter(BuiltInParameter.EDITED_BY)
            if modified_by_param and modified_by_param.HasValue:
                last_modified_by = modified_by_param.AsString()
                if not last_modified_by: # Handle case where parameter exists but value is empty
                    last_modified_by = "<not recorded>"
            else:
                # Parameter might not exist in non-workshared files or for certain elements
                last_modified_by = "<not available>"

            # Escape values for CSV formatting (handle quotes within values)
            safe_mark = '"' + str(mark_val).replace('"', '""') + '"'
            safe_type_name = '"' + str(type_name).replace('"', '""') + '"'
            safe_last_modified_by = '"' + str(last_modified_by).replace('"', '""') + '"'

            # Add row to list
            csv_lines.append(','.join([safe_mark, safe_type_name, safe_last_modified_by]))

        except Exception as e:
            # Optionally log errors for specific elements, but keep script running
            # print("Error processing window {}: {}".format(window.Id, e))
            pass # Skip elements that cause an error during data extraction

# Prepare and print export data if any windows were found
if len(csv_lines) > 1: # Check if any data rows were added (more than just the header)
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::windows_last_modified_by.csv")
    print(file_content)
else:
    # If no windows were found or processed, print a message
    print("# No window instances found in the document.")