# Purpose: This script updates insulation thickness for exterior wall types in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallType,
    BuiltInParameter,
    Parameter,
    StorageType,
    UnitUtils,
    WallFunction
)

# Attempt to import unit types - handle potential errors gracefully
try:
    # Revit 2022+ preferred method for spec type checking
    from Autodesk.Revit.DB import ForgeTypeId
    LENGTH_SPEC_ID = ForgeTypeId('autodesk.spec.aec:length-2.0.0') # Spec for Length
except ImportError:
    ForgeTypeId = None # Flag that it's not available
    LENGTH_SPEC_ID = None

try:
    # Revit 2021+ alternative/common method for units
    from Autodesk.Revit.DB import UnitTypeId
except ImportError:
    UnitTypeId = None # Flag that it's not available

try:
    # Pre-Revit 2021 method for units
    from Autodesk.Revit.DB import DisplayUnitType
except ImportError:
    DisplayUnitType = None # Flag that it's not available

# --- Configuration ---
TARGET_THICKNESS_MM = 100.0
# WARNING: Parameter names are case-sensitive. Verify the exact name in Revit.
INSULATION_THICKNESS_PARAM_NAME = "Insulation Thickness"
FUNCTION_PARAM_BIP = BuiltInParameter.FUNCTION_PARAM
TARGET_FUNCTION = WallFunction.Exterior
ZERO_TOLERANCE = 1e-9 # Tolerance for checking if current value is zero

# --- Convert Target Thickness to Internal Units (Feet) ---
target_thickness_internal = None
conversion_success = False

# Try Revit 2021+ ForgeTypeId/UnitTypeId method first
if UnitTypeId and not conversion_success:
    try:
        if UnitTypeId.Millimeters: # Check if the specific unit exists
             target_thickness_internal = UnitUtils.ConvertToInternalUnits(TARGET_THICKNESS_MM, UnitTypeId.Millimeters)
             conversion_success = True
    except Exception as utid_e:
        # print("# Debug: UnitTypeId conversion failed: {}".format(utid_e)) # Optional debug
        pass # Continue to next fallback

# Fallback using ForgeTypeId string lookup if UnitTypeId failed or unavailable
if ForgeTypeId and not conversion_success:
    try:
        millimeters_type_id = ForgeTypeId('autodesk.unit.unit:millimeters-1.0.1')
        # Need to check validity and compatibility (may vary across Revit versions)
        # Simple approach: just try converting
        if UnitUtils.IsValidUnit(millimeters_type_id):
             target_thickness_internal = UnitUtils.ConvertToInternalUnits(TARGET_THICKNESS_MM, millimeters_type_id)
             conversion_success = True
    except Exception as forge_e:
        # print("# Debug: ForgeTypeId conversion failed: {}".format(forge_e)) # Optional debug
        pass # Continue to next fallback

# Fallback for older API versions (pre-2021) using DisplayUnitType
if DisplayUnitType and not conversion_success:
    try:
        target_thickness_internal = UnitUtils.ConvertToInternalUnits(TARGET_THICKNESS_MM, DisplayUnitType.DUT_MILLIMETERS)
        conversion_success = True
    except Exception as dut_e:
        print("# Error: Failed converting target thickness units using DisplayUnitType: {}".format(dut_e))

if not conversion_success or target_thickness_internal is None:
    print("# Error: Could not convert target thickness ({} mm) to internal units. Aborting.".format(TARGET_THICKNESS_MM))
