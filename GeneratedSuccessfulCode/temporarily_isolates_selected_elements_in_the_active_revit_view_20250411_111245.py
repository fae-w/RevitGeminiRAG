# Purpose: This script temporarily isolates selected elements in the active Revit view.

# Purpose: This script isolates temporarily selected elements within the active Revit view.

﻿import clr
clr.AddReference('System.Collections')
from Autodesk.Revit.DB import ElementId, View
from System.Collections.Generic import ICollection, List

# Get the active view
active_view = doc.ActiveView

if not active_view:
    print("# Error: No active view found.")
else:
    # Get the currently selected element IDs
    selected_ids = uidoc.Selection.GetElementIds()

    # Check if any elements are selected
    if selected_ids is None or selected_ids.Count == 0:
        print("# No elements selected to isolate.")
    else:
        try:
            # Ensure selected_ids is ICollection<ElementId> (which it should be)
            # The API expects ICollection<ElementId>
            # If GetElementIds() returned something else, conversion might be needed:
            # selected_ids_list = List[ElementId](selected_ids)
            # active_view.IsolateElementsTemporary(selected_ids_list)
            # But GetElementIds() returns ICollection<ElementId> directly.

            active_view.IsolateElementsTemporary(selected_ids)
            print("# Isolated {} selected elements temporarily in view '{}'.".format(selected_ids.Count, active_view.Name))
        except Exception as e:
            print("# Error isolating elements: {}".format(e))