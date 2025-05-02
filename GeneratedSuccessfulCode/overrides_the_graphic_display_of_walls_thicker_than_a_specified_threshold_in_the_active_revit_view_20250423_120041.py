# Purpose: This script overrides the graphic display of walls thicker than a specified threshold in the active Revit view.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall, ElementId,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    View, ViewPlan # Import ViewPlan specifically for type checking clarity
)

# --- Configuration ---
# Target thickness threshold (7 inches = 7/12 feet in internal units)
min_thickness_feet = 7.0 / 12.0
# Override color (Blue: RGB 0, 0, 255)
override_color = Color(0, 0, 255)

# --- Get Active View ---
# Assuming "current plan view" refers to the active graphical view.
# doc and uidoc are assumed to be pre-defined
active_view = doc.ActiveView
# Check if the active view is suitable for graphic overrides (not null, is a view, not a template)
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found, or the active view does not support graphic overrides.")
    # Stop execution if no valid view
else:
    # --- Find Solid Fill Pattern Element Id ---
    solid_pattern_id = ElementId.InvalidElementId
    # Collect fill patterns in the document
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    # List to store potential solid fill elements if drafting type isn't found first
    solid_fill_elements_fallback = []

    for pattern_element in fill_pattern_collector:
        try:
            # Get the actual FillPattern object
            fill_pattern = pattern_element.GetFillPattern()

            # Check if it's a solid fill pattern
            if fill_pattern and fill_pattern.IsSolidFill:
                 # Prefer Drafting target type for view overrides in plan views
                if fill_pattern.Target == FillPatternTarget.Drafting:
                    solid_pattern_id = pattern_element.Id
                    break # Found the preferred pattern, exit loop
                elif not solid_fill_elements_fallback: # Store the first non-drafting solid fill as a fallback
                    solid_fill_elements_fallback.append(pattern_element)

        except Exception:
            # Handle potential errors getting fill patterns (e.g., corrupt data)
            pass

    # If no drafting solid fill was found, use the first non-drafting solid fill found (if any)
    if solid_pattern_id == ElementId.InvalidElementId and solid_fill_elements_fallback:
        solid_pattern_id = solid_fill_elements_fallback[0].Id
        # print("# Debug: Using a non-Drafting solid fill pattern as fallback.") # Optional debug

    if solid_pattern_id == ElementId.InvalidElementId:
        # Warning if no solid fill pattern could be found at all
        print("# Warning: Could not find any 'Solid fill' pattern element. Color override might only affect lines or surface patterns.")

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set Cut Pattern Colors to Blue
    override_settings.SetCutForegroundPatternColor(override_color)
    override_settings.SetCutBackgroundPatternColor(override_color) # Ensure background is also blue for a solid look

    # Set Cut Pattern Visibility to True
    override_settings.SetCutBackgroundPatternVisible(True)
    override_settings.SetCutForegroundPatternVisible(True)

    # Set Cut Fill Pattern to Solid Fill if found
    if solid_pattern_id != ElementId.InvalidElementId:
        override_settings.SetCutForegroundPatternId(solid_pattern_id)
        override_settings.SetCutBackgroundPatternId(solid_pattern_id) # Set background pattern too
    else:
        # Fallback: If no solid pattern ID found, also color projection lines and surface patterns.
        # This ensures some visual feedback even if the cut pattern can't be solid.
        # Note: Cut pattern is primary for walls in plan view, but lines/surface might show for thin walls or elements not cut.
        override_settings.SetProjectionLineColor(override_color)
        override_settings.SetSurfaceForegroundPatternColor(override_color)
        override_settings.SetSurfaceBackgroundPatternColor(override_color)
        override_settings.SetSurfaceForegroundPatternVisible(True)
        override_settings.SetSurfaceBackgroundPatternVisible(True)
        # If a solid pattern was found but couldn't be applied to cut (unlikely if solid_pattern_id is InvalidElementId),
        # we could theoretically apply it to surface here, but the logic above already handles the solid_pattern_id case.

    # --- Collect and Filter Walls in the Active View ---
    # Filter by view first for better performance on large models
    wall_collector = FilteredElementCollector(doc, active_view.Id)\
                     .OfCategory(BuiltInCategory.OST_Walls)\
                     .WhereElementIsNotElementType() # Get instances, not types

    walls_overridden_count = 0

    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the C# wrapper.
    for wall in wall_collector:
        # Double check element type, though collector should handle this
        if isinstance(wall, Wall):
            try:
                # Check wall thickness using the Width property (internal units - feet)
                # Width property is available on wall instances and represents the wall type's width.
                # Ensure wall has a valid Width property value that can be compared.
                if wall.Width > min_thickness_feet:
                    # Apply the override to this specific wall element in the active view
                    active_view.SetElementOverrides(wall.Id, override_settings)
                    walls_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Error processing wall {{wall.Id}}: {{e}}") # Optional debug
                # Silently ignore specific walls that might cause errors (e.g., complex in-place walls)
                pass

    # Provide feedback on the number of walls affected
    print(f"# Applied overrides to {{walls_overridden_count}} walls thicker than {{min_thickness_feet * 12:.2f}} inches in view '{{active_view.Name}}'.")