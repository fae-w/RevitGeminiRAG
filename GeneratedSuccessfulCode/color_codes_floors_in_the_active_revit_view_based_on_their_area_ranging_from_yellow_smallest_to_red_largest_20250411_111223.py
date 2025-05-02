# Purpose: This script color-codes floors in the active Revit view based on their area, ranging from yellow (smallest) to red (largest).

# Purpose: This script color-codes floors in the active Revit view based on their area, ranging from yellow (smallest) to red (largest).

# Import necessary classes
import clr
clr.AddReference('System') # Required for Math
from System import Math
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Floor, ElementId, Color, OverrideGraphicSettings, View, BuiltInParameter

# Get the active view
active_view = doc.ActiveView
if not active_view or not active_view.IsValidObject or not isinstance(active_view, View):
    print("# Error: Could not get a valid active graphical view.")
else:
    # Collect all Floor elements visible in the active view
    collector = FilteredElementCollector(doc, active_view.Id)
    floor_collector = collector.OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

    floors_data = []
    min_area = float('inf')
    max_area = float('-inf')
    has_floors = False

    # First pass: Collect floors and their areas, find min/max area
    for floor in floor_collector:
        if isinstance(floor, Floor):
            area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param:
                area = area_param.AsDouble()
                if area > 0: # Ignore floors with zero or negative area if any
                    floors_data.append({'element': floor, 'area': area})
                    min_area = min(min_area, area)
                    max_area = max(max_area, area)
                    has_floors = True
            else:
                # print(f"# Debug: Could not get area for Floor {floor.Id}")
                pass # Skip floors without area param

    if not has_floors:
        print("# No floors found in the current view or none have a valid area.")
    elif min_area == float('inf'):
         print("# No floors with valid area found.")
    else:
        # Define start (Yellow) and end (Red) colors
        yellow = Color(255, 255, 0)
        red = Color(255, 0, 0)

        # Calculate area range, handle division by zero if all floors have same area
        area_range = max_area - min_area
        if area_range < 0.0001: # Use a small tolerance for float comparison
             area_range = 0 # Treat as single area case

        # Second pass: Apply overrides
        for floor_info in floors_data:
            floor = floor_info['element']
            area = floor_info['area']

            # Calculate interpolation factor (t)
            if area_range == 0:
                t = 0.5 # Assign mid-color (orange-ish) if all areas are the same
            else:
                t = (area - min_area) / area_range
                t = max(0.0, min(1.0, t)) # Clamp t between 0 and 1

            # Interpolate color components
            # R = R_yellow + (R_red - R_yellow) * t = 255 + (255 - 255) * t = 255
            # G = G_yellow + (G_red - G_yellow) * t = 255 + (0 - 255) * t = 255 * (1 - t)
            # B = B_yellow + (B_red - B_yellow) * t = 0 + (0 - 0) * t = 0
            interp_r = 255
            interp_g = int(255 * (1.0 - t))
            interp_b = 0

            # Create Revit Color
            override_color = Color(interp_r, interp_g, interp_b)

            # Create OverrideGraphicSettings
            ogs = OverrideGraphicSettings()

            # Set the surface foreground pattern color (more visible than background)
            # Requires a pattern to be visible, but color override often works without explicit pattern setting
            ogs.SetSurfaceForegroundPatternColor(override_color)
            # Optional: Could also set a solid fill pattern if needed
            # fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
            # solid_fill = next((p for p in fill_pattern_collector if p.GetFillPattern().IsSolidFill), None)
            # if solid_fill:
            #    ogs.SetSurfaceForegroundPatternId(solid_fill.Id)

            # Apply the override to the floor in the view
            try:
                active_view.SetElementOverrides(floor.Id, ogs)
            except Exception as e:
                 print("# Error applying override to floor {}: {}".format(floor.Id, e)) # Escaped format

        # print(f"# Applied color overrides to {len(floors_data)} floors based on area.") # Escaped - Optional debug/confirmation message