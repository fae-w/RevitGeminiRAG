# Purpose: This script updates specified parameters of a Revit room based on its number and level.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter, Level

# Attempt to import Room class specifically from Architecture namespace
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Error: {}".format(e))

# Define the target room identifiers and new parameter values
target_room_number = "101"
target_level_name = "Level 1"
new_room_name = "Executive Office"
new_department = "Management"

# --- Find the Target Room ---
target_room = None
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in collector:
    if not isinstance(room, Room):
        continue

    # Skip unplaced rooms
    if room.Location is None:
        continue

    # Check Room Number
    number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
    if number_param and number_param.HasValue and number_param.AsString() == target_room_number:
        # Check Room Level
        room_level = None
        try:
            # SpatialElement.Level property requires API 2022+
            # For older versions, use room.get_Parameter(BuiltInParameter.ROOM_LEVEL_ID) and get the Element
            room_level = room.Level
        except AttributeError:
             # Fallback for older Revit versions if Level property doesn't exist
             level_id_param = room.get_Parameter(BuiltInParameter.ROOM_LEVEL_ID)
             if level_id_param:
                 level_id = level_id_param.AsElementId()
                 if level_id != ElementId.InvalidElementId:
                     level_element = doc.GetElement(level_id)
                     if isinstance(level_element, Level):
                         room_level = level_element

        if room_level and room_level.Name == target_level_name:
            target_room = room
            break # Found the room, stop searching

# --- Set Parameters if Room Found ---
if target_room:
    # Set Room Name
    name_param = target_room.get_Parameter(BuiltInParameter.ROOM_NAME)
    if name_param and not name_param.IsReadOnly:
        current_name = name_param.AsString()
        if current_name != new_room_name:
            name_param.Set(new_room_name)
            # print("# INFO: Set Name for Room {} on Level {} to '{}'".format(target_room_number, target_level_name, new_room_name)) # Optional info
    #else:
        # print("# WARNING: Room Name parameter not found or read-only for Room {} on Level {}".format(target_room_number, target_level_name)) # Optional warning

    # Set Department
    dept_param = target_room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)
    if dept_param and not dept_param.IsReadOnly:
        current_dept = dept_param.AsString()
        if current_dept != new_department:
            dept_param.Set(new_department)
            # print("# INFO: Set Department for Room {} on Level {} to '{}'".format(target_room_number, target_level_name, new_department)) # Optional info
    #else:
        # print("# WARNING: Room Department parameter not found or read-only for Room {} on Level {}".format(target_room_number, target_level_name)) # Optional warning
#else:
    # print("# WARNING: Room with Number '{}' on Level '{}' not found.".format(target_room_number, target_level_name)) # Optional warning