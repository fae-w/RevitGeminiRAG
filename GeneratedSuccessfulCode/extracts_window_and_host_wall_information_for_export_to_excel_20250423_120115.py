# Purpose: This script extracts window and host wall information for export to Excel.

﻿import clr
import System
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, FamilyInstance, Wall, WallType,
    BuiltInParameter, Element, ElementId
)

# List to hold CSV lines for Excel export
csv_lines = []
# Add header row
csv_lines.append('"Window Mark","Host Wall Type Mark","Host Wall Fire Rating"')

# Collect all Window FamilyInstances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()

# Iterate through windows
for window in collector:
    # Ensure it's a FamilyInstance as expected for Windows
    if isinstance(window, FamilyInstance):
        window_mark = ""
        host_wall_type_mark = "N/A"
        host_wall_fire_rating = "N/A"

        try:
            # 1. Get Window Mark (Instance Parameter)
            mark_param = window.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            if mark_param and mark_param.HasValue:
                window_mark = mark_param.AsString() if mark_param.AsString() else ""

            # 2. Get Host Element and check if it's a Wall
            host = window.Host
            if host and isinstance(host, Wall):
                wall = host
                wall_type = doc.GetElement(wall.GetTypeId())

                if wall_type and isinstance(wall_type, WallType):
                    # 2a. Get Host Wall's Type Mark (Type Parameter)
                    type_mark_param = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
                    if type_mark_param and type_mark_param.HasValue:
                        host_wall_type_mark = type_mark_param.AsString() if type_mark_param.AsString() else ""

                    # 2b. Get Host Wall's Fire Rating (Check Instance first, then Type)
                    # Instance Parameter on Wall
                    fire_rating_param_inst = wall.get_Parameter(BuiltInParameter.FIRE_RATING)
                    if fire_rating_param_inst and fire_rating_param_inst.HasValue and fire_rating_param_inst.AsString():
                         host_wall_fire_rating = fire_rating_param_inst.AsString()
                    else:
                        # Type Parameter on WallType
                        fire_rating_param_type = wall_type.get_Parameter(BuiltInParameter.FIRE_RATING)
                        if fire_rating_param_type and fire_rating_param_type.HasValue:
                            host_wall_fire_rating = fire_rating_param_type.AsString() if fire_rating_param_type.AsString() else ""
            else:
                 # Handle cases where host is not a wall or no host found
                 host_wall_type_mark = "Not Hosted by Wall"
                 host_wall_fire_rating = "Not Hosted by Wall"


            # Escape quotes for CSV safety
            safe_window_mark = '"' + window_mark.replace('"', '""') + '"'
            safe_wall_type_mark = '"' + host_wall_type_mark.replace('"', '""') + '"'
            safe_wall_fire_rating = '"' + host_wall_fire_rating.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_window_mark, safe_wall_type_mark, safe_wall_fire_rating]))

        except Exception as e:
            # Optional: Log errors for debugging specific windows
            # print("# Error processing Window ID {}: {}".format(window.Id.ToString(), e))
            # Append row with error indication if needed, or skip
            try:
                 safe_window_mark_err = '"' + window_mark.replace('"', '""') + '"' if window_mark else '""'
                 error_message = '"Error Processing: {}"'.format(str(e).replace('"', '""'))
                 csv_lines.append(','.join([safe_window_mark_err, error_message, error_message]))
            except:
                 csv_lines.append('"Error","Could not process window {}",""'.format(window.Id.ToString()))
            pass # Continue processing other windows

# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::EXCEL::window_host_wall_info.xlsx")
    print(file_content)
else:
    print("# No Window elements found or processed in the project.")