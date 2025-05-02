# Purpose: This script counts wall instances within the active Revit view.

﻿from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId

# Get the active view
active_view = doc.ActiveView
wall_count = 0

if active_view:
    # Create a collector filtered by the active view
    collector = FilteredElementCollector(doc, active_view.Id)

    # Filter for wall instances (not types) within the active view
    wall_collector = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    # Get the count of wall instances
    wall_count = wall_collector.GetElementCount()

    # Print the result using the specified format
    print("# Found {0} wall instances in the active view.".format(wall_count))
else:
    # Handle the case where there is no active view
    print("# Error: No active view found or the active view cannot contain elements.")