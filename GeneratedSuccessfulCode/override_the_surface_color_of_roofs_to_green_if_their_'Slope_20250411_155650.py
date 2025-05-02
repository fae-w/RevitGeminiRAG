# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Color and Exceptions
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    ElementId,
    View,
    BuiltInParameter,
    ElementIsElementTypeFilter
)
import System # For exception handling
import math # For slope calculation

# --- Configuration ---
# Slope threshold in degrees
slope_threshold_degrees = 30.0
# Target color (Green)
target_color = Color(0, 128, 0) # RGB for Green

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found, the active 'view' is not a valid View element, or it is a view template.")
    # Exit script cleanly if no suitable view
    import sys
    sys.exit()

# --- Calculate Slope Threshold (Ratio) ---
try:
    slope_threshold_radians = math.radians(slope_threshold_degrees)
    # Handle potential vertical slope (tan(90) is undefined) or near vertical
    # ROOF_SLOPE parameter is rise/run, so 90 degrees would be infinite ratio
    if abs(slope_threshold_degrees - 90.0) < 1e-9:
        slope_threshold_ratio = float('inf') # Effectively infinite slope ratio for comparison
    elif abs(slope_threshold_degrees + 90.0) < 1e-9:
         slope_threshold_ratio = float('-inf') # Though slope param usually positive
    else:
        slope_threshold_ratio = math.tan(slope_threshold_radians) # Slope ratio tan(angle)
except System.Exception as calc_e:
    print("# Error calculating slope threshold ratio: {{}}".format(calc_e))
    slope_threshold_ratio = None # Indicate calculation failure

if slope_threshold_ratio is not None:
    # --- Find a Solid Fill Pattern ---
    solid_fill_pattern_id = ElementId.InvalidElementId
    try:
        # Use FirstElement() for efficiency if any solid fill is acceptable
        solid_fill_pattern_element = FilteredElementCollector(doc)\
                                    .OfClass(FillPatternElement)\
                                    .WhereElementIsNotElementType()\
                                    .First(lambda fp: fp.GetFillPattern().IsSolidFill) # Using Linq-like extension method syntax common in pyRevit

        if solid_fill_pattern_element:
            solid_fill_pattern_id = solid_fill_pattern_element.Id
        else:
            print("# Warning: No solid fill pattern found in the document. Surface override might not appear solid.")
            # Proceed without a specific pattern ID

    except System.Exception as e:
        print("# Warning: Error occurred while searching for solid fill pattern: {{}}. Proceeding without pattern.".format(e))
        solid_fill_pattern_id = ElementId.InvalidElementId # Ensure it's invalid if error occurs


    # --- Define Override Graphic Settings ---
    override_settings = OverrideGraphicSettings()
    apply_overrides = True
    try:
        # Set surface foreground pattern color to green
        override_settings.SetSurfaceForegroundPatternColor(target_color)
        override_settings.SetSurfaceForegroundPatternVisible(True)
        if solid_fill_pattern_id != ElementId.InvalidElementId:
            override_settings.SetSurfaceForegroundPatternId(solid_fill_pattern_id)

        # Set surface background pattern color to green (for solid appearance)
        # Setting background ensures solid appearance even if default foreground pattern isn't solid
        override_settings.SetSurfaceBackgroundPatternColor(target_color)
        override_settings.SetSurfaceBackgroundPatternVisible(True)
        if solid_fill_pattern_id != ElementId.InvalidElementId:
            override_settings.SetSurfaceBackgroundPatternId(solid_fill_pattern_id)

    except System.Exception as e:
         print("# Unexpected error creating OverrideGraphicSettings: {{}}".format(e))
         apply_overrides = False

    if apply_overrides:
        # --- Collect Roof Elements ---
        roof_collector = FilteredElementCollector(doc)\
                         .OfCategory(BuiltInCategory.OST_Roofs)\
                         .WhereElementIsNotElementType()

        roofs_overridden_count = 0
        elements_processed = 0
        error_count = 0
        skipped_no_slope_param = 0

        # --- Apply Overrides ---
        # Note: The script runs inside an existing transaction provided by the C# wrapper.
        for roof in roof_collector:
            elements_processed += 1
            try:
                # ROOF_SLOPE parameter stores the slope as a unitless ratio (rise/run).
                slope_param = roof.get_Parameter(BuiltInParameter.ROOF_SLOPE)

                if slope_param and slope_param.HasValue:
                    slope_value_ratio = slope_param.AsDouble()

                    # Check if the roof's slope ratio is greater than the threshold ratio
                    # Use abs() just in case of slightly negative values from modelling, though typically positive
                    if abs(slope_value_ratio) > slope_threshold_ratio:
                        # Apply the override to this specific roof element in the active view
                        active_view.SetElementOverrides(roof.Id, override_settings)
                        roofs_overridden_count += 1
                else:
                    # Roof might not have a slope parameter (e.g., flat roof by sketch with no slope defined, or certain roof types)
                    # We only act if the parameter exists and meets the criteria.
                    skipped_no_slope_param +=1

            except System.Exception as e:
                print("# Error processing Roof ID {{}}: {{}}".format(roof.Id, e))
                error_count += 1

        # --- Provide Feedback ---
        if roofs_overridden_count > 0:
            print("# Applied green surface color override to {{}} Roof(s) with slope greater than {{}} degrees in the active view '{{}}'.".format(roofs_overridden_count, slope_threshold_degrees, active_view.Name))
            if skipped_no_slope_param > 0:
                 print("# Also skipped {{}} roof(s) due to missing or unavailable 'Slope' parameter.".format(skipped_no_slope_param))
        else:
             if elements_processed > 0 and error_count == 0 and skipped_no_slope_param == 0:
                 print("# No Roof elements found with a 'Slope' parameter greater than {{}} degrees.".format(slope_threshold_degrees))
             elif elements_processed == 0:
                 print("# No Roof elements found in the document.")
             elif error_count > 0:
                 print("# Processed {{}} elements, applied overrides to {{}}, but encountered {{}} errors.".format(elements_processed, roofs_overridden_count, error_count))
             elif skipped_no_slope_param > 0 and roofs_overridden_count == 0 and error_count == 0 :
                  print("# No Roof elements met the slope criteria ({{}} skipped due to missing or unavailable 'Slope' parameter).".format(skipped_no_slope_param))

elif slope_threshold_ratio is None:
    # Error during slope calculation was already printed
    print("# Cannot proceed without a valid slope threshold.")