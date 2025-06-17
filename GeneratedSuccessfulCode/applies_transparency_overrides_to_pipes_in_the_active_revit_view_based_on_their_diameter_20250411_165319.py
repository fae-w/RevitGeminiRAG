# Purpose: This script applies transparency overrides to pipes in the active Revit view based on their diameter.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    OverrideGraphicSettings,
    View,
    Parameter,
    StorageType,
    UnitUtils,
    BuiltInParameter,
    Element
)

# Attempt to import unit types - handle potential errors gracefully
try:
    # Revit 2021+ preferred method
    from Autodesk.Revit.DB import ForgeTypeId
except ImportError:
    ForgeTypeId = None # Flag that it's not available

try:
    # Revit 2021+ alternative/common method
    from Autodesk.Revit.DB import UnitTypeId
except ImportError:
    UnitTypeId = None # Flag that it's not available

try:
    # Pre-Revit 2021 method
    from Autodesk.Revit.DB import DisplayUnitType
except ImportError:
    DisplayUnitType = None # Flag that it's not available

# --- Configuration ---
threshold_mm = 300.0
transparency_level = 50 # Percentage (0-100)
diameter_param_bip = BuiltInParameter.RBS_PIPE_DIAMETER_PARAM
# Fallback parameter name if BIP doesn't work or isn't the one needed
diameter_param_name = "Diameter"

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined and available
active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View):
    print("# Error: No active valid view found or accessible.")
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: Graphics Overrides are not allowed in the active view '{}'.".format(active_view.Name))
else:
    # --- Convert Threshold to Internal Units (Feet) ---
    threshold_internal = None
    conversion_success = False

    # Try Revit 2021+ ForgeTypeId method first
    if ForgeTypeId and not conversion_success:
        try:
            millimeters_type_id = ForgeTypeId("autodesk.unit.unit:millimeters-1.0.1")
            if UnitUtils.IsValidUnit(millimeters_type_id):
                 threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, millimeters_type_id)
                 conversion_success = True
            else:
                 # Try the direct UnitTypeId property if ForgeTypeId lookup failed or wasn't valid
                 if UnitTypeId and UnitTypeId.Millimeters:
                     try:
                         threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
                         conversion_success = True
                     except: pass # Continue to next fallback
        except: pass # Continue to next fallback

    # Fallback to UnitTypeId if ForgeTypeId failed or wasn't available
    if UnitTypeId and not conversion_success:
        try:
            threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
            conversion_success = True
        except: pass # Continue to next fallback

    # Fallback for older API versions (pre-2021) using DisplayUnitType
    if DisplayUnitType and not conversion_success:
        try:
            threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
            conversion_success = True
        except Exception as dut_e:
            print("# Error: Failed converting threshold units using DisplayUnitType: {}".format(dut_e))

    if not conversion_success or threshold_internal is None:
        print("# Error: Could not determine internal units for threshold. Cannot proceed.")
    else:
        # --- Collect Pipes in Active View ---
        collector = FilteredElementCollector(doc, active_view.Id)\
                    .OfCategory(BuiltInCategory.OST_PipeCurves)\
                    .WhereElementIsNotElementType()

        pipes_to_modify = List[ElementId]()
        processed_count = 0
        matched_count = 0

        for pipe in collector:
            processed_count += 1
            diameter_value = None
            param_found = False

            # 1. Try getting the BuiltInParameter first
            try:
                param = pipe.get_Parameter(diameter_param_bip)
                if param and param.HasValue and param.StorageType == StorageType.Double:
                    diameter_value = param.AsDouble()
                    param_found = True
            except Exception as e_bip:
                # print("# Debug: Error getting BIP diameter for {}: {}".format(pipe.Id, e_bip))
                pass # Continue to try by name

            # 2. If BIP failed or wasn't found, try finding by name
            if not param_found:
                try:
                    # Iterate through parameters to find by name (case-sensitive)
                    # For case-insensitive, use .lower() comparison
                    for p in pipe.Parameters:
                        if p.Definition.Name == diameter_param_name:
                            if p.HasValue and p.StorageType == StorageType.Double:
                                diameter_value = p.AsDouble()
                                param_found = True
                                break # Found the parameter
                except Exception as e_name:
                    # print("# Debug: Error searching for parameter '{}' on {}: {}".format(diameter_param_name, pipe.Id, e_name))
                    pass # Parameter likely doesn't exist or error occurred

            # Check if a valid diameter was found and meets the criteria
            if param_found and diameter_value is not None:
                try:
                    if diameter_value > threshold_internal:
                        pipes_to_modify.Add(pipe.Id)
                        matched_count += 1
                except Exception as e_comp:
                     print("# Error comparing diameter for pipe ID {}: {}".format(pipe.Id, e_comp))
            # elif not param_found:
                # print("# Debug: Diameter parameter not found for pipe ID {}".format(pipe.Id)) # Optional: log pipes missing the param

        # --- Define Override Settings ---
        ogs = OverrideGraphicSettings()
        try:
            ogs.SetSurfaceTransparency(transparency_level) # Range 0-100
            # print("# Debug: Override Settings created with {}% transparency.".format(transparency_level)) # Optional Debug
        except Exception as e_ogs:
             print("# Error setting transparency in OverrideGraphicSettings: {}. Value was: {}".format(e_ogs, transparency_level))
             ogs = None # Invalidate ogs if setting failed

        # --- Apply Overrides ---
        if ogs and pipes_to_modify.Count > 0:
            applied_count = 0
            error_count = 0
            # Transaction is handled externally by the caller
            for pipe_id in pipes_to_modify:
                try:
                    active_view.SetElementOverrides(pipe_id, ogs)
                    applied_count += 1
                except Exception as e_apply:
                    # print("# Warning: Could not apply overrides to element {}: {}".format(pipe_id, e_apply)) # Optional Debug
                    error_count += 1

            print("# Processed {} pipes in view '{}'.".format(processed_count, active_view.Name))
            print("# Found {} pipes with diameter > {}mm.".format(matched_count, threshold_mm))
            if applied_count > 0:
                 print("# Successfully applied {}% transparency override to {} pipes.".format(transparency_level, applied_count))
            if error_count > 0:
                 print("# Failed to apply overrides to {} pipes.".format(error_count))

        elif ogs is None:
            print("# Cannot apply overrides because OverrideGraphicSettings could not be configured.")
        elif pipes_to_modify.Count == 0:
            print("# Processed {} pipes in view '{}'. No pipes found with diameter > {}mm.".format(processed_count, active_view.Name, threshold_mm))
        else:
            # Should not happen if ogs is valid and pipes_to_modify has items, but included for completeness
            print("# No overrides applied.")