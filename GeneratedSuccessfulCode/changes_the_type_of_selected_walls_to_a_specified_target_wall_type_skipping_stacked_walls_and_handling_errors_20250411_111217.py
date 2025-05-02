# Purpose: This script changes the type of selected walls to a specified target wall type, skipping stacked walls and handling errors.

# Purpose: This script changes the wall type of selected Revit wall elements to a specified target wall type, handling errors and stacked walls.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections') # Required for ICollection<T>
from Autodesk.Revit.DB import FilteredElementCollector, WallType, Wall, ElementId, BuiltInParameter, ParameterFilterRuleFactory, FilterStringRule, FilterStringEquals, ElementParameterFilter
from System.Collections.Generic import List, ICollection

# Target Wall Type Name
target_wall_type_name = "Generic - 200mm Masonry"
target_wall_type = None
found_target_type = False

# Find the target WallType element
collector_types = FilteredElementCollector(doc).OfClass(WallType)
for wt in collector_types:
    # Using Element.Name property is generally reliable for type names
    if wt.Name == target_wall_type_name:
        target_wall_type = wt
        found_target_type = True
        break

# Proceed only if the target wall type was found
if found_target_type:
    # Get the current selection
    selected_ids = uidoc.Selection.GetElementIds()
    walls_changed_count = 0
    walls_skipped_subwall_count = 0
    walls_skipped_error_count = 0

    if selected_ids and selected_ids.Count > 0:
        for element_id in selected_ids:
            element = doc.GetElement(element_id)

            # Check if the element is a Wall instance
            if isinstance(element, Wall):
                wall = element
                try:
                    # Check if the wall is part of a stacked wall (cannot change type directly)
                    if wall.IsStackedWallMember:
                        # print("# Skipping Wall ID {0}: It is part of a stacked wall.".format(wall.Id)) # Debug
                        walls_skipped_subwall_count += 1
                        continue

                    # Check if the current type is already the target type
                    if wall.WallType.Id == target_wall_type.Id:
                        # print("# Skipping Wall ID {0}: It is already of type '{1}'.".format(wall.Id, target_wall_type_name)) # Debug
                        continue

                    # Attempt to change the wall type
                    wall.WallType = target_wall_type
                    walls_changed_count += 1

                except Exception as e:
                    # print("# Error changing type for Wall ID {0}: {1}".format(wall.Id, e)) # Debug
                    walls_skipped_error_count += 1
                    pass # Continue with the next selected element

        # Optional: Print summary
        # print("# Changed type for {0} walls.".format(walls_changed_count))
        # if walls_skipped_subwall_count > 0:
        #     print("# Skipped {0} walls (part of stacked walls).".format(walls_skipped_subwall_count))
        # if walls_skipped_error_count > 0:
        #     print("# Skipped {0} walls due to errors during type change.".format(walls_skipped_error_count))
    # else:
    #     print("# No elements selected.")

else:
    print("# Error: Wall Type '{0}' not found in the project.".format(target_wall_type_name))