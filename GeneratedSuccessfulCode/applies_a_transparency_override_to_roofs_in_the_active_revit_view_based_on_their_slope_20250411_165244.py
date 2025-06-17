# Purpose: This script applies a transparency override to roofs in the active Revit view based on their slope.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    Parameter,
    BuiltInParameter,
    ElementId,
    View
)
import System # For exception handling
import math # For slope calculation

# --- Configuration ---
# Slope threshold in degrees
slope_threshold_degrees = 2.0
# Transparency percentage (0 = opaque, 100 = fully transparent)
target_transparency = 75

# --- Get Active View ---
# Assume 'doc' is pre-defined
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active view found, the active 'view' is not a valid View element, or it is a view template.")
    # Optional: Raise an exception if preferred for automation workflows
    # raise ValueError("Active view is not suitable for applying overrides.")
else:
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
    except Exception as calc_e:
        print("# Error calculating slope threshold ratio: {}".format(calc_e))
        slope_threshold_ratio = None # Indicate calculation failure

    if slope_threshold_ratio is not None:
        # --- Create Override Settings ---
        override_settings = OverrideGraphicSettings()
        apply_overrides = True
        try:
            # Set surface transparency (0-100)
            override_settings.SetSurfaceTransparency(target_transparency)
        except System.ArgumentException as e:
             print("# Error setting transparency value ({}): {}. Must be 0-100.".format(target_transparency, e.Message))
             apply_overrides = False # Do not proceed if setting transparency failed
        except Exception as e:
             print("# Unexpected error creating OverrideGraphicSettings: {}".format(e))
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

                        # Check if the roof's slope ratio is less than the threshold ratio
                        # We use abs() for the value in case of slightly negative slopes from modeling,
                        # although ROOF_SLOPE is typically non-negative.
                        if abs(slope_value_ratio) < slope_threshold_ratio:
                            # Apply the override to this specific roof element in the active view
                            active_view.SetElementOverrides(roof.Id, override_settings)
                            roofs_overridden_count += 1
                    else:
                        # Roof might not have a slope parameter (e.g., flat roof by sketch with no slope defined, or certain roof types)
                        # We only act if the parameter exists and meets the criteria.
                        skipped_no_slope_param +=1

                except System.Exception as e:
                    print("# Error processing Roof ID {}: {}".format(roof.Id, e))
                    error_count += 1

            # --- Provide Feedback ---
            if roofs_overridden_count > 0:
                print("# Applied {}% surface transparency override to {} Roof(s) with slope less than {} degrees in the active view '{}'.".format(target_transparency, roofs_overridden_count, slope_threshold_degrees, active_view.Name))
                if skipped_no_slope_param > 0:
                    print("# Also skipped {} roof(s) due to missing or unavailable 'Slope' parameter.".format(skipped_no_slope_param))
            else:
                 if elements_processed > 0 and error_count == 0 and skipped_no_slope_param == 0:
                     print("# No Roof elements found with a 'Slope' parameter less than {} degrees.".format(slope_threshold_degrees))
                 elif elements_processed == 0:
                     print("# No Roof elements found in the document.")
                 elif error_count > 0:
                     print("# Processed {} elements, applied overrides to {}, but encountered {} errors.".format(elements_processed, roofs_overridden_count, error_count))
                 elif skipped_no_slope_param > 0 and roofs_overridden_count == 0 and error_count == 0 :
                      print("# No Roof elements met the slope criteria ({} skipped due to missing or unavailable 'Slope' parameter).".format(skipped_no_slope_param))

    elif slope_threshold_ratio is None:
        # Error during slope calculation was already printed
        print("# Cannot proceed without a valid slope threshold.")