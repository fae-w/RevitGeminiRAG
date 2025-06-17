# Purpose: This script overrides the color of specific mullions in Revit based on their type and level.

﻿# Import necessary classes
import clr
clr.AddReference('System')
from System import Byte
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Mullion,
    MullionType,
    Wall,
    Level,
    OverrideGraphicSettings,
    Color,
    View,
    ElementId,
    BuiltInParameter,
    CurtainGrid # Required for Wall.CurtainGrid
)
import System # For Exception handling and Color

# --- Configuration ---
target_mullion_type_name = 'Corner Mullion - 150mm Square'
target_level_name = 'Level 3'
override_color_magenta = Color(255, 0, 255) # RGB for Magenta

# --- Initial Checks ---
# Get the active view
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found. Cannot apply overrides.")
    # Exit or handle error appropriately if not running in a context with an active view
    # For this script, we'll proceed but won't be able to apply overrides later if active_view is None.

# Find the target Mullion Type ID
target_mullion_type_id = ElementId.InvalidElementId
mullion_types_collector = FilteredElementCollector(doc).OfClass(MullionType)
for mt in mullion_types_collector:
    if mt.Name == target_mullion_type_name:
        target_mullion_type_id = mt.Id
        break

if target_mullion_type_id == ElementId.InvalidElementId:
    print("# Error: Mullion Type '{}' not found in the document.".format(target_mullion_type_name))

# Find the target Level ID
target_level_id = ElementId.InvalidElementId
levels_collector = FilteredElementCollector(doc).OfClass(Level)
for level in levels_collector:
    if level.Name == target_level_name:
        target_level_id = level.Id
        break

if target_level_id == ElementId.InvalidElementId:
    print("# Error: Level '{}' not found in the document.".format(target_level_name))

# --- Main Logic ---
mullion_ids_to_override = List[ElementId]()
processed_walls = 0
walls_with_matching_level = 0
grids_found = 0
mullions_checked = 0

# Proceed only if target type, level, and active view are found
if target_mullion_type_id != ElementId.InvalidElementId and \
   target_level_id != ElementId.InvalidElementId and \
   active_view:

    print("# Found Target Mullion Type ID: {}".format(target_mullion_type_id))
    print("# Found Target Level ID: {}".format(target_level_id))
    print("# Active View: '{}' (ID: {})".format(active_view.Name, active_view.Id))

    # Collect all Wall elements
    wall_collector = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()

    for wall in wall_collector:
        processed_walls += 1
        try:
            # Check Wall's Base Constraint Parameter
            base_constraint_param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
            if base_constraint_param and base_constraint_param.AsElementId() == target_level_id:
                walls_with_matching_level += 1
                # Check if the wall hosts a Curtain Grid
                curtain_grid = wall.CurtainGrid # Wall.CurtainGrid property
                if curtain_grid:
                    grids_found += 1
                    # Get Mullions associated with this Curtain Grid
                    mullion_ids = curtain_grid.GetMullionIds()
                    if mullion_ids and mullion_ids.Count > 0:
                        for mullion_id in mullion_ids:
                            mullions_checked += 1
                            mullion = doc.GetElement(mullion_id)
                            # Check if the Mullion's Type matches the target type
                            if isinstance(mullion, Mullion) and mullion.GetTypeId() == target_mullion_type_id:
                                # Check if not already added (though GetMullionIds should be unique per grid)
                                if mullion_id not in mullion_ids_to_override:
                                     mullion_ids_to_override.Add(mullion_id)

        except System.Exception as e:
            # Log errors processing specific walls if needed
            # print("# Warning: Could not process Wall ID {}: {}".format(wall.Id, e))
            pass # Continue processing other walls

    # --- Apply Overrides ---
    if mullion_ids_to_override.Count > 0:
        # Create OverrideGraphicSettings
        override_settings = OverrideGraphicSettings()
        override_settings.SetProjectionLineColor(override_color_magenta)

        try:
            # Apply the overrides in the active view
            # Note: This assumes the C# wrapper has an open transaction
            active_view.SetElementOverrides(mullion_ids_to_override, override_settings)
            print("# Successfully applied Magenta projection color override to {} mullions.".format(mullion_ids_to_override.Count))
        except System.Exception as e:
            print("# Error applying overrides: {}".format(e))
    else:
        print("# No mullions matching the criteria were found to override.")

    # --- Final Summary Report ---
    print("# --- Processing Summary ---")
    print("# Walls processed: {}".format(processed_walls))
    print("# Walls on Level '{}': {}".format(target_level_name, walls_with_matching_level))
    print("# Curtain Grids found on matching walls: {}".format(grids_found))
    print("# Mullions checked on those grids: {}".format(mullions_checked))
    print("# Mullions matching Type '{}' found and targeted for override: {}".format(target_mullion_type_name, mullion_ids_to_override.Count))

# Additional error messages if prerequisites were not met
elif not active_view:
    print("# Operation could not proceed: No active view.")
else: # Type or Level not found
    print("# Operation could not proceed: Target Mullion Type or Level not found.")