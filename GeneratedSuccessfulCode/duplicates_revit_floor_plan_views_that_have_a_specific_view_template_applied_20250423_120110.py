# Purpose: This script duplicates Revit floor plan views that have a specific view template applied.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewPlan,
    ViewType,
    ElementId,
    ViewDuplicateOption
)

# --- Configuration ---
template_name_to_find = "Architectural Plan"

# --- Find the View Template ID ---
template_id = ElementId.InvalidElementId
template_collector = FilteredElementCollector(doc).OfClass(View)
for view in template_collector:
    if view.IsTemplate and view.Name == template_name_to_find:
        template_id = view.Id
        # print(f"# Found View Template '{template_name_to_find}' with ID: {template_id}") # Optional debug
        break

if template_id == ElementId.InvalidElementId:
    print(f"# Error: View Template named '{template_name_to_find}' not found in the document.")
else:
    # --- Find and Duplicate Floor Plans ---
    views_to_duplicate = []
    view_collector = FilteredElementCollector(doc).OfClass(ViewPlan)

    for view in view_collector:
        # Check if it's a Floor Plan, not a template itself, and has the target template applied
        if view.ViewType == ViewType.FloorPlan and not view.IsTemplate:
            if view.ViewTemplateId == template_id:
                views_to_duplicate.append(view)

    if not views_to_duplicate:
        print(f"# No Floor Plan views found with the '{template_name_to_find}' template applied.")
    else:
        duplicated_count = 0
        error_count = 0
        print(f"# Found {len(views_to_duplicate)} Floor Plan view(s) with the '{template_name_to_find}' template. Duplicating...")

        for view_to_dup in views_to_duplicate:
            try:
                # Duplicate the view with standard options (no detailing)
                new_view_id = view_to_dup.Duplicate(ViewDuplicateOption.Duplicate)
                if new_view_id != ElementId.InvalidElementId:
                    # print(f"# Duplicated '{view_to_dup.Name}' (ID: {view_to_dup.Id}) to new view ID: {new_view_id}") # Optional debug
                    duplicated_count += 1
                else:
                    print(f"# Warning: Failed to duplicate view '{view_to_dup.Name}' (ID: {view_to_dup.Id}) - Duplicate returned InvalidElementId.")
                    error_count += 1
            except Exception as e:
                print(f"# Error duplicating view '{view_to_dup.Name}' (ID: {view_to_dup.Id}): {e}")
                error_count += 1

        print(f"# --- Summary ---")
        print(f"# Successfully duplicated {duplicated_count} view(s).")
        if error_count > 0:
            print(f"# Failed to duplicate {error_count} view(s).")