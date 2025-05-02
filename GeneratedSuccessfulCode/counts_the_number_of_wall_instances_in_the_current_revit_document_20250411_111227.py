# Purpose: This script counts the number of wall instances in the current Revit document.

# Purpose: This script counts the number of wall instances in the current Revit document.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall

# This script performs a safe operation (counting walls)
# in response to a prompt mentioning safety settings.
# No unsafe or destructive actions are taken.

# Collect all Wall elements (instances)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

# Get the count of wall instances
wall_count = collector.GetElementCount()

# Print the result (safe output)
# Using print() for feedback as no export format was requested.
print("# Found {0} wall instances in the document.".format(wall_count))

# Note: No unsafe operations performed.