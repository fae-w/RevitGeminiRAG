# Purpose: This script colors floors in a Revit view based on their area, interpolating between pink and blue.

# Purpose: This script colors floors in the active Revit view based on their area, interpolating between pink and blue.

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
            # Ensure it's actually a Floor element (not a FloorType)
            if isinstance(floor, Floor):
                try:
                    # Use HOST_AREA_COMPUTED as it's generally reliable for floors
                    area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                    if area_param and area_param.HasValue:
                        area = area_param.AsDouble()
                        # Only consider floors with a positive area greater than a small tolerance
                        if area > 1e-6:
                           floors_data.append({'id': floor.Id, 'area': area})
                           min_area = min(min_area, area)
                           max_area = max(max_area, area)
                    # else: # Optional: Handle cases where area cannot be determined
                    #    print(f"# Warning: Could not get area for floor {floor.Id}") # Escaped
                except Exception as e:
                    # print(f"# Debug: Error processing floor {floor.Id}: {e}") # Escaped
                    pass # Silently skip floors that cause errors

        # Check if we found any floors with valid areas
        if not floors_data:
            print("# No floors with calculable areas found in the current view.")
        elif min_area == float('inf') or max_area == float('-inf'):
             print("# Only floors with zero or invalid area found.")
        else:
            # Define start (Pink) and end (Blue) colors
            # Using a common pink shade
            color_start = Color(255, 192, 203) # Pink
            color_end = Color(0, 0, 255)       # Blue

            # Calculate area range (avoid division by zero if all areas are the same)
            area_range = max_area - min_area
            if area_range < 1e-6: # Effectively zero range or single floor
                area_range = 1.0 # Avoid division by zero, all will get a mid-point color

            # Apply overrides
            override_count = 0
            for floor_info in floors_data:
                floor_id = floor_info['id']
                area = floor_info['area']

                # Calculate interpolation factor (0 for min area, 1 for max area)
                if area_range > 1e-6:
                   t = (area - min_area) / area_range
                else:
                   t = 0.5 # Midpoint if range is zero (or all same area)

                # Clamp t to be strictly between 0.0 and 1.0
                t = max(0.0, min(1.0, t))

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
                # Ensure the pattern is visible (might be off by default)
                ogs.SetSurfaceForegroundPatternVisible(True)

                # Apply the overrides to the element in the view
                try:
                    active_view.SetElementOverrides(floor_id, ogs)
                    override_count += 1
                except Exception as e:
                    print("# Error applying override to floor {0}: {1}".format(floor_id, e)) # Escaped format

            # Optional: Print summary
            # print("# Applied color overrides to {0} floors based on area.".format(override_count)) # Escaped