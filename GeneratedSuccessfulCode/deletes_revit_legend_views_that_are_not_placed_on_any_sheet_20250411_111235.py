# Purpose: This script deletes Revit legend views that are not placed on any sheet.

# Purpose: This script deletes Revit legend views that are not placed on any sheet.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')
from System.Collections.Generic import HashSet, List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    View,
    ViewType,
    ElementId
)

# Assume 'doc' is pre-defined

# 1. Find all unique View IDs that are placed on sheets
placed_view_ids = HashSet[ElementId]()
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)

for sheet in sheet_collector:
    # Ensure sheet is valid before proceeding
    if sheet and sheet.IsValidObject:
        try:
            viewport_ids = sheet.GetAllViewports()
            for vp_id in viewport_ids:
                # Check if vp_id is valid before getting the element
                if vp_id != ElementId.InvalidElementId:
                    viewport = doc.GetElement(vp_id)
                    # Check if viewport element exists and is a Viewport
                    if viewport and isinstance(viewport, Viewport):
                        view_id = viewport.ViewId
                        # Add valid ViewId to the set
                        if view_id != ElementId.InvalidElementId:
                            placed_view_ids.Add(view_id)
        except Exception as e:
            # print(f"# Warning: Could not process viewports for sheet {{{{sheet.Id}}}}. Error: {{{{e}}}}") # Escaped
            pass # Continue with the next sheet

# 2. Collect all Legend Views
legend_views = FilteredElementCollector(doc).OfClass(View)
legends_to_delete_ids = List[ElementId]()

for view in legend_views:
    # Ensure view is valid and is a Legend view
    if view and view.IsValidObject and view.ViewType == ViewType.Legend:
        # Check if the Legend view's ID is NOT in the set of placed views
        if not placed_view_ids.Contains(view.Id):
            legends_to_delete_ids.Add(view.Id)

# 3. Delete the collected Legend Views that are not on sheets
# The transaction is handled by the external C# wrapper
if legends_to_delete_ids.Count > 0:
    try:
        deleted_ids_result = doc.Delete(legends_to_delete_ids)
        # print(f"# Deleted {{{{deleted_ids_result.Count}}}} legend views not placed on any sheet.") # Escaped
    except Exception as e:
        print(f"# Error during deletion: {{{{e}}}}") # Escaped
#else:
    # print("# No unplaced legend views found to delete.") # Escaped
    # pass