# Purpose: This script updates window sill heights based on provided Mark and height data.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException
from System.Collections.Generic import Dictionary # For mapping Mark to Height

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance, # Windows are typically FamilyInstances
    Element,
    ElementId,
    BuiltInParameter,
    Parameter,
    UnitUtils,
    ForgeTypeId, # For modern unit handling (Revit 2021+)
    UnitTypeId # For modern unit handling (Revit 2021+)
)

# --- Configuration ---
# Input data provided in the prompt
input_data_string = """Mark,SillHeight
W-E-01,900
W-E-02,850
W-E-03,950"""

# Threshold for checking existing sill height (in mm)
threshold_mm = 100.0

# BuiltInParameter for 'Sill Height' on window instances
sill_height_bip = BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM
# BuiltInParameter for 'Mark' value on instances
mark_bip = BuiltInParameter.ALL_MODEL_MARK

# --- Initialization ---
target_heights_mm = {}
target_heights_internal = Dictionary[str, float]() # Map Mark (string) to internal height (float)
updated_count = 0
skipped_mark_not_found = 0
skipped_above_threshold = 0
skipped_no_mark_param = 0
skipped_no_sill_param = 0
skipped_sill_read_only = 0
skipped_input_parse_error = 0
error_count = 0
threshold_internal = None

# --- Step 1: Parse Input Data and Convert Target Heights ---
lines = input_data_string.strip().split('\n')
if len(lines) > 1: # Check if there is data beyond the header
    for i, line in enumerate(lines[1:]): # Skip header line
        parts = line.split(',')
        if len(parts) == 2:
            mark = parts[0].strip()
            height_str = parts[1].strip()
            if not mark:
                print("# Warning: Skipping line {} due to empty Mark value: '{}'".format(i + 2, line))
                skipped_input_parse_error += 1
                continue
            try:
                height_mm = float(height_str)
                target_heights_mm[mark] = height_mm # Store mm value temporarily if needed
                # Convert target height to internal units (feet)
                internal_height = UnitUtils.ConvertToInternalUnits(height_mm, UnitTypeId.Millimeters)
                if mark in target_heights_internal:
                     print("# Warning: Duplicate Mark value '{}' found in input. Using the last value ({}mm).".format(mark, height_mm))
                target_heights_internal[mark] = internal_height
            except ValueError:
                 print("# Warning: Skipping line {} due to invalid height value '{}': '{}'".format(i + 2, height_str, line))
                 skipped_input_parse_error += 1
            except SystemException as conv_e:
                 print("# Error converting height {}mm for mark {}: {}".format(height_mm, mark, conv_e))
                 error_count += 1
        else:
            print("# Warning: Skipping malformed line {}: '{}'".format(i + 2, line))
            skipped_input_parse_error += 1
else:
    print("# Error: Input data string does not contain valid data rows.")
    # Stop processing if no valid data to use
    target_heights_internal = None # Flag that we cannot proceed

# --- Step 2: Convert Threshold Height ---
if target_heights_internal is not None: # Proceed only if parsing was somewhat successful
    try:
        threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
    except SystemException as thresh_conv_e:
        print("# Error converting threshold {}mm to internal units: {}".format(threshold_mm, thresh_conv_e))
        error_count += 1
        threshold_internal = None # Prevent proceeding

