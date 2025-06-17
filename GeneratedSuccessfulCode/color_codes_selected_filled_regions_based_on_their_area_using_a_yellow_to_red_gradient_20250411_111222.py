# Purpose: This script color-codes selected filled regions based on their area, using a yellow-to-red gradient.

# Purpose: This script color-codes filled regions in the active Revit view based on their area, using a yellow-to-red gradient.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FilledRegion,
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    ElementId,
    BuiltInParameter
)
from System import InvalidOperationException # For FirstElement potential error
from System.Collections.Generic import List # Potentially needed, though GetElementIds returns ICollection

# Define the color gradient function (Yellow to Red)
def get_gradient_color(area, min_area, max_area):
    """Returns a color based on the area within the specified range (Yellow to Red).

    Args:
        area (float): The area of the filled region.
        min_area (float): The minimum area in the dataset.
        max_area (float): The maximum area in the dataset.

    Returns:
        Color: A Revit Color object representing the gradient color.
    """
    # Handle the case where all regions have the same area or only one region exists
    if max_area <= min_area:
        normalized_area = 0.0 # Default to yellow if no range
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

# Get selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected.")
    # Exit the script if nothing is selected
    import sys
    sys.exit()

# --- Filter for FilledRegions and Calculate Areas ---
min_area = float('inf')
max_area = float('-inf')
filled_regions_with_areas = [] # Store tuples of (region, area)

for elem_id in selected_ids:
    element = doc.GetElement(elem_id)
    if isinstance(element, FilledRegion):
        try:
            # FilledRegions have an Area parameter (HOST_AREA_COMPUTED)
            area_param = element.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                area_value_internal = area_param.AsDouble()
                if area_value_internal > 0: # Consider only regions with positive area
                    filled_regions_with_areas.append((element, area_value_internal))
                    min_area = min(min_area, area_value_internal)
                    max_area = max(max_area, area_value_internal)
            # else:
                # print("# Skipping FilledRegion {{{{{{{{}}}}}}}} because area parameter is null or has no value".format(element.Id)) # Optional Debug
        except Exception as e:
            # print("# Error getting area for FilledRegion {{{{{{{{}}}}}}}}: {{{{{{{{}}}}}}}}".format(element.Id, e)) # Optional Debug
            pass

# Check if any valid filled regions were found in the selection
if not filled_regions_with_areas:
    print("# No FilledRegion elements with valid areas found in the selection.")
    import sys
    sys.exit()

# --- Find a Solid Fill Pattern ---
solid_fill_pattern_id = ElementId.InvalidElementId
try:
    # Efficiently get the first solid fill pattern
    # Use WhereElementIsNotElementType() to avoid matching FillPatternElement types themselves if not needed
    # Filter for drafting patterns as required by SetSurfaceForegroundPatternId
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement).WhereElementIsNotElementType()
    solid_fill_pattern = None
    for fp in fill_pattern_collector:
        fill_pattern = fp.GetFillPattern()
        if fill_pattern.IsSolidFill: # and fill_pattern.Target == FillPatternTarget.Drafting: # Drafting target is implicitly handled by FilledRegion overrides
            solid_fill_pattern = fp
            break # Found the first one

    if solid_fill_pattern:
        solid_fill_pattern_id = solid_fill_pattern.Id
    else:
        print("# Warning: No solid fill pattern found in the document. Surface patterns will not be solid.")
except InvalidOperationException: # Catches if filtering finds nothing or logic errors
    print("# Warning: Error occurred while searching for solid fill pattern. Surface patterns might not be solid.")
except Exception as e:
    print("# Error finding solid fill pattern: {{}}".format(e)) # Escaped

# Check if a solid fill pattern was found before proceeding
if solid_fill_pattern_id == ElementId.InvalidElementId:
    print("# Error: Cannot proceed without a solid fill pattern. Ensure one exists in the project.")
    import sys
    sys.exit()


# --- Apply Color Overrides ---
for region, area_value_internal in filled_regions_with_areas:
    try:
        color = get_gradient_color(area_value_internal, min_area, max_area)
        ogs = OverrideGraphicSettings()

        # Set surface foreground pattern color
        ogs.SetSurfaceForegroundPatternColor(color)
        ogs.SetSurfaceForegroundPatternVisible(True)

        # Set surface background pattern color to match foreground for solid appearance
        ogs.SetSurfaceBackgroundPatternColor(color)
        ogs.SetSurfaceBackgroundPatternVisible(True)

        # Apply solid fill pattern
        ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
        ogs.SetSurfaceBackgroundPatternId(solid_fill_pattern_id) # Apply to background too for solid fill

        # Apply the graphic overrides to the filled region in the active view
        active_view.SetElementOverrides(region.Id, ogs)

    except Exception as e:
        # print("# Error setting overrides for FilledRegion {{{{{{{{}}}}}}}}: {{{{{{{{}}}}}}}}".format(region.Id, e)) # Optional Debug
        pass