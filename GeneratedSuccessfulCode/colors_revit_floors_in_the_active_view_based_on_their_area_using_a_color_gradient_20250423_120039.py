# Purpose: This script colors Revit floors in the active view based on their area, using a color gradient.

﻿# Import necessary classes
import clr
clr.AddReference('System')
clr.AddReference('System.Collections')
from System import Byte
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Floor, ElementId,
    OverrideGraphicSettings, Color, View, BuiltInParameter,
    FillPatternElement, FillPatternTarget
)
from System.Collections.Generic import List

# --- Helper function to find the Solid Fill pattern ---
def find_solid_fill_pattern(doc):
    """Finds the first solid fill pattern element."""
    collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    for pattern_element in collector:
        if pattern_element is not None:
            pattern = pattern_element.GetFillPattern()
            # Check if pattern is not null and is solid fill
            if pattern is not None and pattern.IsSolidFill:
                return pattern_element.Id
    return ElementId.InvalidElementId

# --- Main Script ---

# Get the active view
active_view = doc.ActiveView
if active_view is None:
    print("# Error: No active view found.")
else:
    # Find the solid fill pattern ID
    solid_fill_pattern_id = find_solid_fill_pattern(doc)
    if solid_fill_pattern_id == ElementId.InvalidElementId:
        print("# Error: Could not find a Solid Fill pattern in the document.")
    else:
        # Collect floors visible in the active view and their areas
        floor_collector = FilteredElementCollector(doc, active_view.Id)\
                          .OfCategory(BuiltInCategory.OST_Floors)\
                          .WhereElementIsNotElementType()

        floors_data = []
        min_area = float('inf')
        max_area = float('-inf')

        for floor in floor_collector:
            # Ensure it's a Floor element
            if isinstance(floor, Floor):
                try:
                    # Use HOST_AREA_COMPUTED as it's generally reliable for floors
                    area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                    if area_param and area_param.HasValue:
                        area = area_param.AsDouble()
                        # Only consider floors with a positive area
                        if area > 1e-6: # Using a small epsilon to avoid floating point issues with zero
                            floors_data.append({'id': floor.Id, 'area': area})
                            min_area = min(min_area, area)
                            max_area = max(max_area, area)
                    # else: # Optional: Handle cases where area parameter isn't found
                    #     print(f"# Warning: Could not retrieve area for Floor ID: {floor.Id}") # Escaped
                except Exception as e:
                    # print(f"# Debug: Error processing floor {floor.Id}: {e}") # Escaped
                    pass # Silently skip floors that cause errors

        # Check if we found any floors with valid areas
        if not floors_data:
            print("# No floors with calculable areas found in the current view.")
        elif min_area == float('inf') or max_area == float('-inf'):
             print("# Only floors with zero or invalid area found, cannot create gradient.")
        else:
            # Define start (e.g., Green) and end (e.g., Blue) colors for the gradient
            color_start = Color(0, 255, 0) # Green
            color_end = Color(0, 0, 255)   # Blue

            # Calculate area range (avoid division by zero if all areas are the same)
            area_range = max_area - min_area
            is_range_zero = area_range < 1e-6

            # Apply overrides
            override_count = 0
            for floor_info in floors_data:
                floor_id = floor_info['id']
                area = floor_info['area']

                # Calculate interpolation factor (t) between 0.0 and 1.0
                if is_range_zero:
                    t = 0.5 # Assign a mid-color if all areas are effectively the same
                else:
                    t = (area - min_area) / area_range
                t = max(0.0, min(1.0, t)) # Clamp t to [0, 1] range

                # Interpolate color components (Linear interpolation)
                # Byte conversion ensures values are valid for Color constructor (0-255)
                r = Byte(int(color_start.Red + t * (color_end.Red - color_start.Red)))
                g = Byte(int(color_start.Green + t * (color_end.Green - color_start.Green)))
                b = Byte(int(color_start.Blue + t * (color_end.Blue - color_start.Blue)))
                interpolated_color = Color(r, g, b)

                # Create override settings
                ogs = OverrideGraphicSettings()
                # Set the surface foreground pattern to solid fill
                ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
                # Set the color for the solid fill pattern
                ogs.SetSurfaceForegroundPatternColor(interpolated_color)
                # Ensure the pattern is visible (important!)
                ogs.SetSurfaceForegroundPatternVisible(True)
                # Optional: Set surface transparency if desired (0=opaque, 100=transparent)
                # ogs.SetSurfaceTransparency(0)

                # Apply the overrides to the element in the view
                try:
                    active_view.SetElementOverrides(floor_id, ogs)
                    override_count += 1
                except Exception as e:
                    print("# Error applying override to floor {{{{0}}}}: {{{{1}}}}".format(floor_id, e)) # Escaped format

            # Optional: Print summary
            # print(f"# Applied color overrides to {override_count} floors based on area.") # Escaped