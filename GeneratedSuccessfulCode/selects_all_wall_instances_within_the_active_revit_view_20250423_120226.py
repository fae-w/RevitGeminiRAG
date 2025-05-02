# Purpose: This script selects all wall instances within the active Revit view.

﻿import clr
clr.AddReference('System.Collections')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, Wall
from System.Collections.Generic import List
import System

try:
    # Get the active view ID
    active_view_id = doc.ActiveView.Id

    if active_view_id == ElementId.InvalidElementId:
        print("# Error: Could not get a valid active view ID.")
    else:
        # Create a collector filtered by the active view
        collector = FilteredElementCollector(doc, active_view_id)

        # Filter for wall instances (not types) within the active view
        wall_collector = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

        # Get the ElementIds of the walls
        wall_ids = wall_collector.ToElementIds()

        # Check if any walls were found
        if wall_ids and wall_ids.Count > 0:
            # Convert to .NET List<ElementId> for selection
            selection_list = List[ElementId](wall_ids)
            try:
                # Set the selection in the UI
                uidoc.Selection.SetElementIds(selection_list)
                print("# Selected {0} wall instances in the active view.".format(selection_list.Count))
            except System.Exception as sel_ex:
                print("# Error setting selection: {0}".format(sel_ex))
        else:
            print("# No wall instances found in the active view to select.")

except AttributeError:
    print("# Error: No active view found or the active view cannot contain elements.")
except System.Exception as e:
    print("# An unexpected error occurred: {0}".format(e))