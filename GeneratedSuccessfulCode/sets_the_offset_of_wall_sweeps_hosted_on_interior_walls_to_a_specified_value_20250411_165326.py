# Purpose: This script sets the offset of wall sweeps hosted on interior walls to a specified value.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallSweep,
    Wall,
    WallType,
    BuiltInCategory,
    BuiltInParameter,
    Parameter,
    WallFunction,
    Element
)

# --- Parameters ---
target_wall_function = WallFunction.Interior
target_offset_value = 0.0 # Internal units (feet)

# --- Script Logic ---
sweep_collector = FilteredElementCollector(doc).OfClass(WallSweep)

modified_count = 0
already_set_count = 0
skipped_wrong_wall_func_count = 0
skipped_no_host_wall_count = 0
skipped_no_param_count = 0
skipped_readonly_count = 0
error_count = 0

for sweep in sweep_collector:
    if not isinstance(sweep, WallSweep):
        continue

    try:
        host_element = doc.GetElement(sweep.HostId)
        if not isinstance(host_element, Wall):
            skipped_no_host_wall_count += 1
            continue # Skip if host is not a Wall

        host_wall = host_element
        wall_type = doc.GetElement(host_wall.GetTypeId())

        if not isinstance(wall_type, WallType):
            # This might happen for specific wall types or corrupted elements
            error_count += 1
            continue

        # Get the Wall Function (Type Parameter)
        function_param = wall_type.get_Parameter(BuiltInParameter.FUNCTION_PARAM)

        if function_param and function_param.AsInteger() == int(target_wall_function):
            # Host wall function matches, now check the sweep's offset parameter
            # Assuming 'Offset' refers to 'Offset From Level' (WALL_SWEEP_OFFSET)
            offset_param = sweep.get_Parameter(BuiltInParameter.WALL_SWEEP_OFFSET)

            if offset_param:
                if not offset_param.IsReadOnly:
                    current_value = offset_param.AsDouble()
                    # Use a small tolerance for floating point comparison
                    if abs(current_value - target_offset_value) > 1e-6:
                        offset_param.Set(target_offset_value)
                        modified_count += 1
                    else:
                        already_set_count += 1
                else:
                    skipped_readonly_count += 1
            else:
                # Try 'Offset From Wall' as an alternative, though less likely intended
                offset_param_alt = sweep.get_Parameter(BuiltInParameter.WALL_SWEEP_WALL_OFFSET) # Offset From Wall
                if offset_param_alt:
                    if not offset_param_alt.IsReadOnly:
                        current_value = offset_param_alt.AsDouble()
                        if abs(current_value - target_offset_value) > 1e-6:
                           # Decide if this parameter should also be set to 0.
                           # Assuming ONLY "Offset From Level" was intended based on the simpler term "Offset"
                           # print("# Info: Found 'Offset From Wall' parameter on Sweep ID {0}, but skipping as 'Offset From Level' was assumed.".format(sweep.Id))
                           skipped_no_param_count += 1 # Count as skipped because primary wasn't found
                        else:
                            # If this parameter was already 0, it doesn't count towards 'already_set_count' unless specified.
                            skipped_no_param_count += 1
                    else:
                         skipped_readonly_count += 1 # Count as read-only if alt param found but read-only
                else:
                    skipped_no_param_count += 1 # Neither parameter found

        elif function_param:
            # Wall function does not match target
            skipped_wrong_wall_func_count += 1
        else:
            # Wall type lacks the function parameter (unlikely for standard walls)
            error_count += 1

    except Exception as e:
        # Log errors encountered during processing a specific sweep
        print("# Error processing Wall Sweep ID {0}: {1}".format(sweep.Id.ToString(), str(e)))
        error_count += 1

# --- Optional Summary Output (Keep commented out per instructions) ---
# print("--- Wall Sweep Offset Update Summary ---")
# print("Wall Sweeps processed (approximate): {0}".format(sweep_collector.GetElementCount()))
# print("Sweeps modified ('Offset From Level' set to {0}): {1}".format(target_offset_value, modified_count))
# print("Sweeps skipped (Already set): {0}".format(already_set_count))
# print("Sweeps skipped (Host Wall not Interior Partition): {0}".format(skipped_wrong_wall_func_count))
# print("Sweeps skipped (Host not a Wall): {0}".format(skipped_no_host_wall_count))
# print("Sweeps skipped (Offset Parameter Not Found): {0}".format(skipped_no_param_count))
# print("Sweeps skipped (Offset Parameter ReadOnly): {0}".format(skipped_readonly_count))
# print("Errors encountered: {0}".format(error_count))