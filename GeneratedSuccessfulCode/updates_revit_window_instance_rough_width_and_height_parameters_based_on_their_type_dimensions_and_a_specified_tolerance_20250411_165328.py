# Purpose: This script updates Revit window instance rough width and height parameters based on their type dimensions and a specified tolerance.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String operations and Exception handling
from System import Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    FamilySymbol,
    ElementType,
    Parameter,
    BuiltInParameter,
    StorageType,
    UnitUtils,
    ElementId
)

# Attempt to import unit types - handle potential errors gracefully
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
TOLERANCE_MM = 20.0

# Built-in parameters for type dimensions
TYPE_WIDTH_BIP = BuiltInParameter.WINDOW_WIDTH
TYPE_HEIGHT_BIP = BuiltInParameter.WINDOW_HEIGHT

# Built-in parameters for instance rough dimensions
INSTANCE_ROUGH_WIDTH_BIP = BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM
INSTANCE_ROUGH_HEIGHT_BIP = BuiltInParameter.FAMILY_ROUGH_HEIGHT_PARAM

# --- Convert Tolerance to Internal Units (Feet) ---
tolerance_internal = None
conversion_success = False

# Try Revit 2021+ UnitTypeId method first
if UnitTypeId and not conversion_success:
    try:
        if UnitTypeId.Millimeters: # Check if the specific unit exists
             tolerance_internal = UnitUtils.ConvertToInternalUnits(TOLERANCE_MM, UnitTypeId.Millimeters)
             conversion_success = True
    except Exception as utid_e:
        # print("# Debug: UnitTypeId conversion failed: {{}}".format(utid_e)) # Optional debug
        pass # Continue to next fallback

# Fallback for older API versions (pre-2021) using DisplayUnitType
if DisplayUnitType and not conversion_success:
    try:
        tolerance_internal = UnitUtils.ConvertToInternalUnits(TOLERANCE_MM, DisplayUnitType.DUT_MILLIMETERS)
        conversion_success = True
    except Exception as dut_e:
        print("# Error: Failed converting tolerance units using DisplayUnitType: {{}}".format(dut_e))

if not conversion_success or tolerance_internal is None:
    print("# Error: Could not convert tolerance ({{}} mm) to internal units. Aborting.".format(TOLERANCE_MM))
