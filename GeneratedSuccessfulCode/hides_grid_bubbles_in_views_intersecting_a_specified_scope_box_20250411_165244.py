# Purpose: This script hides grid bubbles in views intersecting a specified scope box.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Although not strictly used, good practice
clr.AddReference('System')
from System import Exception, InvalidOperationException # Explicit exception imports from System
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    ElementId,
    Grid,
    View,
    ViewType,
    BoundingBoxXYZ,
    Outline,
    BoundingBoxIntersectsFilter,
    DatumEnds,
    Category
    # Removed InvalidOperationException from here
)
# Removed: from Autodesk.Revit.UI import * # Not strictly needed based on code logic
# Removed: from Autodesk.Revit.ApplicationServices import * # Not strictly needed

# --- Configuration ---
# !!! IMPORTANT: Set the exact name of the target Scope Box here !!!
TARGET_SCOPE_BOX_NAME = "Scope Box 1" # <--- CHANGE THIS NAME

# --- Initialization ---
target_scope_box = None
intersecting_grids = []
views_to_process = []
hidden_call_count = 0
skipped_view_count = 0
error_count = 0
processed_grid_count = 0

# --- Step 1: Find the Target Scope Box ---
try:
    # Scope Boxes are Elements of category OST_VolumeOfInterest
    collector_sb = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_VolumeOfInterest).WhereElementIsNotElementType()
    found = False
    for sb in collector_sb:
        # Check Name property exists before accessing it
        if hasattr(sb, "Name") and sb.Name == TARGET_SCOPE_BOX_NAME:
            target_scope_box = sb
            found = True
            break # Found the scope box

    if not found:
        print("# Error: Scope Box named '{{{{}}}}' not found.".format(TARGET_SCOPE_BOX_NAME))
        # Stop script execution if the essential scope box is missing
        target_scope_box = None # Ensure it's None

except Exception as e:
    print("# Error finding scope box '{{{{}}}}': {{{{}}}}".format(TARGET_SCOPE_BOX_NAME, e))
    target_scope_box = None # Ensure it's None on error

