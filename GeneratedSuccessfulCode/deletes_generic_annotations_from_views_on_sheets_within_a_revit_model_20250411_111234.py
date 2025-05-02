# Purpose: This script deletes generic annotations from views on sheets within a Revit model.

# Purpose: This script deletes all Generic Annotations placed in views that appear on sheets within a Revit document.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Not strictly needed for this logic, but good practice
clr.AddReference('System.Collections')
from System.Collections.Generic import List, HashSet
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    ElementId,
    BuiltInCategory
)

# Assume 'doc' is pre-defined

# 1. Find all unique View IDs that are placed on sheets
view_ids_on_sheets = HashSet[ElementId]()
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
                            view_ids_on_sheets.Add(view_id)
        except Exception as e:
            # print(f"# Warning: Could not process viewports for sheet {{sheet.Id}}. Error: {{e}}") # Escaped
            pass # Continue with the next sheet

# 2. Collect Generic Annotations located ONLY within those specific views
annotations_to_delete_ids = List[ElementId]()

if view_ids_on_sheets.Count > 0:
    for view_id in view_ids_on_sheets:
        try:
            # Get the view element itself to check if it's valid
            view = doc.GetElement(view_id)
            if view and view.IsValidObject:
                 # Create a collector filtered specifically for the current view
                 # Filter by category OST_GenericAnnotation
                 annotation_collector = FilteredElementCollector(doc, view_id).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType()

                 # Add the ElementIds of found annotations to the list for deletion
                 for anno in annotation_collector:
                     # Check if element is valid before adding ID
                     if anno and anno.IsValidObject:
                         annotations_to_delete_ids.Add(anno.Id)

        except Exception as e:
            # print(f"# Warning: Could not collect annotations for view {{view_id}}. Error: {{e}}") # Escaped
            pass # Continue with the next view

# 3. Delete the collected Generic Annotations
# The transaction is handled by the external C# wrapper
if annotations_to_delete_ids.Count > 0:
    try:
        deleted_ids_result = doc.Delete(annotations_to_delete_ids)
        # print(f"# Deleted {{deleted_ids_result.Count}} generic annotation elements from views on sheets.") # Escaped
    except Exception as e:
        print(f"# Error during deletion: {{e}}") # Escaped
#else:
    # print("# No generic annotations found in views placed on sheets to delete.") # Escaped
    # pass