# Purpose: This script overrides the graphic display of walls thicker than a specified thickness in the active Revit view, changing their cut pattern to solid red.

# Purpose: This script graphically overrides walls thicker than a specified value in the active view by changing their cut pattern color to red and using a solid fill.

# Import necessary classes
import clr
clr.AddReference('System.Collections') # For List potentially needed, although not strictly used in final code
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    ElementId, View
)
# from System.Collections.Generic import List # Not strictly needed for this specific task

# --- Configuration ---
# Target thickness (6 inches = 0.5 feet)
min_thickness_feet = 0.5
# Override color (Red)
override_color = Color(255, 0, 0)
# Name of the solid fill pattern (used as fallback, IsSolidFill is preferred)
# solid_fill_pattern_name = "Solid fill" # Commented out - relying on IsSolidFill

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view found or the active 'view' is not a valid View element.")
    # Stop execution if no valid view
else:
    # --- Find Solid Fill Pattern Element Id ---
    solid_pattern_id = ElementId.InvalidElementId
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_fill_elements = []
    for pattern in fill_pattern_collector:
        try:
            if pattern.GetFillPattern().IsSolidFill:
                solid_fill_elements.append(pattern)
        except Exception:
            # Some patterns might throw errors on GetFillPattern()
            pass

    if solid_fill_elements:
        # Prefer Drafting patterns if available, otherwise take any solid fill
        drafting_solid = [p for p in solid_fill_elements if p.GetFillPattern().Target == FillPatternTarget.Drafting]
        if drafting_solid:
            solid_pattern_id = drafting_solid[0].Id
        else:
            # Fallback to the first solid fill pattern found, regardless of target
            solid_pattern_id = solid_fill_elements[0].Id
            # print("# Debug: Using a non-Drafting solid fill pattern.") # Escaped Optional debug
    else:
        print("# Warning: Could not find any 'Solid fill' pattern element using IsSolidFill. Color override will be applied without explicit pattern ID.")
        # As a further fallback, one could try GetFillPatternElementByName here if needed

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set Cut Fill Pattern Colors to Red
    override_settings.SetCutForegroundPatternColor(override_color)
    override_settings.SetCutBackgroundPatternColor(override_color)

    # Set Cut Fill Pattern Visibility to True
    override_settings.SetCutBackgroundPatternVisible(True)
    override_settings.SetCutForegroundPatternVisible(True)

    # Set Cut Fill Pattern to Solid Fill if found
    if solid_pattern_id != ElementId.InvalidElementId:
        override_settings.SetCutForegroundPatternId(solid_pattern_id)
        override_settings.SetCutBackgroundPatternId(solid_pattern_id)
        # print(f"# Debug: Using solid fill pattern ID: {solid_pattern_id}") # Escaped Optional debug
    else:
        # If no solid pattern ID found, the color settings alone will make it appear solid red.
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
                if wall.Width > min_thickness_feet:
                    # Apply the override to this specific wall element in the active view
                    active_view.SetElementOverrides(wall.Id, override_settings)
                    walls_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Error processing wall {wall.Id}: {e}") # Escaped Optional debug
                # Silently ignore walls that cause errors (e.g., cannot get Width)
                pass

    # print(f"# Applied overrides to {walls_overridden_count} walls thicker than {min_thickness_feet * 12} inches.") # Escaped Optional output