# --- Step 3: Collect Windows and Update ---
if target_heights_internal is not None and threshold_internal is not None and target_heights_internal.Count > 0:
    window_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()
    windows_processed_count = 0

    for window in window_collector:
        windows_processed_count += 1
        if not isinstance(window, FamilyInstance):
            continue # Should not happen with this filter, but good practice

        try:
            # Get the Mark parameter
            mark_param = window.get_Parameter(mark_bip)
            if mark_param is None or not mark_param.HasValue:
                skipped_no_mark_param += 1
                continue

            window_mark = mark_param.AsString()
            if window_mark is None or not window_mark: # Check for empty Mark value
                 skipped_no_mark_param += 1
                 continue

            # Check if this window's mark is in our target list
            if window_mark in target_heights_internal:
                # Get the Sill Height parameter
                sill_height_param = window.get_Parameter(sill_height_bip)

                if sill_height_param is None:
                    skipped_no_sill_param += 1
                    # print("# Info: Window Mark '{}' (ID {}) has no 'Sill Height' parameter.".format(window_mark, window.Id)) # Debug
                    continue

                if not sill_height_param.HasValue:
                    # Treat no value as being below the threshold (effectively 0)
                    current_sill_height_internal = 0.0
                else:
                    # Get current sill height only if it has a value
                    current_sill_height_internal = sill_height_param.AsDouble()

                # Check if current sill height is below the threshold
                if current_sill_height_internal < threshold_internal:
                    if sill_height_param.IsReadOnly:
                        skipped_sill_read_only += 1
                        # print("# Info: Sill Height for Window Mark '{}' (ID {}) is read-only.".format(window_mark, window.Id)) # Debug
                        continue

                    # Get the target height from our dictionary
                    target_height_internal = target_heights_internal[window_mark]

                    # Set the new value
                    set_result = sill_height_param.Set(target_height_internal)
                    if set_result:
                        updated_count += 1
                        # print("# Updated Sill Height for Window Mark '{}' (ID {}) to {}mm".format(window_mark, window.Id, target_heights_mm[window_mark])) # Debug
                    else:
                        error_count += 1
                        print("# Error: Failed to set Sill Height for Window Mark '{}' (ID {}) to {}mm. Parameter.Set returned False.".format(window_mark, window.Id, target_heights_mm[window_mark]))
                else:
                    # Sill height is already above or equal to the threshold
                    skipped_above_threshold += 1
                    # print("# Info: Skipping Window Mark '{}' (ID {}). Current Sill Height ({:.1f}mm) is >= threshold ({}mm).".format(window_mark, window.Id, UnitUtils.ConvertFromInternalUnits(current_sill_height_internal, UnitTypeId.Millimeters), threshold_mm)) # Debug

            else:
                # This window's mark was not in the input data list
                skipped_mark_not_found += 1

        except SystemException as proc_ex:
            error_count += 1
            window_id_str = "Unknown ID"
            try:
                 window_id_str = window.Id.ToString() # Try to get ID for error message
            except:
                 pass
            print("# Error processing Window ID {}: {}".format(window_id_str, proc_ex))

    # --- Final Summary ---
    print("# --- Window Sill Height Update Summary ---")
    print("# Target Marks Parsed: {}".format(target_heights_internal.Count))
    print("# Threshold for Update: < {}mm ({:.4f} ft)".format(threshold_mm, threshold_internal if threshold_internal is not None else float('nan')))
    print("# Windows Checked: {}".format(windows_processed_count))
    print("# Successfully Updated: {}".format(updated_count))
    print("# Skipped (Mark not in input list): {}".format(skipped_mark_not_found))
    print("# Skipped (Current Sill Height >= Threshold): {}".format(skipped_above_threshold))
    print("# Skipped (Window has no Mark value): {}".format(skipped_no_mark_param))
    print("# Skipped (Window has no Sill Height param): {}".format(skipped_no_sill_param))
    print("# Skipped (Sill Height param read-only): {}".format(skipped_sill_read_only))
    print("# Skipped (Input data parsing issues): {}".format(skipped_input_parse_error))
    print("# Errors Encountered: {}".format(error_count))
    if error_count > 0:
        print("# Review errors printed above for details.")

elif target_heights_internal is None:
    print("# Script aborted due to errors during input data parsing or threshold conversion.")
elif target_heights_internal.Count == 0:
     print("# Script finished. No valid Mark/Height pairs found in the input data.")
else:
    # This case should only happen if threshold conversion failed but parsing succeeded
    print("# Script aborted due to error converting threshold value.")