# Proceed only if scope box was found
if target_scope_box:
    # --- Step 2: Find Intersecting Grids ---
    try:
        # Get the bounding box of the scope box
        bbox = target_scope_box.get_BoundingBox(None) # Use None for model coordinates
        if bbox:
            # Create an Outline object from the bounding box (add small tolerance if needed)
            outline = Outline(bbox.Min, bbox.Max)
            # Create a filter based on the outline
            bb_filter = BoundingBoxIntersectsFilter(outline)

            # Collect grids that intersect the bounding box
            collector_grids = FilteredElementCollector(doc).OfClass(Grid).WherePasses(bb_filter).WhereElementIsNotElementType()
            intersecting_grids = list(collector_grids) # Convert iterator to list
            processed_grid_count = len(intersecting_grids)
            if not intersecting_grids:
                 print("# Info: No grids found intersecting Scope Box '{{{{}}}}'.".format(TARGET_SCOPE_BOX_NAME))
        else:
            print("# Error: Could not retrieve bounding box for Scope Box '{{{{}}}}'.".format(TARGET_SCOPE_BOX_NAME))
            error_count += 1
            intersecting_grids = [] # Ensure list is empty

    except Exception as e:
        print("# Error collecting intersecting grids: {{{{}}}}".format(e))
        error_count += 1
        intersecting_grids = [] # Ensure list is empty

    # --- Step 3: Collect Views ---
    try:
        collector_views = FilteredElementCollector(doc).OfClass(View)
        for view in collector_views:
            # Skip view templates
            if view.IsTemplate:
                continue
            # Only process views where graphics overrides are generally possible
            if view.AreGraphicsOverridesAllowed():
                 # Check if the view type typically shows grids (optional filter)
                 # Relevant types: FloorPlan, CeilingPlan, Elevation, Section, Detail, AreaPlan, StructuralPlan
                 # You might adjust this list based on project standards
                 relevant_view_types = [
                     ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Elevation,
                     ViewType.Section, ViewType.Detail, ViewType.AreaPlan,
                     ViewType.EngineeringPlan # Revit 2023+ name for StructuralPlan
                 ]
                 # Check if ViewType.StructuralPlan exists for older Revit versions if needed
                 try:
                     # Check existence using dir() or hasattr() on the ViewType enum itself
                     if hasattr(ViewType, 'StructuralPlan'):
                         relevant_view_types.append(ViewType.StructuralPlan)
                 except: pass # Ignore if StructuralPlan enum doesn't exist or check fails

                 if view.ViewType in relevant_view_types:
                     views_to_process.append(view)

        if not views_to_process:
            print("# Info: No suitable views (Plan, Section, Elevation, etc.) found to process.")

    except Exception as e:
        print("# Error collecting views: {{{{}}}}".format(e))
        error_count += 1
        views_to_process = [] # Ensure list is empty

    # --- Step 4: Override Bubble Visibility ---
    if intersecting_grids and views_to_process:
        grid_cat = Category.GetCategory(doc, BuiltInCategory.OST_Grids)
        grid_cat_id = grid_cat.Id if grid_cat else ElementId.InvalidElementId

        for grid in intersecting_grids:
            if not isinstance(grid, Grid): continue # Should not happen with OfClass(Grid) filter

            for view in views_to_process:
                try:
                    # Check 1: Is the Grid category globally hidden in this view?
                    if grid_cat_id != ElementId.InvalidElementId and view.GetCategoryHidden(grid_cat_id):
                        # skipped_view_count += 1 # Don't count here, HideBubbleInView will handle it
                        continue

                    # Check 2: Is the specific grid element hidden (e.g., by filter or element hide)?
                    # We rely on HideBubbleInView throwing an exception if not applicable.

                    # Attempt to hide bubble End1.
                    # HideBubbleInView should handle cases where it's already hidden or not applicable.
                    # It throws InvalidOperationException if the datum is not visible in the view at all.
                    grid.HideBubbleInView(DatumEnds.End1, view)
                    hidden_call_count += 1 # Count calls that don't throw InvalidOperationException immediately

                except InvalidOperationException: # Catching System.InvalidOperationException now
                    # Common exception if the grid/bubble isn't applicable/visible in the view context.
                    skipped_view_count += 1
                except Exception as e:
                    # Catch other potential errors during the hide operation
                    grid_name = "Unnamed Grid"
                    try:
                        grid_name = grid.Name # Try to get name for better error message
                    except:
                        pass # Keep default name if error accessing property
                    view_name = "Unnamed View"
                    try:
                        view_name = view.Name
                    except:
                        pass

                    print("# Error hiding bubble End1 for Grid '{{{{}}}}' (ID: {{{{}}}}) in View '{{{{}}}}' (ID: {{{{}}}}): {{{{}}}}".format(grid_name, grid.Id, view_name, view.Id, e))
                    error_count += 1

    # --- Step 5: Optional Summary (Commented out for direct execution, uncomment in PyRevit/Dynamo if needed) ---
    # print("--- Grid Bubble Override Summary ---")
    # print("# Target Scope Box: '{{{{}}}}'".format(TARGET_SCOPE_BOX_NAME))
    # print("# Intersecting Grids Found: {{{{}}}}".format(processed_grid_count))
    # print("# Suitable Views Found: {{{{}}}}".format(len(views_to_process)))
    # print("# HideBubbleInView Calls Attempted (Approx.): {{{{}}}}".format(hidden_call_count)) # Renamed for clarity
    # print("# Skipped Operations (Not Applicable/Category Hidden): {{{{}}}}".format(skipped_view_count)) # Renamed for clarity
    # print("# Errors during Override: {{{{}}}}".format(error_count))

# else: # Scope box was not found initially
#     print("# Script execution stopped: Target Scope Box '{{{{}}}}' was not found.".format(TARGET_SCOPE_BOX_NAME)) # Optional final message