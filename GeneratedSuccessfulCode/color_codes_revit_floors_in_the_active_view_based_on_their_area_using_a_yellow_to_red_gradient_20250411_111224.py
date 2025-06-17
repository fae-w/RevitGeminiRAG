# Purpose: This script color-codes Revit floors in the active view based on their area, using a yellow-to-red gradient.

# Purpose: This script color-codes floors in the active Revit view based on their area, using a gradient from yellow (smallest) to red (largest).

# Import necessary classes
import clr
clr.AddReference('System')
from System import Byte
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Floor, View, OverrideGraphicSettings,
    Color, ElementId, BuiltInParameter, FillPatternElement, FillPatternTarget, Element
)

# --- Helper Function to Find Solid Fill Pattern ---
def find_solid_fill_pattern_id(doc):
    collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_pattern_id = ElementId.InvalidElementId
    for pattern_elem in collector:
        if isinstance(pattern_elem, FillPatternElement):
            pattern = pattern_elem.GetFillPattern()
            # Check if it's a solid fill and suitable for drafting/surface overrides
            if pattern.IsSolidFill and pattern.Target == FillPatternTarget.Drafting:
                solid_pattern_id = pattern_elem.Id
                break # Found the first solid drafting pattern
    return solid_pattern_id

# --- Helper Function for Color Gradient ---
def get_gradient_color(value, min_val, max_val):
    """Calculates a color between yellow and red based on the value's position in the range."""
    if max_val <= min_val:
        # Handle edge case: no range, return yellow
        return Color(255, 255, 0)

    # Normalize value between 0.0 and 1.0
    normalized_value = (value - min_val) / (max_val - min_val)
    normalized_value = max(0.0, min(1.0, normalized_value)) # Clamp between 0 and 1

    # Interpolate between Yellow (255, 255, 0) and Red (255, 0, 0)
    # Red component is constant (255)
    # Green component goes from 255 (yellow) to 0 (red)
    green = int(255 * (1.0 - normalized_value))

    # Ensure components are valid byte values (0-255)
    red_byte = Byte(255)
    green_byte = Byte(max(0, min(255, green)))
    blue_byte = Byte(0)

    return Color(red_byte, green_byte, blue_byte)

# --- Main Script Logic ---
# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view found or active view is not a standard View.")
else:
    # Find the Solid Fill Pattern ID
    solid_fill_id = find_solid_fill_pattern_id(doc)
    if solid_fill_id == ElementId.InvalidElementId:
        print("# Error: Could not find a 'Solid fill' drafting pattern in the document.")
    else:
        # Collect Floor elements visible in the active view
        collector = FilteredElementCollector(doc, active_view.Id)
        floor_collector = collector.OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

        floors_data = []
        min_area = float('inf')
        max_area = float('-inf')

        # Iterate through floors to get areas and find min/max
        for floor in floor_collector:
            if isinstance(floor, Floor):
                area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                if area_param and area_param.HasValue:
                    area = area_param.AsDouble()
                    if area > 0: # Only consider floors with positive area
                        floors_data.append({'element': floor, 'area': area})
                        min_area = min(min_area, area)
                        max_area = max(max_area, area)
                else:
                    # print(f"# Debug: Could not get area for Floor {floor.Id}") # Escaped
                    pass

        # Apply overrides if floors were found and there's an area range
        if floors_data and min_area != float('inf'):
            if min_area == max_area:
                 print("# Only one area value found ({:.2f}), coloring all floors yellow.".format(min_area)) # Escaped format

            count = 0
            for floor_info in floors_data:
                floor = floor_info['element']
                area = floor_info['area']

                # Calculate color based on area
                gradient_color = get_gradient_color(area, min_area, max_area)

                # Create override settings
                override_settings = OverrideGraphicSettings()
                override_settings.SetSurfaceForegroundPatternVisible(True)
                override_settings.SetSurfaceForegroundPatternId(solid_fill_id)
                override_settings.SetSurfaceForegroundPatternColor(gradient_color)

                # Apply overrides to the element in the current view
                try:
                    active_view.SetElementOverrides(floor.Id, override_settings)
                    count += 1
                except Exception as e:
                    print("# Error applying override to floor {}: {}".format(floor.Id, e)) # Escaped format

            # print("# Applied color overrides to {} floors based on area.".format(count)) # Escaped Format - Optional final message

        elif not floors_data:
            print("# No Floor elements with calculable area found in the active view.")
        else: # min_area == float('inf') implies no floors had valid area
             print("# No Floor elements with valid positive area found in the active view.")