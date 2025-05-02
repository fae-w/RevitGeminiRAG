# Purpose: This script highlights non-bearing walls in the active Revit view with a light gray surface override.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Color and Exceptions
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Wall,
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    ElementId,
    BuiltInCategory,
    View,
    ElementIsElementTypeFilter,
    BuiltInParameter
)
# The Structure namespace classes are within RevitAPI.dll, no extra reference needed
import Autodesk.Revit.DB.Structure # Needed for StructuralWallUsage enum
import System # For exception handling

# --- Configuration ---
# Use the enum directly from the Structure namespace
target_usage_value = int(Autodesk.Revit.DB.Structure.StructuralWallUsage.NonBearing)
light_gray_color = Color(192, 192, 192) # Define light gray color

# --- Script Core Logic ---

# Get the active view
# uidoc is assumed to be available
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    # Use print for simple feedback; avoid raising exceptions unless necessary for workflow control
    print("# Error: No active graphical view found or active view is a template.")
    # Exit script cleanly if no suitable view
    import sys
    sys.exit()

# --- Find a Solid Fill Pattern ---
solid_fill_pattern_id = ElementId.InvalidElementId
try:
    # Use FirstElement() for efficiency if any solid fill is acceptable
    solid_fill_pattern_element = FilteredElementCollector(doc)\
                                .OfClass(FillPatternElement)\
                                .WhereElementIsNotElementType()\
                                .FirstElement(lambda fp: fp.GetFillPattern().IsSolidFill)

    if solid_fill_pattern_element:
        solid_fill_pattern_id = solid_fill_pattern_element.Id
    else:
        print("# Warning: No solid fill pattern found in the document. Surface override might not appear solid.")
        # Proceed without a specific pattern ID

except System.Exception as e:
    print("# Warning: Error occurred while searching for solid fill pattern: {}. Proceeding without pattern.".format(e))
    solid_fill_pattern_id = ElementId.InvalidElementId # Ensure it's invalid if error occurs

# --- Define Override Graphic Settings ---
override_settings = OverrideGraphicSettings()

# Set surface foreground pattern color to light gray
override_settings.SetSurfaceForegroundPatternColor(light_gray_color)
override_settings.SetSurfaceForegroundPatternVisible(True)
if solid_fill_pattern_id != ElementId.InvalidElementId:
    override_settings.SetSurfaceForegroundPatternId(solid_fill_pattern_id)

# Set surface background pattern color to light gray (for solid appearance)
# Setting background ensures solid appearance even if default foreground pattern isn't solid
override_settings.SetSurfaceBackgroundPatternColor(light_gray_color)
override_settings.SetSurfaceBackgroundPatternVisible(True)
if solid_fill_pattern_id != ElementId.InvalidElementId:
    override_settings.SetSurfaceBackgroundPatternId(solid_fill_pattern_id)


# --- Collect and Override Walls ---
applied_count = 0
error_count = 0
processed_count = 0

try:
    # Collect all wall instances in the active view
    wall_collector = FilteredElementCollector(doc, active_view.Id)\
                        .OfCategory(BuiltInCategory.OST_Walls)\
                        .WhereElementIsNotElementType()

    for wall in wall_collector:
        processed_count += 1
        if isinstance(wall, Wall): # Ensure it's a Wall instance
            try:
                # Get the 'Structural Usage' parameter
                usage_param = wall.get_Parameter(BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM)

                # Check if the parameter exists and its value matches NonBearing
                if usage_param and usage_param.HasValue and usage_param.AsInteger() == target_usage_value:
                    try:
                        active_view.SetElementOverrides(wall.Id, override_settings)
                        applied_count += 1
                    except System.Exception as apply_ex:
                        print("# Error applying override to Wall ID {}: {}".format(wall.Id, apply_ex.Message))
                        error_count += 1
            except System.Exception as param_ex:
                # Catch errors getting the parameter (might not exist on some walls)
                # print("# Info: Could not check parameter for Wall ID {}: {}".format(wall.Id, param_ex.Message)) # Optional debug info
                pass # Ignore walls where parameter check fails

except System.Exception as general_ex:
    print("# Error during wall collection or processing: {}".format(general_ex))
    error_count += 1

# --- Final Summary ---
if applied_count > 0:
    print("# Successfully applied light gray surface override to {} Non-bearing walls.".format(applied_count))
elif processed_count > 0 and error_count == 0:
     print("# No Non-bearing walls found among the {} walls processed in the active view.".format(processed_count))
elif processed_count == 0 and error_count == 0:
     print("# No walls found in the active view.")

if error_count > 0:
    print("# Encountered {} errors during processing.".format(error_count))