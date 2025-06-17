# Purpose: This script selects all curtain wall instances in the Revit model.

﻿# Mandatory Imports
import clr
clr.AddReference('System.Collections') # Required for List<T>
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    ElementId,
    WallKind # Needed to check wall type kind
)
from System.Collections.Generic import List
import System # For exception handling

# --- Script Core Logic ---
curtain_wall_ids = []
processed_count = 0
error_count = 0

try:
    # Collect all Wall instances in the project
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    for wall in collector:
        processed_count += 1
        # Check if the element is actually a Wall object (robustness)
        if isinstance(wall, Wall):
            try:
                # Check 1: Using the CurtainGrid property (more direct)
                # If a wall instance has a CurtainGrid, it is a curtain wall.
                if wall.CurtainGrid is not None:
                    curtain_wall_ids.append(wall.Id)
                    continue # Move to the next wall

                # Check 2: Using WallType Kind (alternative/fallback if CurtainGrid fails or for edge cases)
                # This is less common for instance checks but can be used
                # wall_type = doc.GetElement(wall.GetTypeId())
                # if wall_type and hasattr(wall_type, 'Kind') and wall_type.Kind == WallKind.Curtain:
                #     curtain_wall_ids.append(wall.Id)

            except System.Exception as e:
                # Log error if accessing properties fails for a specific wall
                print("# Warning: Could not process Wall ID {}: {}".format(wall.Id, e))
                error_count += 1
        # else: # Optional: Log elements that are in the category but not Wall instances
             # print("# Debug: Skipping non-Wall element ID {} in OST_Walls category.".format(wall.Id))


except System.Exception as ex:
    print("# Error during collection or processing: {}".format(ex))
    error_count += 1

# Convert Python list to .NET List<ElementId>
selection_list = List[ElementId](curtain_wall_ids)

# Select the elements in the UI
if selection_list.Count > 0:
    try:
        uidoc.Selection.SetElementIds(selection_list)
        print("# Selected {} curtain wall elements.".format(selection_list.Count))
    except System.Exception as sel_ex:
        print("# Error setting selection: {}".format(sel_ex))
        error_count += 1
else:
    print("# No curtain wall elements found to select.")

# Optional: Print summary if errors occurred
if error_count > 0:
    print("# Encountered {} errors during processing.".format(error_count))