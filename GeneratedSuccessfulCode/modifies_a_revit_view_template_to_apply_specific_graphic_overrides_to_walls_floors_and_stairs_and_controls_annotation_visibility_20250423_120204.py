# Purpose: This script modifies a Revit view template to apply specific graphic overrides to walls, floors, and stairs, and controls annotation visibility.

﻿# Import necessary classes
import clr
# clr.AddReference('System.Collections') # Not strictly required for this script but good practice
# from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    View, ViewPlan, ViewType
)

# --- Configuration ---
light_grey_val = 240
light_grey_color = Color(light_grey_val, light_grey_val, light_grey_val)
black_color = Color(0, 0, 0)

# --- Helper Function to find Solid Fill Pattern ---
def find_solid_fill_pattern_id(doc_param):
    solid_fill_pattern_id = ElementId.InvalidElementId
    fill_pattern_collector = FilteredElementCollector(doc_param).OfClass(FillPatternElement)
    # Prefer Drafting Solid Fill
    for pattern_elem in fill_pattern_collector:
        try:
            fill_pattern = pattern_elem.GetFillPattern()
            if fill_pattern.IsSolidFill and fill_pattern.Target == FillPatternTarget.Drafting:
                solid_fill_pattern_id = pattern_elem.Id
                break
        except Exception:
            continue # Skip patterns causing errors
    # Fallback: Any Solid Fill if Drafting not found
    if solid_fill_pattern_id == ElementId.InvalidElementId:
        for pattern_elem in fill_pattern_collector:
            try:
                fill_pattern = pattern_elem.GetFillPattern()
                if fill_pattern.IsSolidFill:
                    solid_fill_pattern_id = pattern_elem.Id
                    # print("# Warning: Using a non-Drafting solid fill pattern as fallback.") # Optional warning
                    break
            except Exception:
                continue
    return solid_fill_pattern_id

# --- Main Logic ---
active_view = doc.ActiveView

# Check if active view exists and is a Floor Plan
if not active_view or not isinstance(active_view, View):
    print("# Error: No active graphical view found.")
# Check if the view is a Floor Plan specifically
elif active_view.ViewType != ViewType.FloorPlan:
     print(f"# Error: Active view '{{active_view.Name}}' is not a Floor Plan. ViewType: {{active_view.ViewType.ToString()}}") # Escaped f-string
else:
    # Check if the active view has a View Template applied
    template_id = active_view.ViewTemplateId
    if template_id == ElementId.InvalidElementId:
        print("# Error: The active view does not have a View Template applied.")
    else:
        # Get the View Template element (which is also a View)
        template_view = doc.GetElement(template_id)
        if not template_view or not isinstance(template_view, View):
            print("# Error: Could not retrieve the View Template element.")
        else:
            # Find Solid Fill Pattern ID (needed for walls and floors)
            solid_fill_id = find_solid_fill_pattern_id(doc)
            if solid_fill_id == ElementId.InvalidElementId:
                print("# Error: Could not find any 'Solid fill' pattern in the project. Cannot proceed with wall/floor overrides.")
            else:
                try:
                    # --- 1. Walls Cut Pattern (Solid Black) ---
                    walls_cat_id = ElementId(BuiltInCategory.OST_Walls)
                    wall_overrides = template_view.GetCategoryOverrides(walls_cat_id)
                    wall_overrides.SetCutForegroundPatternVisible(True)
                    wall_overrides.SetCutForegroundPatternId(solid_fill_id)
                    wall_overrides.SetCutForegroundPatternColor(black_color)
                    # Ensure background pattern is not interfering
                    wall_overrides.SetCutBackgroundPatternVisible(False)
                    wall_overrides.SetCutBackgroundPatternId(ElementId.InvalidElementId) # Explicitly remove background pattern override if any
                    template_view.SetCategoryOverrides(walls_cat_id, wall_overrides)
                    # print("# Applied Wall cut pattern overrides.") # Optional status

                    # --- 2. Floors Surface Pattern (Solid Light Grey) ---
                    floors_cat_id = ElementId(BuiltInCategory.OST_Floors)
                    floor_overrides = template_view.GetCategoryOverrides(floors_cat_id)
                    floor_overrides.SetSurfaceForegroundPatternVisible(True)
                    floor_overrides.SetSurfaceForegroundPatternId(solid_fill_id)
                    floor_overrides.SetSurfaceForegroundPatternColor(light_grey_color)
                    # Ensure background pattern is not interfering
                    floor_overrides.SetSurfaceBackgroundPatternVisible(False)
                    floor_overrides.SetSurfaceBackgroundPatternId(ElementId.InvalidElementId) # Explicitly remove background pattern override if any
                    template_view.SetCategoryOverrides(floors_cat_id, floor_overrides)
                    # print("# Applied Floor surface pattern overrides.") # Optional status

                    # --- 3. Stairs Halftone ---
                    stairs_cat_id = ElementId(BuiltInCategory.OST_Stairs)
                    stairs_overrides = template_view.GetCategoryOverrides(stairs_cat_id)
                    stairs_overrides.SetHalftone(True)
                    template_view.SetCategoryOverrides(stairs_cat_id, stairs_overrides)
                    # print("# Applied Stairs halftone override.") # Optional status

                    # --- 4. Turn Off "Show All Annotation Categories" ---
                    # Setting AreAnnotationCategoriesHidden to True effectively unchecks
                    # the "Show annotation categories in this view" box in VG when controlled by template.
                    if not template_view.AreAnnotationCategoriesHidden:
                         template_view.AreAnnotationCategoriesHidden = True
                         # print("# Set AreAnnotationCategoriesHidden to True (turned off 'Show All').") # Optional status
                    # else:
                         # print("# AreAnnotationCategoriesHidden was already True.") # Optional status

                    # print(f"# Successfully updated View Template: {{template_view.Name}}") # Optional success message

                except Exception as e:
                    print(f"# Error during application of overrides to View Template '{{template_view.Name}}': {{e}}") # Escaped f-string