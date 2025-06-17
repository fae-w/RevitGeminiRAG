# Purpose: This script colors floors in the active Revit view based on their area, using a yellow-to-red gradient.

# Purpose: This script colors floors in the active Revit view based on their area, using a yellow-to-red gradient.

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

# Define the color gradient function (Yellow to Red)
def get_gradient_color(area, min_area, max_area):
    """Returns a color based on the area within the specified range.

    Args:
        area (float): The area of the floor.
        min_area (float): The minimum area in the dataset.
        max_area (float): The maximum area in the dataset.

    Returns:
        Color: A Revit Color object representing the gradient color.
    """
    normalized_area = (area - min_area) / (max_area - min_area) if max_area > min_area else 0.0
    red = int(255 * normalized_area)
    green = int(255 * (1 - normalized_area))
    blue = 0  # No blue component for a yellow-to-red gradient

    # Clamp the values in case of floating-point inaccuracies
    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))
    return Color(red, green, blue)

# Collect all floors in the current view
collector = FilteredElementCollector(doc, doc.ActiveView.Id).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

# Get the minimum and maximum floor areas
min_area = float('inf')
max_area = float('-inf')

floor_areas = []
for floor in collector:
    if isinstance(floor, Floor):
        try:
            area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param:
                area_value_internal = area_param.AsDouble()
                floor_areas.append(area_value_internal)
                min_area = min(min_area, area_value_internal)
                max_area = max(max_area, area_value_internal)
            else:
                print("# Skipping floor {{}} because area parameter is null".format(floor.Id))
        except Exception as e:
            print("# Error getting area for floor {{}}: {{}}".format(floor.Id, e))

# Apply the color overrides
for floor in collector:
    if isinstance(floor, Floor):
        try:
            area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param:
                area_value_internal = area_param.AsDouble()
                color = get_gradient_color(area_value_internal, min_area, max_area)
                ogs = OverrideGraphicSettings()
                ogs.SetSurfaceForegroundPatternColor(color)
                ogs.SetSurfaceForegroundPatternVisible(True) # Make sure the surface pattern is visible

                #find a solid fill pattern
                solidFillId = ElementId.InvalidElementId
                fpatterns = FilteredElementCollector(doc).OfClass(FillPatternElement)

                for fp in fpatterns:
                    if fp.GetFillPattern().IsSolidFill:
                        solidFillId = fp.Id
                        break
                
                if solidFillId != ElementId.InvalidElementId:
                    ogs.SetSurfaceForegroundPatternId(solidFillId)


                # Get the current view
                view = doc.ActiveView

                # Apply the graphic overrides to the view
                view.SetElementOverrides(floor.Id, ogs)
            else:
                print("# Skipping floor {{}} because area parameter is null".format(floor.Id))

        except Exception as e:
            print("# Error setting overrides for floor {{}}: {{}}".format(floor.Id, e))