# Purpose: This script highlights walls thicker than a specified threshold in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Potentially needed, included for safety based on examples
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall, ElementId,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    View
)
# from System.Collections.Generic import List # Not strictly required for this specific task, commenting out

# --- Configuration ---
# Target thickness threshold (6 inches = 0.5 feet)
min_thickness_feet = 0.5
# Override color (Red)
override_color = Color(255, 0, 0)

# --- Get Active View ---
# Assuming "current plan view" refers to the active graphical view.
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found, or the active view is a template.")
    # Stop execution if no valid view
else:
    # --- Find Solid Fill Pattern Element Id ---
    solid_pattern_id = ElementId.InvalidElementId
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_fill_elements = []
    for pattern in fill_pattern_collector:
        try:
            fill_pattern = pattern.GetFillPattern()
            # Ensure pattern is valid and solid fill
            if fill_pattern and fill_pattern.IsSolidFill:
                 # Prefer Drafting target type for view overrides
                if fill_pattern.Target == FillPatternTarget.Drafting:
                    solid_pattern_id = pattern.Id
                    break # Found the best match
                elif not solid_fill_elements: # Store the first non-drafting solid fill as fallback
                    solid_fill_elements.append(pattern)
        except Exception:
            # Some patterns might throw errors on GetFillPattern()
            pass

    # If no drafting solid fill was found, use the first solid fill found (if any)
    if solid_pattern_id == ElementId.InvalidElementId and solid_fill_elements:
        solid_pattern_id = solid_fill_elements[0].Id
        # print("# Debug: Using a non-Drafting solid fill pattern as fallback.") # Optional debug

    if solid_pattern_id == ElementId.InvalidElementId:
        print("# Warning: Could not find any 'Solid fill' drafting pattern element. Color override might only affect lines.")

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set Cut Fill Pattern Colors to Red
    override_settings.SetCutForegroundPatternColor(override_color)
    override_settings.SetCutBackgroundPatternColor(override_color) # Ensure background is also red for solid look

    # Set Cut Fill Pattern Visibility to True
    override_settings.SetCutBackgroundPatternVisible(True)
    override_settings.SetCutForegroundPatternVisible(True)

    # Set Cut Fill Pattern to Solid Fill if found
    if solid_pattern_id != ElementId.InvalidElementId:
        override_settings.SetCutForegroundPatternId(solid_pattern_id)
        override_settings.SetCutBackgroundPatternId(solid_pattern_id) # Set background pattern too
        # print(f"# Debug: Using solid fill pattern ID: {solid_pattern_id}") # Optional debug
    else:
        # Fallback: If no solid pattern ID found, only the lines might be colored red.
        # We can also try overriding projection/surface lines/patterns for better visibility
        override_settings.SetProjectionLineColor(override_color)
        # Optionally set surface patterns if cut pattern isn't enough
        # override_settings.SetSurfaceForegroundPatternColor(override_color)
        # override_settings.SetSurfaceBackgroundPatternColor(override_color)
        # override_settings.SetSurfaceForegroundPatternVisible(True)
        # override_settings.SetSurfaceBackgroundPatternVisible(True)
        pass

    # --- Collect and Filter Walls in the Active View ---
    wall_collector = FilteredElementCollector(doc, active_view.Id)\
                     .OfCategory(BuiltInCategory.OST_Walls)\
                     .WhereElementIsNotElementType()

    walls_overridden_count = 0
    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the C# wrapper.
    for wall in wall_collector:
        if isinstance(wall, Wall):
            try:
                # Check wall thickness using the Width property (internal units - feet)
                # Ensure wall has a valid width (e.g., not an in-place wall with complex geometry without a simple width)
                if wall.Width > min_thickness_feet:
                    # Apply the override to this specific wall element in the active view
                    active_view.SetElementOverrides(wall.Id, override_settings)
                    walls_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Error processing wall {wall.Id}: {e}") # Optional debug
                # Silently ignore walls that cause errors (e.g., cannot get Width)
                pass

    # print(f"# Applied overrides to {walls_overridden_count} walls thicker than {min_thickness_feet * 12} inches.") # Optional output