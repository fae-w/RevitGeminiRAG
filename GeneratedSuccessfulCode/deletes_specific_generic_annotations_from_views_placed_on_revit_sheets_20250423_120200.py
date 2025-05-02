# Purpose: This script deletes specific generic annotations from views placed on Revit sheets.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List, HashSet
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    ElementId,
    BuiltInCategory,
    AnnotationSymbol,
    ElementType,
    FamilySymbol # AnnotationSymbol.Symbol returns ElementType, often FamilySymbol
)

# Assume 'doc' is pre-defined

# 1. Find all unique View IDs that are placed on sheets
view_ids_on_sheets = HashSet[ElementId]()
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)

for sheet in sheet_collector:
    # Ensure sheet is valid before proceeding
    if sheet and sheet.IsValidObject:
        try:
            # Using GetAllViewports() as recommended over deprecated GetAllPlacedViews()
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
            # print(f"# Warning: Could not process viewports for sheet {{{{sheet.Id}}}}. Error: {{{{e}}}}") # Escaped
            pass # Continue with the next sheet

# 2. Collect Generic Annotations with "Help" in Family Name from those views
annotations_to_delete_ids = List[ElementId]()
search_term = "help" # Case-insensitive search term

if view_ids_on_sheets.Count > 0:
    for view_id in view_ids_on_sheets:
        try:
            # Get the view element itself to check if it's valid
            view = doc.GetElement(view_id)
            if view and view.IsValidObject:
                 # Create a collector filtered specifically for the current view
                 # Filter by category OST_GenericAnnotation
                 annotation_collector = FilteredElementCollector(doc, view_id).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType()

                 # Iterate through found annotations
                 for anno in annotation_collector:
                     # Check if element is valid and is an AnnotationSymbol
                     if anno and anno.IsValidObject and isinstance(anno, AnnotationSymbol):
                         try:
                             # Get the symbol (ElementType) of the annotation instance
                             anno_type = doc.GetElement(anno.GetTypeId())
                             if anno_type and isinstance(anno_type, ElementType): # Could be FamilySymbol or other ElementType
                                 family_name = anno_type.FamilyName
                                 # Check if family name contains the search term (case-insensitive)
                                 if family_name and search_term in family_name.lower():
                                     annotations_to_delete_ids.Add(anno.Id)
                         except Exception as type_e:
                             # print(f"# Warning: Could not process annotation type for {{{{anno.Id}}}} in view {{{{view_id}}}}. Error: {{{{type_e}}}}") # Escaped
                             pass # Continue with the next annotation

        except Exception as e:
            # print(f"# Warning: Could not collect annotations for view {{{{view_id}}}}. Error: {{{{e}}}}") # Escaped
            pass # Continue with the next view

# 3. Delete the collected Generic Annotations
# The transaction is handled by the external C# wrapper
if annotations_to_delete_ids.Count > 0:
    try:
        deleted_ids_result = doc.Delete(annotations_to_delete_ids)
        # print(f"# Deleted {{{{deleted_ids_result.Count}}}} generic annotation elements containing 'Help' in family name from views on sheets.") # Escaped Optional output
    except Exception as e:
        print(f"# Error during deletion: {{{{e}}}}") # Escaped
#else:
    # print("# No generic annotations with 'Help' in family name found in views placed on sheets to delete.") # Escaped Optional output
    # pass