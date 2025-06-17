# Purpose: This script selects glazed system panels within selected curtain walls in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('System.Collections')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Wall,
    CurtainGrid,
    ElementId,
    Panel, # Generic Panel class, useful for type checking
    FamilyInstance, # Panels are often FamilyInstances
    PanelType, # Specific type for system panels like Glazed
    BuiltInCategory,
    WallKind
)
from System.Collections.Generic import List
import System # For exception handling

# --- Configuration ---
target_panel_type_name = "System Panel: Glazed"

# --- Script Core Logic ---
selected_panel_ids = []
processed_wall_count = 0
found_panel_count = 0
error_count = 0

try:
    # Get the current selection
    selection_ids = uidoc.Selection.GetElementIds()

    if not selection_ids or selection_ids.Count == 0:
        print("# Info: No elements selected. Please select curtain walls first.")
    else:
        selected_curtain_wall_ids = []
        # Filter the selection to find only Curtain Walls
        for elem_id in selection_ids:
            try:
                element = doc.GetElement(elem_id)
                if isinstance(element, Wall):
                    # Check if it's a curtain wall (using CurtainGrid is reliable for instances)
                    if element.CurtainGrid is not None:
                        selected_curtain_wall_ids.append(element.Id)
                    # Optional: Fallback check using WallType Kind
                    # else:
                    #     wall_type = doc.GetElement(element.GetTypeId())
                    #     if wall_type and hasattr(wall_type, 'Kind') and wall_type.Kind == WallKind.Curtain:
                    #         selected_curtain_wall_ids.append(element.Id)
            except System.Exception as e:
                print("# Warning: Could not process selected element ID {}: {}".format(elem_id, e))
                error_count += 1

        if not selected_curtain_wall_ids:
            print("# Info: Selection does not contain any Curtain Walls.")
        else:
            print("# Found {} selected Curtain Walls to process.".format(len(selected_curtain_wall_ids)))

            # Iterate through the selected curtain walls
            for wall_id in selected_curtain_wall_ids:
                try:
                    wall = doc.GetElement(wall_id)
                    if not isinstance(wall, Wall) or wall.CurtainGrid is None:
                        continue # Skip if not a valid curtain wall (double check)

                    processed_wall_count += 1
                    grid = wall.CurtainGrid

                    # Get all panel IDs from the grid
                    panel_ids = grid.GetPanelIds()

                    for panel_id in panel_ids:
                        try:
                            panel = doc.GetElement(panel_id)
                            # Panels can be FamilyInstance or sometimes direct Panel objects
                            if panel is not None:
                                panel_type_id = panel.GetTypeId()
                                if panel_type_id != ElementId.InvalidElementId:
                                    panel_type = doc.GetElement(panel_type_id)
                                    if panel_type is not None:
                                        # Check if the type name matches the target
                                        # Using Element.Name property should work for PanelType
                                        current_type_name = Element.Name.GetValue(panel_type)
                                        if current_type_name == target_panel_type_name:
                                            selected_panel_ids.append(panel_id)
                                            found_panel_count += 1
                        except System.Exception as panel_ex:
                            print("# Warning: Could not process panel ID {} from wall ID {}: {}".format(panel_id, wall_id, panel_ex))
                            error_count += 1

                except System.Exception as wall_ex:
                    print("# Error processing selected Curtain Wall ID {}: {}".format(wall_id, wall_ex))
                    error_count += 1

            # Convert Python list to .NET List<ElementId>
            selection_list = List[ElementId](selected_panel_ids)

            # Select the found panels in the UI
            if selection_list.Count > 0:
                try:
                    uidoc.Selection.SetElementIds(selection_list)
                    print("# Selected {} panels of type '{}' from {} processed curtain walls.".format(selection_list.Count, target_panel_type_name, processed_wall_count))
                except System.Exception as sel_ex:
                    print("# Error setting final selection: {}".format(sel_ex))
                    error_count += 1
            else:
                print("# No panels of type '{}' found in the selected curtain walls.".format(target_panel_type_name))

except System.Exception as main_ex:
    print("# Error during script execution: {}".format(main_ex))
    error_count += 1

# Optional: Print error summary
if error_count > 0:
    print("# Encountered {} errors during processing.".format(error_count))