else:
    # --- Initialization ---
    updated_count = 0
    skipped_no_type = 0
    skipped_no_type_dims = 0
    skipped_no_inst_params = 0
    skipped_inst_params_readonly = 0
    skipped_inst_params_wrong_type = 0
    error_count = 0
    processed_count = 0

    # --- Step 1: Collect Window Instances ---
    try:
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()
        window_instances = list(collector)
        processed_count = len(window_instances)

        # --- Step 2: Iterate and Update ---
        for window_inst in window_instances:
            if not isinstance(window_inst, FamilyInstance):
                # Should not happen with the collector, but good practice
                continue

            inst_id = window_inst.Id
            inst_name_info = "ID: {}".format(inst_id) # Default info
            try:
                inst_name_info = "'{}' (ID: {})".format(Element.Name.GetValue(window_inst), inst_id)
            except:
                pass # Keep default ID info if name access fails

            try:
                # --- Get Window Type (FamilySymbol) ---
                window_type_id = window_inst.GetTypeId()
                if window_type_id == ElementId.InvalidElementId:
                    skipped_no_type += 1
                    # print("# Info: Window Instance {} has no type. Skipping.".format(inst_name_info)) # Debug
                    continue

                window_type = doc.GetElement(window_type_id)
                if not isinstance(window_type, FamilySymbol):
                    skipped_no_type += 1 # Count as unable to get a usable type
                    # print("# Info: Could not retrieve a valid FamilySymbol for Window Instance {}. Skipping.".format(inst_name_info)) # Debug
                    continue

                type_name_info = "'{}' (ID: {})".format(Element.Name.GetValue(window_type), window_type.Id)

                # --- Get Type Dimensions ---
                type_width_param = window_type.get_Parameter(TYPE_WIDTH_BIP)
                type_height_param = window_type.get_Parameter(TYPE_HEIGHT_BIP)

                if not type_width_param or type_width_param.StorageType != StorageType.Double or \
                   not type_height_param or type_height_param.StorageType != StorageType.Double:
                    skipped_no_type_dims += 1
                    # print("# Info: Window Type {} is missing Width/Height parameters or they are not Double type. Skipping instance {}.".format(type_name_info, inst_name_info)) # Debug
                    continue

                type_width = type_width_param.AsDouble()
                type_height = type_height_param.AsDouble()

                # --- Calculate Rough Dimensions ---
                rough_width = type_width + tolerance_internal
                rough_height = type_height + tolerance_internal

                # --- Get Instance Rough Dimension Parameters ---
                inst_rough_width_param = window_inst.get_Parameter(INSTANCE_ROUGH_WIDTH_BIP)
                inst_rough_height_param = window_inst.get_Parameter(INSTANCE_ROUGH_HEIGHT_BIP)

                # Check existence
                if not inst_rough_width_param or not inst_rough_height_param:
                    skipped_no_inst_params += 1
                    # print("# Info: Window Instance {} is missing Rough Width/Height parameters. Skipping.".format(inst_name_info)) # Debug
                    continue

                # Check writability
                if inst_rough_width_param.IsReadOnly or inst_rough_height_param.IsReadOnly:
                    skipped_inst_params_readonly += 1
                    # print("# Info: Rough Width/Height parameters on Window Instance {} are read-only. Skipping.".format(inst_name_info)) # Debug
                    continue

                # Check storage type
                if inst_rough_width_param.StorageType != StorageType.Double or \
                   inst_rough_height_param.StorageType != StorageType.Double:
                    skipped_inst_params_wrong_type += 1
                    # print("# Info: Rough Width/Height parameters on Window Instance {} are not Double type. Skipping.".format(inst_name_info)) # Debug
                    continue

                # --- Set Instance Parameters ---
                update_width_success = False
                update_height_success = False
                try:
                    update_width_success = inst_rough_width_param.Set(rough_width)
                    update_height_success = inst_rough_height_param.Set(rough_height)

                    if update_width_success and update_height_success:
                        updated_count += 1
                        # print("# Updated Rough Width/Height for Window Instance {}.".format(inst_name_info)) # Debug
                    else:
                        # If one failed, log it as an error, even if the other succeeded
                        error_count += 1
                        print("# Error: Failed to set one or both Rough dimensions for Window Instance {}. Width success: {}, Height success: {}.".format(inst_name_info, update_width_success, update_height_success))

                except SystemException as set_ex:
                    error_count += 1
                    print("# Error setting parameters for Window Instance {}: {}".format(inst_name_info, set_ex.Message))

            except SystemException as loop_ex:
                error_count += 1
                print("# Error processing Window Instance {}: {}".format(inst_name_info, loop_ex.Message))

    except SystemException as col_ex:
        # Error during the collection phase
        print("# Error collecting Window Instances: {}".format(col_ex.Message))
        error_count += 1

    # --- Final Summary --- (Optional: uncomment if needed for debugging)
    # print("# --- Window Instance Rough Dimension Update Summary ---")
    # print("# Tolerance applied: {{}} mm ({{}} ft)".format(TOLERANCE_MM, tolerance_internal))
    # print("# Total Window Instances processed/attempted: {{}}".format(processed_count))
    # print("# Successfully Updated: {{}}".format(updated_count))
    # print("# Skipped (No Type/Invalid Type): {{}}".format(skipped_no_type))
    # print("# Skipped (Type Missing Dims): {{}}".format(skipped_no_type_dims))
    # print("# Skipped (Instance Missing Params): {{}}".format(skipped_no_inst_params))
    # print("# Skipped (Instance Params Read-Only): {{}}".format(skipped_inst_params_readonly))
    # print("# Skipped (Instance Params Wrong Type): {{}}".format(skipped_inst_params_wrong_type))
    # print("# Errors Encountered: {{}}".format(error_count))
    # if error_count > 0:
    #     print("# Review errors printed above for details.")