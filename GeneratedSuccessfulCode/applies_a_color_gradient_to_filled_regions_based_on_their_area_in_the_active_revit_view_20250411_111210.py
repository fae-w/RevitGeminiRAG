# Purpose: This script applies a color gradient to filled regions based on their area in the active Revit view.

# Purpose: This script applies a color gradient (yellow to red) to filled regions in the active Revit view based on their area.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FilledRegion,
    OverrideGraphicSettings,
    Color,
    View,
    BuiltInParameter,
    FillPatternElement,
    ElementId
)
# Ensure System.Collections.Generic is available for Where extension method with lambda
clr.AddReference("System.Core")
from System import Func # Required for lambda in Where


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
    # Use raise Exception() instead of sys.exit() for better error handling in RevitPythonShell/pyRevit
    raise ValueError("No active view found.") # Keeping this error as it's critical

# Collect all Filled Regions visible in the current view
collector = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_FilledRegion).WhereElementIsNotElementType()

# --- Find Min/Max Area ---
min_area = float('inf')
max_area = float('-inf')
regions_with_areas = [] # Store tuples of (region, area)
valid_regions_found = False

# Check if collector has any elements before iterating (optional optimization)
# if not collector.Any(): # Requires Linq - might not be directly available or intuitive in IronPython
#    print("# No Filled Regions found in the current view.")
# else:

for region in collector:
    # No need for isinstance check due to collector setup, but harmless
    if isinstance(region, FilledRegion):
        try:
            # Filled Regions use HOST_AREA_COMPUTED for their Area parameter
            area_param = region.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                area_value_internal = area_param.AsDouble()
                # Ensure area is positive and significant (internal units - sq feet)
                if area_value_internal > 1e-9: # Check against a small tolerance
                    regions_with_areas.append((region, area_value_internal))
                    min_area = min(min_area, area_value_internal)
                    max_area = max(max_area, area_value_internal)
                    valid_regions_found = True
            # else: # Optional Debugging
                # print("# Skipping FilledRegion {} because area parameter is null or has no value".format(region.Id))
        except Exception as e:
            # print("# Error getting area for FilledRegion {}: {}".format(region.Id, e)) # Optional Debugging
            pass # Continue if error reading area for one region


# Check if any valid filled regions were found
if not valid_regions_found:
    print("# No Filled Regions with valid areas found in the current view. Script finished.")
    # Removed 'raise ValueError' to prevent script halt when no regions are found.
    # The script will now finish gracefully after printing the message.
else:
    # --- Find a Solid Fill Pattern ---
    solid_fill_pattern_id = ElementId.InvalidElementId
    solid_pattern_found = False
    try:
        # Create a lambda function explicitly for the Where clause
        # This often helps with IronPython compatibility
        is_solid_fill = Func[FillPatternElement, bool](lambda fp: fp.GetFillPattern().IsSolidFill)

        # Use FirstOrDefaultElement() for potentially better performance if available and compatible
        # For broader compatibility, stick with ToElements() and check the list
        # solid_pattern = FilteredElementCollector(doc).OfClass(FillPatternElement).Where(is_solid_fill).FirstOrDefaultElement()
        # if solid_pattern:
        #      solid_fill_pattern_id = solid_pattern.Id
        #      solid_pattern_found = True

        # Using ToElements() approach from original code for safety
        solid_fill_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).Where(is_solid_fill).ToElements()
        if solid_fill_patterns and len(solid_fill_patterns) > 0:
             solid_fill_pattern_id = solid_fill_patterns[0].Id
             solid_pattern_found = True

        if not solid_pattern_found:
            print("# Warning: No solid fill pattern found in the document. Surface patterns cannot be set to solid.")

    except Exception as e:
        print("# Error finding solid fill pattern: {}".format(e))


    # --- Apply Color Overrides ---
    print("# Applying overrides to {} filled regions...".format(len(regions_with_areas)))
    count = 0
    for region, area_value_internal in regions_with_areas:
        try:
            color = get_gradient_color(area_value_internal, min_area, max_area)
            ogs = OverrideGraphicSettings()

            # Set surface foreground pattern color regardless of pattern availability
            ogs.SetSurfaceForegroundPatternColor(color)
            ogs.SetSurfaceForegroundPatternVisible(True) # Make foreground visible

            # Set surface background pattern color (same color for solid appearance)
            # This helps ensure solid appearance even if only color is applied
            ogs.SetSurfaceBackgroundPatternColor(color)
            ogs.SetSurfaceBackgroundPatternVisible(True) # Make background visible

            # Only set the pattern ID if a valid solid fill pattern was found
            if solid_pattern_found and solid_fill_pattern_id != ElementId.InvalidElementId:
                ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
                ogs.SetSurfaceBackgroundPatternId(solid_fill_pattern_id) # Use solid for background too
            # else: # Optional Debugging
                # if region.Id == regions_with_areas[0][0].Id: # Print only once
                    # print("# Debug: Solid pattern not found or invalid, applying color only.")


            # Apply the graphic overrides to the filled region in the active view
            active_view.SetElementOverrides(region.Id, ogs)
            count += 1

        except Exception as e:
            print("# Error setting overrides for FilledRegion {}: {}".format(region.Id, e))
            pass # Continue processing other regions if one fails

    print("# Successfully applied overrides to {} Filled Regions.".format(count))