# Purpose: This script extracts window mark and host wall type mark information and outputs it to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, FamilyInstance,
    Wall, WallType, BuiltInParameter, Element, ElementId
)

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Window Mark","Host Wall Type Mark"')

# Collect all Window FamilyInstances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()

# Iterate through windows
for window in collector:
    # Ensure it's a FamilyInstance as expected for Windows
    if isinstance(window, FamilyInstance):
        window_mark = "N/A"
        host_wall_type_mark = "N/A"

        try:
            # 1. Get Window Mark (Instance Parameter)
            mark_param = window.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            if mark_param and mark_param.HasValue:
                window_mark = mark_param.AsString() if mark_param.AsString() else "" # Handle empty/null string

            # 2. Get Host Element and check if it's a Wall
            host = window.Host
            if host and isinstance(host, Wall):
                wall = host
                # Get the WallType element from the Wall instance
                wall_type = doc.GetElement(wall.GetTypeId())

                if wall_type and isinstance(wall_type, WallType):
                    # 2a. Get Host Wall's Type Mark (Type Parameter)
                    type_mark_param = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
                    if type_mark_param and type_mark_param.HasValue:
                        host_wall_type_mark = type_mark_param.AsString() if type_mark_param.AsString() else "" # Handle empty/null string
                    else:
                         # Parameter exists on type but has no value or cannot be read
                         host_wall_type_mark = "Type Mark Not Set"
                else:
                    # Could not retrieve a valid WallType from the host Wall's TypeId
                    host_wall_type_mark = "Host Wall Type Invalid"
            elif host:
                 # The host element exists but is not a Wall
                 host_wall_type_mark = "Host Not a Wall ({})".format(host.Category.Name if host.Category else "Unknown Category")
            else:
                 # The window does not have a host assigned
                 host_wall_type_mark = "No Host Found"


            # Escape quotes for CSV safety
            safe_window_mark = '"' + window_mark.replace('"', '""') + '"'
            safe_host_wall_type_mark = '"' + host_wall_type_mark.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_window_mark, safe_host_wall_type_mark]))

        except Exception as e:
            # Optional: Log errors for debugging specific windows
            # print("# Error processing Window ID {}: {}".format(window.Id.ToString(), e))
            # Append row with error indication if needed
            try:
                 safe_window_mark_err = '"' + window_mark.replace('"', '""') + '"' if window_mark else '""'
                 error_message = '"Error Processing: {}"'.format(str(e).replace('"', '""'))
                 csv_lines.append(','.join([safe_window_mark_err, error_message]))
            except:
                 csv_lines.append('"Error","Could not process window {}"'.format(window.Id.ToString()))
            pass # Continue processing other windows

# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::window_host_wall_type_mark.csv")
    print(file_content)
else:
    print("# No Window elements found or processed in the project.")