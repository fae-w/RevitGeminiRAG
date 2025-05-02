# Purpose: This script overrides the graphic display of all walls in the active plan view, changing their surface pattern to solid red.

# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # For Color potentially, though usually okay
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    ElementId, View, ViewType
)

# --- Configuration ---
# Override color (Red)
override_color = Color(255, 0, 0)
# Define acceptable plan view types
plan_view_types = [
    ViewType.FloorPlan,
    ViewType.CeilingPlan,
    ViewType.AreaPlan,
    ViewType.EngineeringPlan,
    # Add other plan-like views if necessary
]

# --- Get Active View ---
active_view = doc.ActiveView

# --- Validate Active View ---
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    # print("# Error: Requires an active, non-template view.") # Optional info
    pass # Silently exit if not a valid view or is a template
elif active_view.ViewType not in plan_view_types:
    # print(f"# Info: Active view '{active_view.Name}' is not a plan view type. Script applies only to plan views.") # Optional info
    pass # Silently exit if not a plan view
else:
    # --- Find Solid Fill Pattern Element Id ---
    solid_pattern_id = ElementId.InvalidElementId
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_fill_elements = []
    for pattern in fill_pattern_collector:
        try:
            fill_pattern = pattern.GetFillPattern()
            # Ensure it's a Drafting pattern and it's solid
            if fill_pattern.Target == FillPatternTarget.Drafting and fill_pattern.IsSolidFill:
                solid_fill_elements.append(pattern)
        except Exception:
            # Some patterns might throw errors
            pass

    if solid_fill_elements:
        # Use the first drafting solid fill pattern found
        solid_pattern_id = solid_fill_elements[0].Id
        # print(f"# Debug: Found solid fill pattern ID: {{{solid_pattern_id}}}") # Optional debug
    else:
        # Try finding *any* solid fill if no drafting solid fill was found
        fill_pattern_collector_any = FilteredElementCollector(doc).OfClass(FillPatternElement)
        for pattern in fill_pattern_collector_any:
             try:
                 if pattern.GetFillPattern().IsSolidFill:
                     solid_pattern_id = pattern.Id
                     # print(f"# Debug: Found non-drafting solid fill pattern ID: {{{solid_pattern_id}}}") # Optional debug
                     break # Use the first one found
             except Exception:
                 pass

    if solid_pattern_id == ElementId.InvalidElementId:
        print("# Warning: Could not find any 'Solid fill' pattern element. Walls will be colored red but might not appear solid.")
        # Proceed without setting pattern ID, relying on color only

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set Surface Fill Pattern Colors to Red
    override_settings.SetSurfaceForegroundPatternColor(override_color)
    # Setting background can help ensure solidity, especially if transparency is involved elsewhere
    override_settings.SetSurfaceBackgroundPatternColor(override_color)

    # Set Surface Fill Pattern Visibility to True
    override_settings.SetSurfaceBackgroundPatternVisible(True)
    override_settings.SetSurfaceForegroundPatternVisible(True)

    # Set Surface Fill Pattern to Solid Fill if found
    if solid_pattern_id != ElementId.InvalidElementId:
        override_settings.SetSurfaceForegroundPatternId(solid_pattern_id)
        override_settings.SetSurfaceBackgroundPatternId(solid_pattern_id) # Use solid for background too

    # --- Collect Walls in the Active View ---
    wall_collector = FilteredElementCollector(doc, active_view.Id)\
                     .OfCategory(BuiltInCategory.OST_Walls)\
                     .WhereElementIsNotElementType()

    walls_overridden_count = 0
    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the C# wrapper.
    for wall in wall_collector:
        if isinstance(wall, Wall):
            try:
                # Apply the override to this specific wall element in the active view
                active_view.SetElementOverrides(wall.Id, override_settings)
                walls_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Error processing wall {{{wall.Id}}}: {{{e}}}") # Optional debug
                # Silently ignore walls that cause errors
                pass

    # print(f"# Applied solid red surface override to {{{walls_overridden_count}}} walls in view '{active_view.Name}'.") # Optional info