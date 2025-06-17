# Purpose: This script modifies the 'Room Bounding' parameter of specific Revit walls based on their function.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    WallType,
    WallFunction,
    BuiltInParameter,
    Element
)

# --- Configuration ---
# Target wall functions to modify
# NOTE: WallFunction.Bulkhead does not exist in the Revit API enum.
# Only Soffit will be targeted based on the standard 'Function' type parameter.
# If 'Bulkhead' walls need identification by other means (e.g., Type Name),
# the script logic would need significant changes.
target_functions = [WallFunction.Soffit]
# Target value for 'Room Bounding' parameter (0 = False, 1 = True)
target_room_bounding_value = 0

# --- Script Core Logic ---
wall_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

modified_count = 0
already_set_count = 0
skipped_no_param_count = 0
skipped_readonly_count = 0
skipped_wrong_function_count = 0
error_count = 0

for wall in wall_collector:
    # Ensure it's a Wall instance (though filter should handle this)
    if not isinstance(wall, Wall):
        continue

    try:
        # Get the WallType associated with the Wall instance
        wall_type = doc.GetElement(wall.GetTypeId())
        if not isinstance(wall_type, WallType):
             # This might happen for specific wall types or corrupted elements
             error_count += 1
             continue

        # Check if the wall type's function matches the target functions
        # Wall Function is a Type Parameter
        wall_function_param = wall_type.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
        if wall_function_param and wall_function_param.AsInteger() in [int(f) for f in target_functions]:
            # Get the 'Room Bounding' parameter (Instance Parameter)
            room_bounding_param = wall.get_Parameter(BuiltInParameter.WALL_ATTR_ROOM_BOUNDING)

            if room_bounding_param:
                if not room_bounding_param.IsReadOnly:
                    # Check current value before setting
                    current_value = room_bounding_param.AsInteger()
                    if current_value != target_room_bounding_value:
                        # Set the parameter value (0 for False)
                        room_bounding_param.Set(target_room_bounding_value)
                        modified_count += 1
                    else:
                        # Parameter already has the desired value
                        already_set_count += 1
                else:
                    # Parameter is read-only, cannot modify
                    skipped_readonly_count += 1
            else:
                # Parameter does not exist on this wall instance
                skipped_no_param_count += 1
        elif wall_function_param:
             # Wall function does not match targets
             skipped_wrong_function_count += 1
        else:
             # Wall Type does not have a Function parameter (unlikely for standard walls)
             error_count += 1


    except Exception as e:
        # Log errors encountered during processing a specific wall
        # Use basic printing compatible with IronPython 2.7 and Revit consoles
        print("# Error processing Wall ID {0}: {1}".format(wall.Id.ToString(), str(e)))
        error_count += 1

# --- Optional Summary Output (Keep commented out per instructions) ---
# print("--- Room Bounding Update Summary ---")
# print("Walls processed (approximate): {0}".format(wall_collector.GetElementCount())) # Filtered count
# print("Walls modified (Room Bounding set to False): {0}".format(modified_count))
# print("Walls skipped (Already False): {0}".format(already_set_count))
# print("Walls skipped (Wrong Function): {0}".format(skipped_wrong_function_count))
# print("Walls skipped (Parameter ReadOnly): {0}".format(skipped_readonly_count))
# print("Walls skipped (Parameter Not Found): {0}".format(skipped_no_param_count))
# print("Errors encountered: {0}".format(error_count))