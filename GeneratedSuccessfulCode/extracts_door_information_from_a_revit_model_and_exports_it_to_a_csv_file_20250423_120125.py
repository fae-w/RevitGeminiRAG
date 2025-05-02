# Purpose: This script extracts door information from a Revit model and exports it to a CSV file.

﻿import clr
import System
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Mark","Type Name","Level","Fire Rating"')

# Collect all Door elements (instances)
collector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

# Iterate through doors and get data
for door in collector:
    try:
        # Get Mark parameter
        mark_param = door.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
        mark = mark_param.AsString() if mark_param and mark_param.HasValue else ""

        # Get Type Name parameter (from the door's type)
        type_name = ""
        door_type_element = doc.GetElement(door.GetTypeId())
        if door_type_element:
            type_name = DB.Element.Name.__get__(door_type_element)

        # Get Level name
        level_name = "No Associated Level" # Default
        level_id = door.LevelId
        if level_id != DB.ElementId.InvalidElementId:
            level_elem = doc.GetElement(level_id)
            if level_elem and isinstance(level_elem, DB.Level):
                 level_name = DB.Element.Name.__get__(level_elem)
            else:
                # Handle cases where LevelId might point to something else or be invalid post-retrieval
                level_param = door.get_Parameter(DB.BuiltInParameter.FAMILY_LEVEL_PARAM)
                if level_param and level_param.HasValue:
                    level_name = level_param.AsValueString() # Fallback to parameter string if element lookup fails
                else:
                    level_name = "Level Not Found ({})".format(level_id.ToString())

        # Get Fire Rating parameter (Check Instance first, then Type)
        fire_rating = ""
        # Instance Parameter
        fire_rating_param_inst = door.get_Parameter(DB.BuiltInParameter.DOOR_FIRE_RATING)
        if fire_rating_param_inst and fire_rating_param_inst.HasValue and fire_rating_param_inst.AsString():
             fire_rating = fire_rating_param_inst.AsString()
        else:
            # Type Parameter
            if door_type_element:
                fire_rating_param_type = door_type_element.get_Parameter(DB.BuiltInParameter.DOOR_FIRE_RATING)
                if fire_rating_param_type and fire_rating_param_type.HasValue:
                    fire_rating = fire_rating_param_type.AsString()

        # Escape quotes for CSV safety
        safe_mark = '"' + mark.replace('"', '""') + '"'
        safe_type_name = '"' + type_name.replace('"', '""') + '"'
        safe_level_name = '"' + level_name.replace('"', '""') + '"'
        safe_fire_rating = '"' + fire_rating.replace('"', '""') + '"'

        # Append data row
        csv_lines.append(','.join([safe_mark, safe_type_name, safe_level_name, safe_fire_rating]))
    except Exception as e:
        # Optional: Log errors for debugging specific doors
        # print("# Error processing Door ID {}: {}".format(door.Id.ToString(), e))
        pass # Silently skip doors that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::door_schedule.csv")
    print(file_content)
else:
    print("# No Door elements found or processed in the project.")