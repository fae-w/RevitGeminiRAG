# Purpose: This script hides Scope Boxes in Revit views, excluding floor plans and templates.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewType,
    BuiltInCategory,
    Category,
    ElementId
)
import System # For Exception handling

# --- Initialization ---
hidden_count = 0
skipped_floorplan = 0
skipped_template = 0
skipped_cannot_hide = 0
skipped_already_hidden = 0
error_count = 0
scope_box_cat_id = ElementId.InvalidElementId

# --- Get Scope Box Category ID ---
try:
    # Find the Category object for Scope Boxes
    scope_box_cat = Category.GetCategory(doc, BuiltInCategory.OST_SectionBox)
    if scope_box_cat is not None:
        scope_box_cat_id = scope_box_cat.Id
    else:
        # print("# Error: BuiltInCategory.OST_SectionBox not found in the document's categories.") # Optional debug
        error_count += 1 # Log as an error preventing the script from running fully
except Exception as e_cat:
    # print("# Error retrieving Scope Box category: {}".format(e_cat)) # Escaped Optional debug
    error_count += 1 # Log as an error

# --- Script Core Logic ---
# Proceed only if the category ID was successfully found
if scope_box_cat_id != ElementId.InvalidElementId:
    # Collect all View elements
    collector = FilteredElementCollector(doc).OfClass(View)

    # Iterate through the collected views
    for view in collector:
        # 1. Filter: Skip View Templates
        if view.IsTemplate:
            skipped_template += 1
            continue

        # 2. Filter: Skip Floor Plans
        if view.ViewType == ViewType.FloorPlan:
            skipped_floorplan += 1
            continue

        # 3. Process other view types
        try:
            # Check if the category can be hidden in this view
            if not view.CanCategoryBeHidden(scope_box_cat_id):
                skipped_cannot_hide += 1
                continue

            # Check if the category is already hidden
            if view.GetCategoryHidden(scope_box_cat_id):
                skipped_already_hidden += 1
                continue

            # Hide the Scope Box category
            view.SetCategoryHidden(scope_box_cat_id, True)
            hidden_count += 1
            # print("# Hid Scope Boxes in view: '{}' (ID: {})".format(view.Name, view.Id)) # Escaped Optional debug

        except Exception as e_view:
            # print("# Error processing view '{}' (ID: {}): {}".format(view.Name, view.Id, e_view)) # Escaped Optional debug
            error_count += 1

# --- Optional: Print Summary ---
# (Commented out as per instructions to only output code unless exporting)
# if scope_box_cat_id == ElementId.InvalidElementId:
#    print("# Script aborted: Could not find Scope Box category ID.") # Escaped
# else:
#    print("--- Scope Box Hiding Summary ---") # Escaped
#    print("# Scope Box Category ID: {}".format(scope_box_cat_id)) # Escaped
#    print("# Successfully hid category in: {} views".format(hidden_count)) # Escaped
#    print("# Skipped (Floor Plan): {} views".format(skipped_floorplan)) # Escaped
#    print("# Skipped (View Template): {} views".format(skipped_template)) # Escaped
#    print("# Skipped (Already Hidden): {} views".format(skipped_already_hidden)) # Escaped
#    print("# Skipped (Cannot Hide Category): {} views".format(skipped_cannot_hide)) # Escaped
#    print("# Errors encountered: {}".format(error_count)) # Escaped
#    total_views = len(list(collector)) # Recalculate or store initially if needed often
#    print("# Total views processed/checked: {}".format(total_views)) # Escaped