else:
    # --- Script Core Logic ---
    collector = FilteredElementCollector(doc).OfClass(WallType)
    # Ensure we are dealing with WallType elements, not other element types
    wall_types = [wt for wt in collector.ToElements() if isinstance(wt, WallType)]

    modified_count = 0
    skipped_non_exterior = 0
    skipped_param_missing = 0
    skipped_param_not_zero = 0
    skipped_read_only = 0
    skipped_wrong_type = 0
    error_count = 0

    for wall_type in wall_types:
        try:
            # 1. Check Wall Function Parameter
            function_param = wall_type.get_Parameter(FUNCTION_PARAM_BIP)
            is_exterior = False
            if function_param and function_param.StorageType == StorageType.Integer:
                try:
                    # Attempt to cast the integer value to the WallFunction enum
                    current_function = clr.Convert(function_param.AsInteger(), WallFunction)
                    if current_function == TARGET_FUNCTION:
                        is_exterior = True
                except Exception as e_func_cast:
                    # Issue casting or getting value, assume not exterior for safety
                    # print("# Debug: Could not read/cast Function parameter for WallType '{}' (ID: {}): {}".format(wall_type.Name, wall_type.Id, e_func_cast))
                    pass

            if not is_exterior:
                skipped_non_exterior += 1
                continue

            # 2. Find the 'Insulation Thickness' parameter by name
            insulation_param = wall_type.LookupParameter(INSULATION_THICKNESS_PARAM_NAME)

            if not insulation_param:
                skipped_param_missing += 1
                # print("# Skipping WT '{}': Param '{}' not found.".format(wall_type.Name, INSULATION_THICKNESS_PARAM_NAME)) # Optional debug
                continue

            if insulation_param.IsReadOnly:
                skipped_read_only += 1
                # print("# Skipping WT '{}': Param '{}' is read-only.".format(wall_type.Name, INSULATION_THICKNESS_PARAM_NAME)) # Optional debug
                continue

            # 3. Check Parameter Type (must be Double and ideally Length)
            param_def = insulation_param.Definition
            is_suitable_type = False
            if insulation_param.StorageType == StorageType.Double:
                if ForgeTypeId and LENGTH_SPEC_ID: # Revit 2022+ check preferred
                    try:
                        param_spec = param_def.GetSpecTypeId()
                        if param_spec == LENGTH_SPEC_ID:
                            is_suitable_type = True
                    except Exception: # Fallback if GetSpecTypeId fails
                        is_suitable_type = True # Assume Double is ok if spec check fails
                else: # Older Revit (pre-ForgeTypeId for specs)
                    is_suitable_type = True # Assume Double storage is sufficient

            if not is_suitable_type:
                skipped_wrong_type += 1
                # print("# Skipping WT '{}': Param '{}' is not a Length/Double type.".format(wall_type.Name, INSULATION_THICKNESS_PARAM_NAME)) # Optional debug
                continue

            # 4. Check Current Value
            current_value = insulation_param.AsDouble()
            if abs(current_value) < ZERO_TOLERANCE:
                # 5. Set the new value (Transaction handled externally)
                try:
                    success = insulation_param.Set(target_thickness_internal)
                    if success:
                        modified_count += 1
                        # print("# Modified WT '{}'. Set '{}' to {} mm.".format(wall_type.Name, INSULATION_THICKNESS_PARAM_NAME, TARGET_THICKNESS_MM)) # Optional debug
                    else:
                        # Set returned false, indicating potential issue (though exception usually occurs)
                        error_count += 1
                        print("# Warning: Setting parameter for WT '{}' returned false.".format(wall_type.Name))
                except Exception as e_set:
                    error_count += 1
                    print("# Error setting parameter for WT '{}': {}".format(wall_type.Name, e_set))
            else:
                skipped_param_not_zero += 1
                # print("# Skipping WT '{}': Param '{}' not zero (value: {}).".format(wall_type.Name, INSULATION_THICKNESS_PARAM_NAME, current_value)) # Optional debug

        except Exception as e:
            error_count += 1
            try:
                name_for_error = wall_type.Name
            except:
                name_for_error = "ID: {}".format(wall_type.Id)
            print("# Error processing WallType '{}': {}".format(name_for_error, e))

    # --- Summary (Optional: Print to console for feedback) ---
    # print("--- Wall Type Insulation Thickness Update Summary ---")
    # print("Target Thickness: {} mm ({} ft)".format(TARGET_THICKNESS_MM, target_thickness_internal))
    # print("Successfully modified: {}".format(modified_count))
    # print("Skipped (Not Exterior Function): {}".format(skipped_non_exterior))
    # print("Skipped (Param '{}' Missing): {}".format(INSULATION_THICKNESS_PARAM_NAME, skipped_param_missing))
    # print("Skipped (Param Read-Only): {}".format(skipped_read_only))
    # print("Skipped (Param Wrong Type): {}".format(skipped_wrong_type))
    # print("Skipped (Param Value Not Zero): {}".format(skipped_param_not_zero))
    # print("Errors during processing/setting: {}".format(error_count))
    # print("Total Wall Types checked: {}".format(len(wall_types)))