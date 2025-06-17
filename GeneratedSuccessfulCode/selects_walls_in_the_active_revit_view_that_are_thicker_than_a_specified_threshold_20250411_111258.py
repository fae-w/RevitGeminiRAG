# Purpose: This script selects walls in the active Revit view that are thicker than a specified threshold.

# Purpose: This script selects walls thicker than a specified threshold in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Required for UIDocument
clr.AddReference('System.Collections') # Required for List<T>
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall, ElementId
from Autodesk.Revit.UI import UIDocument # Explicit import for clarity
from System.Collections.Generic import List

# Define the thickness threshold in millimeters
min_thickness_mm = 300.0
# Revit's internal units are typically feet. Convert mm to feet.
mm_to_feet_conversion = 1 / (25.4 * 12)
min_thickness_internal = min_thickness_mm * mm_to_feet_conversion # Approximately 0.98425 feet

# List to store IDs of walls to select
walls_to_select_ids = []
selection_attempted = False

# Get the active view
active_view = uidoc.ActiveView

if active_view is not None:
    active_view_id = active_view.Id
    selection_attempted = True # We will attempt selection based on this view

    try:
        # Create a collector for walls in the active view
        collector = FilteredElementCollector(doc, active_view_id)
        wall_collector = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

        # Iterate through collected walls
        for wall in wall_collector:
            # Double-check if it's a Wall instance (though filter should suffice)
            if isinstance(wall, Wall):
                try:
                    # Get wall thickness (Width property is in internal units - feet)
                    wall_thickness_internal = wall.Width
                    # Check if thickness is greater than the threshold
                    if wall_thickness_internal > min_thickness_internal:
                        walls_to_select_ids.append(wall.Id)
                except Exception as e:
                    # Silently skip walls where Width cannot be accessed or other errors occur
                    # Optional: print debug message
                    # print("# Debug: Skipping element {0}, could not get Width. Error: {1}".format(wall.Id, e))
                    pass

        # If any matching walls were found, proceed to select them
        if walls_to_select_ids:
            # Convert the Python list of ElementIds to a .NET List<ElementId>
            selection_list = List[ElementId](walls_to_select_ids)

            # Set the selection in the Revit UI
            try:
                uidoc.Selection.SetElementIds(selection_list)
                # Optional: Print confirmation message
                # print("# Selected {0} walls thicker than {1}mm in the active view.".format(len(walls_to_select_ids), min_thickness_mm))
            except Exception as sel_ex:
                print("# Error setting selection: {}".format(sel_ex))
        # else:
             # Optional: print message if no walls met criteria
             # print("# No walls found thicker than {0}mm in the active view.".format(min_thickness_mm))

    except Exception as proc_ex:
        # Handle potential errors during collection or processing
        print("# Error collecting or processing walls: {}".format(proc_ex))

else: # No active view
    print("# Error: No active view found. Cannot select elements by view.")

# Final check - if selection wasn't even attempted due to no active view
# This is somewhat redundant with the else block above, but covers the initial state explicitly
# if not selection_attempted:
#    print("# Selection process not initiated: No active view available.")