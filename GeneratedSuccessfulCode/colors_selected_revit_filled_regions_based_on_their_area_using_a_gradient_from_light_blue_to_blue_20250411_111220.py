# Purpose: This script colors selected Revit filled regions based on their area, using a gradient from light blue to blue.

# Purpose: This script colors filled regions in Revit based on their area, creating a color gradient from light blue to blue.

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
from System.Collections.Generic import List # Potentially needed for selection handling

# Define the color gradient function (Light Blue to Blue)
def get_gradient_color(area, min_area, max_area):
    """Returns a color based on the area within the specified range (Light Blue to Blue).

    Args:
        area (float): The area of the filled region.
        min_area (float): The minimum area in the dataset.
        max_area (float): The maximum area in the dataset.

    Returns:
        Color: A Revit Color object representing the gradient color.
    """
    # Handle the case where all regions have the same area or only one region exists
    if max_area <= min_area:
        normalized_area = 0.0 # Default to Light Blue if no range
    else:
        normalized_area = (area - min_area) / (max_area - min_area)

    # Interpolate between Light Blue (173, 216, 230) and Blue (0, 0, 255)
    start_r, start_g, start_b = 173, 216, 230
    end_r, end_g, end_b = 0, 0, 255

    red = int(start_r + (end_r - start_r) * normalized_area)
    green = int(start_g + (end_g - start_g) * normalized_area)
    blue = int(start_b + (end_b - start_b) * normalized_area)

    # Clamp the values in case of floating-point inaccuracies or normalization edge cases
    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))

    return Color(red, green, blue)

# Get the active view
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
    # Use raise Exception() for better error handling in RevitPythonShell/pyRevit
    raise ValueError("No active view found.")

# Get selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected.")
    # Use raise Exception() instead of sys.exit()
    raise ValueError("No elements selected.")

# --- Filter for FilledRegions and Calculate Areas ---
min_area = float('inf')
max_area = float('-inf')
filled_regions_with_areas = [] # Store tuples of (region, area)
valid_regions_found = False

for elem_id in selected_ids:
    element = doc.GetElement(elem_id)
    if isinstance(element, FilledRegion):
        try:
            # FilledRegions have an Area parameter (HOST_AREA_COMPUTED)
            area_param = element.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                area_value_internal = area_param.AsDouble()
                # Ensure area is positive and significant (internal units - sq feet)
                if area_value_internal > 1e-9: # Check against a small tolerance
                    filled_regions_with_areas.append((element, area_value_internal))
                    min_area = min(min_area, area_value_internal)
                    max_area = max(max_area, area_value_internal)
                    valid_regions_found = True
            # else: # Optional Debugging
                # print("# Skipping FilledRegion {{}} because area parameter is null or has no value".format(element.Id))
        except Exception as e:
            # print("# Error getting area for FilledRegion {{}}: {{}}".format(element.Id, e)) # Optional Debugging
            pass # Continue if error reading area for one region

# Check if any valid filled regions were found in the selection
if not valid_regions_found:
    print("# No FilledRegion elements with valid areas found in the selection.")
    # Use raise Exception() instead of sys.exit()
    raise ValueError("No valid FilledRegions found in selection.")


# --- Find a Solid Fill Pattern ---
solid_fill_pattern_id = ElementId.InvalidElementId
solid_pattern_found = False
try:
    # Find the first solid fill pattern element
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement).WhereElementIsNotElementType()
    solid_fill_pattern = None
    for fp in fill_pattern_collector:
        fill_pattern = fp.GetFillPattern()
        if fill_pattern.IsSolidFill:
            solid_fill_pattern = fp
            break # Found the first one

    if solid_fill_pattern:
        solid_fill_pattern_id = solid_fill_pattern.Id
        solid_pattern_found = True
    else:
        print("# Warning: No solid fill pattern found in the document. Surface patterns will not be solid.")

except InvalidOperationException: # Catches if filtering finds nothing or logic errors
    print("# Warning: Error occurred while searching for solid fill pattern. Surface patterns might not be solid.")
except Exception as e:
    print("# Error finding solid fill pattern: {}".format(e)) # Use standard format


# --- Apply Color Overrides ---
print("# Applying overrides to {} selected filled regions...".format(len(filled_regions_with_areas)))
count = 0
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

        # Apply solid fill pattern if found
        if solid_pattern_found and solid_fill_pattern_id != ElementId.InvalidElementId:
            ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
            ogs.SetSurfaceBackgroundPatternId(solid_fill_pattern_id) # Apply to background too for solid fill

        # Apply the graphic overrides to the filled region in the active view
        active_view.SetElementOverrides(region.Id, ogs)
        count += 1

    except Exception as e:
        print("# Error setting overrides for FilledRegion {}: {}".format(region.Id, e)) # Use standard format
        pass # Continue processing other regions if one fails

print("# Successfully applied overrides to {} Filled Regions.".format(count))