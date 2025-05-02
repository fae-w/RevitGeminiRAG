# Purpose: This script selects walls thicker than a specified threshold within the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Required for List<T>
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall, ElementId
from System.Collections.Generic import List
import System

# Define the thickness threshold in feet (7 inches = 7 / 12.0 feet)
min_thickness_feet = 7.0 / 12.0

# Get the active view ID, handle potential errors if no active view
try:
    active_view = doc.ActiveView
    if active_view is None:
        print("# Error: No active view found.")
        active_view_id = ElementId.InvalidElementId
    else:
        active_view_id = active_view.Id
except AttributeError:
    print("# Error: Could not get active view ID. Cannot filter by view.")
    active_view_id = ElementId.InvalidElementId

walls_to_select_ids = []
if active_view_id != ElementId.InvalidElementId:
    # Create a collector filtered by the active view
    collector = FilteredElementCollector(doc, active_view_id)

    # Filter for wall instances (not types) within the active view
    wall_collector = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    # Iterate through the collected walls
    for wall in wall_collector:
        if isinstance(wall, Wall):
            try:
                # Check wall thickness using the Width property (internal units - feet)
                wall_thickness = wall.Width
                if wall_thickness > min_thickness_feet:
                    walls_to_select_ids.append(wall.Id)
            except Exception as e:
                # Silently skip walls where Width cannot be accessed or other errors occur
                # print(f"# Debug: Skipping element {wall.Id}, could not get Width or other error. Error: {e}") # Escaped Optional debug
                pass

# Convert the list of ElementIds to a .NET List<ElementId>
selection_list = List[ElementId](walls_to_select_ids)

# Set the selection in the UI
if selection_list.Count > 0:
    try:
        uidoc.Selection.SetElementIds(selection_list)
        # print(f"# Selected {selection_list.Count} walls thicker than 7 inches in the active view.") # Escaped Optional output
    except System.Exception as sel_ex:
        print("# Error setting selection: {0}".format(sel_ex)) # Escaped
else:
    # print("# No walls found thicker than 7 inches in the active view.") # Escaped Optional output
    # Clear selection if nothing met the criteria
    try:
        uidoc.Selection.SetElementIds(List[ElementId]())
    except System.Exception as clear_ex:
        print("# Error clearing selection: {0}".format(clear_ex)) # Escaped