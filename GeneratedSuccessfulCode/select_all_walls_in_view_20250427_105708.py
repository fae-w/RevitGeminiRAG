# Purpose: Selects all wall instances within the active Revit view.

import clr
clr.AddReference('System.Collections') # Required for List<T>
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, Wall, View
from System.Collections.Generic import List
import System

try:
    # Get the active view
    active_view = doc.ActiveView

    if not active_view:
        print("# Error: No active view found.")
    elif not isinstance(active_view, View) or not active_view.IsValidObject:
         print("# Error: The active view is not valid or not a graphical view.")
    else:
        active_view_id = active_view.Id
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
                # Clear selection if no walls are found in the view
                uidoc.Selection.SetElementIds(List[ElementId]())
                print("# No wall instances found in the active view to select.")

except AttributeError:
    print("# Error: Could not access the ActiveView property or its Id.")
except System.Exception as e:
    # Catch potential Revit API errors during filtering or other issues
    print("# An unexpected error occurred: {0}".format(e))