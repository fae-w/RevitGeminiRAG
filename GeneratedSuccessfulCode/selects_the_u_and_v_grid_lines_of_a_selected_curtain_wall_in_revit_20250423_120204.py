# Purpose: This script selects the U and V grid lines of a selected curtain wall in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    Wall,
    CurtainGrid,
    CurtainGridLine,
    ElementId
)
import System # For exception handling

# --- Script Core Logic ---

# Get current selection
selected_ids = uidoc.Selection.GetElementIds()
selected_elements = [doc.GetElement(id) for id in selected_ids]

# Check if exactly one element is selected
if len(selected_elements) == 1:
    selected_element = selected_elements[0]

    # Check if the selected element is a Wall
    if isinstance(selected_element, Wall):
        wall = selected_element
        curtain_grid = None
        try:
            # Try to get the CurtainGrid from the Wall
            curtain_grid = wall.CurtainGrid
        except System.Exception as e:
            print("# Error accessing CurtainGrid property for selected wall (ID: {{}}): {{}}".format(wall.Id, e))
            curtain_grid = None # Ensure it's None if error occurs

        if curtain_grid:
            # Get U and V grid line IDs
            u_grid_line_ids = List[ElementId]()
            v_grid_line_ids = List[ElementId]()
            all_grid_line_ids = List[ElementId]()

            try:
                u_grid_line_ids = curtain_grid.GetUGridLineIds()
            except System.Exception as e:
                 print("# Warning: Could not get U grid lines for wall ID {{}}: {{}}".format(wall.Id, e))

            try:
                v_grid_line_ids = curtain_grid.GetVGridLineIds()
            except System.Exception as e:
                 print("# Warning: Could not get V grid lines for wall ID {{}}: {{}}".format(wall.Id, e))

            # Combine the lists
            for id in u_grid_line_ids:
                all_grid_line_ids.Add(id)
            for id in v_grid_line_ids:
                all_grid_line_ids.Add(id)

            # Select the grid lines
            if all_grid_line_ids.Count > 0:
                try:
                    uidoc.Selection.SetElementIds(all_grid_line_ids)
                    print("# Selected {{}} curtain grid lines (U and V) from the selected curtain wall.".format(all_grid_line_ids.Count))
                except System.Exception as sel_ex:
                    print("# Error setting selection: {{}}".format(sel_ex))
            else:
                print("# No curtain grid lines found on the selected curtain wall.")

        else:
            print("# The selected wall (ID: {{}}) does not appear to be a curtain wall or does not have a CurtainGrid.".format(wall.Id))
    else:
        print("# The selected element (ID: {{}}) is not a Wall.".format(selected_element.Id))
elif len(selected_elements) == 0:
    print("# Please select exactly one curtain wall element.")
else:
    print("# Please select exactly ONE curtain wall element. Currently selected: {{}} elements.".format(len(selected_elements)))