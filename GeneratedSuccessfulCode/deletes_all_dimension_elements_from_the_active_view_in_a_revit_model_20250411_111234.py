# Purpose: This script deletes all dimension elements from the active view in a Revit model.

# Purpose: This script deletes all dimension elements from the currently active view in Revit.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector, Dimension, ElementId, View

# Get the active view ID
try:
    active_view = doc.ActiveView
    if active_view is None:
        print("# Error: No active view found.")
        # Stop processing if no active view
        active_view_id = ElementId.InvalidElementId
    else:
        active_view_id = active_view.Id
except Exception as e:
    print(f"# Error getting active view: {e}") # Escaped f-string
    active_view_id = ElementId.InvalidElementId

dimensions_to_delete_ids = []

# Proceed only if we have a valid active view ID
if active_view_id != ElementId.InvalidElementId:
    # Collect Dimension elements specifically in the active view
    # Using OfClass(Dimension) is generally better than OfCategory(OST_Dimensions)
    # as it specifically targets Dimension elements and subtypes.
    collector = FilteredElementCollector(doc, active_view_id).OfClass(Dimension)

    # Gather the ElementIds of the dimensions found
    for dim in collector:
        dimensions_to_delete_ids.append(dim.Id)

    # Check if any dimensions were found to delete
    if dimensions_to_delete_ids:
        # Prepare the collection of ElementIds for the Delete method
        ids_to_delete_net = List[ElementId](dimensions_to_delete_ids)

        # Delete the elements (Transaction is managed externally)
        try:
            deleted_ids_count = doc.Delete(ids_to_delete_net).Count
            # Optional: Print confirmation message
            # print(f"# Deleted {deleted_ids_count} dimension elements from the active view.") # Escaped f-string
        except Exception as e:
            print(f"# Error during deletion: {e}") # Escaped f-string
    else:
        # Optional: Print message if no dimensions were found
        # print("# No dimension elements found in the active view to delete.") # Escaped
        pass # Nothing to delete
# else:
    # Error message printed above if active view was not found
    # print("# Cannot proceed without a valid active view.") # Escaped
    pass