# Purpose: This script extracts door information with a specific fire rating to a CSV format.

﻿import clr
import System
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB

# Target fire rating value
target_fire_rating = "90 minutes"

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Mark","Type Name","Level"')

# Collect all Door elements (instances)
collector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

# Iterate through doors
for door in collector:
    fire_rating_value = ""
    door_type_element = None

    try:
        # Check Instance Parameter first
        fire_rating_param_inst = door.get_Parameter(DB.BuiltInParameter.DOOR_FIRE_RATING)
        if fire_rating_param_inst and fire_rating_param_inst.HasValue and fire_rating_param_inst.AsString():
             fire_rating_value = fire_rating_param_inst.AsString()
        else:
            # Check Type Parameter if instance parameter is not found or empty
            door_type_id = door.GetTypeId()
            if door_type_id != DB.ElementId.InvalidElementId:
                 door_type_element = doc.GetElement(door_type_id)
                 if door_type_element:
                     fire_rating_param_type = door_type_element.get_Parameter(DB.BuiltInParameter.DOOR_FIRE_RATING)
                     if fire_rating_param_type and fire_rating_param_type.HasValue:
                         fire_rating_value = fire_rating_param_type.AsString()

        # Check if the fire rating matches the target value
        if fire_rating_value == target_fire_rating:
            # Get Mark parameter
            mark_param = door.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
            mark = mark_param.AsString() if mark_param and mark_param.HasValue else ""

            # Get Type Name parameter (from the door's type)
            type_name = ""
            if not door_type_element: # Get type element if not already fetched
                door_type_id = door.GetTypeId()
                if door_type_id != DB.ElementId.InvalidElementId:
                    door_type_element = doc.GetElement(door_type_id)

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
                    # Fallback to parameter string if element lookup fails or is not a Level
                    level_param = door.get_Parameter(DB.BuiltInParameter.FAMILY_LEVEL_PARAM)
                    if level_param and level_param.HasValue:
                        level_name = level_param.AsValueString()
                    else:
                         level_name = "Level Not Found ({})".format(level_id.ToString())

            # Escape quotes for CSV safety
            safe_mark = '"' + mark.replace('"', '""') + '"'
            safe_type_name = '"' + type_name.replace('"', '""') + '"'
            safe_level_name = '"' + level_name.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_mark, safe_type_name, safe_level_name]))

    except Exception as e:
        # Optional: Log errors for debugging specific doors
        # print("# Error processing Door ID {}: {}".format(door.Id.ToString(), e))
        pass # Silently skip doors that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::doors_90min_fire_rating.csv")
    print(file_content)
else:
    print("# No doors found with 'Fire Rating' equal to '{}'.".format(target_fire_rating))