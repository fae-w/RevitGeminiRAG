# Purpose: This script colors floors in the active Revit view based on their area, using a gradient.

# Import necessary classes
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
    # Attempt to find by name first for robustness
    solid_pattern_name = "Solid fill" # Common name, adjust if different in templates
    collector_by_name = FilteredElementCollector(doc).OfClass(FillPatternElement)
    for pattern_element in collector_by_name:
        if pattern_element is not None and pattern_element.Name == solid_pattern_name:
            pattern = pattern_element.GetFillPattern()
            if pattern is not None and pattern.IsSolidFill:
                return pattern_element.Id

    # Fallback: Find the first solid fill pattern if name matching fails
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
    # Check if the active view is of a type that supports element overrides (basic View check)
    if not isinstance(active_view, View):
         print("# Error: The active object is not a valid View.")
    else:
        # Find the solid fill pattern ID
        solid_fill_pattern_id = find_solid_fill_pattern(doc)
        if solid_fill_pattern_id == ElementId.InvalidElementId:
            print("# Error: Could not find a Solid Fill pattern in the document. Please ensure one exists.")
        else:
            # Collect floors visible in the active view and their areas
            floor_collector = FilteredElementCollector(doc, active_view.Id)\
                              .OfCategory(BuiltInCategory.OST_Floors)\
                              .WhereElementIsNotElementType()

            floors_data = []
            min_area = float('inf')
            max_area = float('-inf')

            for floor in floor_collector:
                # Ensure it's a Floor element (though collector should handle this)
                if isinstance(floor, Floor):
                    try:
                        # Use HOST_AREA_COMPUTED as it's generally reliable for floors
                        area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                        if area_param and area_param.HasValue:
                            area = area_param.AsDouble()
                            # Only consider floors with a positive area greater than a small threshold
                            if area > 1e-6:
                                floors_data.append({'id': floor.Id, 'area': area}) # Corrected dictionary syntax
                                min_area = min(min_area, area)
                                max_area = max(max_area, area)
                        # else: # Optional: Handle cases where area parameter isn't found
                        #     print("# Warning: Could not retrieve area for Floor ID: {{0}}".format(floor.Id))
                    except Exception as e:
                        # print("# Debug: Error processing floor {{0}}: {{1}}".format(floor.Id, e))
                        pass # Silently skip floors that cause errors

            # Check if we found any floors with valid areas
            if not floors_data:
                print("# No floors with calculable areas found in the current view.")
            elif min_area == float('inf') or max_area == float('-inf') or (max_area - min_area) < 1e-6:
                 # Handle cases with no valid range (only one floor, or all same area)
                 # print("# Only one floor or all floors have the same area. Applying single color.")
                 # Define a single color (e.g., the start color or a mid-color)
                 single_color = Color(255, 128, 0) # Orange as a single color
                 override_count = 0
                 for floor_info in floors_data:
                    floor_id = floor_info['id']
                    ogs = OverrideGraphicSettings()
                    ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
                    ogs.SetSurfaceForegroundPatternColor(single_color)
                    ogs.SetSurfaceForegroundPatternVisible(True)
                    try:
                        active_view.SetElementOverrides(floor_id, ogs)
                        override_count += 1
                    except Exception as e:
                        print("# Error applying override to floor {0}: {1}".format(floor_id, e))
                 # print("# Applied single color override to {0} floors.".format(override_count))
            else:
                # Define start (e.g., Yellow for smallest) and end (e.g., Red for largest) colors for the gradient
                color_start = Color(255, 255, 0) # Yellow
                color_end = Color(255, 0, 0)   # Red

                # Calculate area range
                area_range = max_area - min_area

                # Apply overrides with gradient
                override_count = 0
                for floor_info in floors_data:
                    floor_id = floor_info['id']
                    area = floor_info['area']

                    # Calculate interpolation factor (t) between 0.0 and 1.0
                    # Avoid division by zero, although handled by the earlier check
                    if area_range > 1e-9:
                         t = (area - min_area) / area_range
                    else: # Should not happen due to earlier check, but safety first
                         t = 0.5
                    t = max(0.0, min(1.0, t)) # Clamp t to [0, 1] range

                    # Interpolate color components (Linear interpolation)
                    # Byte conversion ensures values are valid for Color constructor (0-255)
                    r = Byte(int(color_start.Red + t * (color_end.Red - color_start.Red)))
                    g = Byte(int(color_start.Green + t * (color_end.Green - color_start.Green)))
                    b = Byte(int(color_start.Blue + t * (color_end.Blue - color_start.Blue)))
                    interpolated_color = Color(r, g, b)

                    # Create override settings
                    ogs = OverrideGraphicSettings()
                    ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
                    ogs.SetSurfaceForegroundPatternColor(interpolated_color)
                    ogs.SetSurfaceForegroundPatternVisible(True) # Make sure the pattern is visible
                    # Optional: Set surface transparency if desired (0=opaque, 100=transparent)
                    # ogs.SetSurfaceTransparency(0)

                    # Apply the overrides to the element in the view
                    try:
                        active_view.SetElementOverrides(floor_id, ogs)
                        override_count += 1
                    except Exception as e:
                        print("# Error applying override to floor {0}: {1}".format(floor_id, e))

                # Optional: Print summary
                # print("# Applied color overrides to {0} floors based on area gradient.".format(override_count))