# Purpose: This script unpins all pinnable elements within the active Revit view.

# Purpose: This script unpins all pinnable elements in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector, Element, ElementId, View

# Get the active view
try:
    active_view = doc.ActiveView
    if active_view is None:
        print("# Error: No active view found.")
        # Stop processing if no active view
        active_view_id = ElementId.InvalidElementId
    else:
        active_view_id = active_view.Id
except Exception as e:
    print(f"# Error getting active view: {{e}}") # Escaped f-string
    active_view_id = ElementId.InvalidElementId

unpinned_count = 0

# Proceed only if we have a valid active view ID
if active_view_id != ElementId.InvalidElementId:
    try:
        # Collect all elements visible (or potentially visible) in the active view
        # Note: This collects elements *associated* with the view, not just strictly visible ones.
        # Filtering further might be needed depending on exact requirements, but for pinning,
        # collecting elements in the view context is usually sufficient.
        collector = FilteredElementCollector(doc, active_view_id).WhereElementIsNotElementType()

        # Iterate through the collected elements
        for elem in collector:
            # Check if the element has the Pinned property (most elements do)
            if hasattr(elem, 'Pinned'):
                try:
                    # Check if the element is currently pinned
                    if elem.Pinned:
                        # Unpin the element (Transaction handled externally)
                        elem.Pinned = False
                        unpinned_count += 1
                except Exception as pin_ex:
                    # Some elements might throw exceptions when trying to access or change Pinned status
                    # e.g., elements controlled by groups, or specific system elements.
                    # print(f"# Could not modify pin status for element {elem.Id}: {pin_ex}") # Escaped f-string (optional debug)
                    pass # Continue with the next element

        # Optional: Print confirmation message
        # print(f"# Unpinned {{unpinned_count}} elements in the active view.") # Escaped f-string

    except Exception as e:
        print(f"# An error occurred during element processing: {{e}}") # Escaped f-string
# else:
    # Error message printed above if active view was not found
    # print("# Cannot proceed without a valid active view.") # Escaped
    # pass