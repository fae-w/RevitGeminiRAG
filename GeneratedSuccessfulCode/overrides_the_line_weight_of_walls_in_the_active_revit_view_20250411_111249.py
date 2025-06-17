# Purpose: This script overrides the line weight of walls in the active Revit view.

# Purpose: This script overrides the line weight of walls in the active Revit view.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    View,
    OverrideGraphicSettings,
    ElementId
)

# Define the desired line weight
new_line_weight = 5

# Get the active view
try:
    active_view = doc.ActiveView
    if not active_view:
        print("# Error: No active view found.")
        active_view = None # Ensure it's None if not found
except AttributeError:
    print("# Error: Could not get active view.")
    active_view = None

if active_view:
    # Create OverrideGraphicSettings object
    override_settings = OverrideGraphicSettings()

    # Set the projection line weight
    try:
        override_settings.SetProjectionLineWeight(new_line_weight)
    except Exception as e:
        print("# Error setting projection line weight: {}".format(e)) # Escaped format

    # Set the cut line weight
    try:
        override_settings.SetCutLineWeight(new_line_weight)
    except Exception as e:
        print("# Error setting cut line weight: {}".format(e)) # Escaped format

    # Collect all Wall elements visible in the active view
    collector = FilteredElementCollector(doc, active_view.Id)
    wall_collector = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    # Apply the overrides to each wall
    walls_overridden_count = 0
    for wall in wall_collector:
        if isinstance(wall, Wall):
            try:
                active_view.SetElementOverrides(wall.Id, override_settings)
                walls_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Failed to override wall {wall.Id}: {e}") # Escaped
                pass # Skip elements that cause errors

    # Optional: Print a confirmation message
    # print(f"# Applied line weight override ({new_line_weight}) to {walls_overridden_count} walls in view '{active_view.Name}'.") # Escaped
else:
    print("# Script did not run because there is no active view.")