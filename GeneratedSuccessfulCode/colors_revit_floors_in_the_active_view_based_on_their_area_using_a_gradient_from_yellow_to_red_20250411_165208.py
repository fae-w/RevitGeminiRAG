# Purpose: This script colors Revit floors in the active view based on their area, using a gradient from yellow to red.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Floor,
    OverrideGraphicSettings,
    Color,
    View,
    BuiltInParameter,
    FillPatternElement,
    ElementId
)
from System import InvalidOperationException # For potential errors

# Define the color gradient function (Yellow to Red)
def get_gradient_color(area, min_area, max_area):
    """Returns a color based on the area within the specified range (Yellow to Red).

    Args:
        area (float): The area of the floor.
        min_area (float): The minimum area in the dataset.
        max_area (float): The maximum area in the dataset.

    Returns:
        Color: A Revit Color object representing the gradient color.
    """
    # Handle the case where all floors have the same area or only one floor exists
    if max_area <= min_area:
        normalized_area = 0.0 # Default to yellow if no range or single element
    else:
        normalized_area = (area - min_area) / (max_area - min_area)

    # Interpolate between Yellow (255, 255, 0) and Red (255, 0, 0)
    red = 255  # Red component is always 255 in this gradient
    green = int(255 * (1 - normalized_area))
    blue = 0   # Blue component is always 0 in this gradient

    # Clamp the values in case of floating-point inaccuracies
    green = max(0, min(255, green))

    return Color(red, green, blue)

# Get the active view
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
    # Exit the script if no active view
    import sys
    sys.exit()

# Collect all floors visible in the current view
collector = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

# --- Find Min/Max Area ---
min_area = float('inf')
max_area = float('-inf')
floors_with_areas = [] # Store tuples of (floor, area)

for floor in collector:
    if isinstance(floor, Floor):
        try:
            area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                area_value_internal = area_param.AsDouble()
                if area_value_internal >= 0: # Consider floors with zero or positive area
                    floors_with_areas.append((floor, area_value_internal))
                    min_area = min(min_area, area_value_internal)
                    max_area = max(max_area, area_value_internal)
            # else:
                # print("# Skipping floor {{{{}}}} because area parameter is null or has no value".format(floor.Id)) # Optional Debug - Escaped
        except Exception as e:
            # print("# Error getting area for floor {{{{}}}}: {{{{}}}}".format(floor.Id, e)) # Optional Debug - Escaped
            pass

# Check if any valid floors were found
if not floors_with_areas:
    print("# No floors with valid areas found in the current view.")
    import sys
    sys.exit()

# --- Find a Solid Fill Pattern ---
solid_fill_pattern_id = ElementId.InvalidElementId
try:
    # Efficiently get the first solid fill pattern
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_fill_pattern = None
    for fp in fill_pattern_collector:
        if fp.GetFillPattern().IsSolidFill:
            solid_fill_pattern = fp
            break # Found the first one

    if solid_fill_pattern:
        solid_fill_pattern_id = solid_fill_pattern.Id
    else:
        print("# Warning: No solid fill pattern found in the document. Surface patterns will not be solid.")
except Exception as e:
    print("# Error finding solid fill pattern: {{{{}}}}".format(e)) # Escaped

# --- Apply Color Overrides ---
for floor, area_value_internal in floors_with_areas:
    try:
        color = get_gradient_color(area_value_internal, min_area, max_area)
        ogs = OverrideGraphicSettings()

        # Set surface foreground pattern color
        ogs.SetSurfaceForegroundPatternColor(color)
        ogs.SetSurfaceForegroundPatternVisible(True)

        # Set surface background pattern color to match foreground for solid appearance
        ogs.SetSurfaceBackgroundPatternColor(color)
        ogs.SetSurfaceBackgroundPatternVisible(True) # Ensure background is visible

        # Apply solid fill pattern if found
        if solid_fill_pattern_id != ElementId.InvalidElementId:
            ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
            ogs.SetSurfaceBackgroundPatternId(solid_fill_pattern_id) # Apply to background too for solid fill

        # Apply the graphic overrides to the floor in the active view
        active_view.SetElementOverrides(floor.Id, ogs)

    except Exception as e:
        print("# Error setting overrides for floor {{{{}}}}: {{{{}}}}".format(floor.Id, e)) # Escaped
        pass