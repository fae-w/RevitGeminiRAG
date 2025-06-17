# Purpose: This script counts mullion instances within the active Revit view.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Mullion, ElementId

# Get the active view
active_view = doc.ActiveView
mullion_count = 0

if active_view:
    # Create a collector for the active view
    collector = FilteredElementCollector(doc, active_view.Id)

    # Filter for mullion instances in the active view
    # OST_CurtainWallMullions represents Mullion instances
    mullion_collector = collector.OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType()

    # Get the count of mullion instances
    mullion_count = mullion_collector.GetElementCount()

    # Print the result
    print("# Found {0} mullion instances in the active view.".format(mullion_count))
else:
    # Handle case where there is no active view
    print("# Error: No active view found.")

# Optional: Print the count again outside the if block for consistency,
# it will be 0 if no active view was found.
# print("# Total mullions counted in active view (if any): {0}".format(mullion_count))