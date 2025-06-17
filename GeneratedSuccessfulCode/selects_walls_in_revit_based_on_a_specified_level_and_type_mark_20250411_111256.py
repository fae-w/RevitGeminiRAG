# Purpose: This script selects walls in Revit based on a specified level and type mark.

# Purpose: This script selects walls on a specific level and with a specific type mark in Revit.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    Level,
    ElementId,
    BuiltInParameter,
    ElementLevelFilter
)
from System.Collections.Generic import List

# --- Configuration ---
target_level_name = "Level 3"
target_type_mark = "W1"
# --- End Configuration ---

# Find the target Level ElementId
target_level_id = ElementId.InvalidElementId
level_collector = FilteredElementCollector(doc).OfClass(Level)
for level in level_collector:
    if level.Name == target_level_name:
        target_level_id = level.Id
        break

walls_to_select_ids = []

if target_level_id != ElementId.InvalidElementId:
    # Create a level filter
    level_filter = ElementLevelFilter(target_level_id)

    # Create a collector for walls, filtered by level
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls)
    wall_collector = collector.WherePasses(level_filter).WhereElementIsNotElementType()

    # Iterate through the collected walls
    for wall in wall_collector:
        # Double check it's a Wall instance, although filters should handle this
        if isinstance(wall, Wall):
            try:
                # Get the WallType
                wall_type = doc.GetElement(wall.GetTypeId())
                if wall_type:
                    # Get the Type Mark parameter from the WallType
                    type_mark_param = wall_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
                    if type_mark_param and type_mark_param.HasValue:
                        type_mark_value = type_mark_param.AsString()
                        # Check if the Type Mark matches the target
                        if type_mark_value == target_type_mark:
                            walls_to_select_ids.append(wall.Id)
            except Exception as e:
                # print("# Debug: Skipping element {0}, Error: {1}".format(wall.Id, e)) # Escaped
                pass # Silently skip walls that cause errors

    # Select the walls if any were found
    if walls_to_select_ids:
        selection_list = List[ElementId](walls_to_select_ids)
        try:
            uidoc.Selection.SetElementIds(selection_list)
            # print("# Selected {0} walls on '{1}' with Type Mark '{2}'.".format(len(walls_to_select_ids), target_level_name, target_type_mark)) # Escaped
        except Exception as sel_ex:
            print("# Error setting selection: {}".format(sel_ex)) # Escaped
    else:
        print("# No walls found matching the criteria (Level='{}', Type Mark='{}').".format(target_level_name, target_type_mark)) # Escaped
else:
    print("# Error: Level named '{}' not found in the document.".format(target_level_name)) # Escaped