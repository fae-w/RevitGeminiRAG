# Purpose: This script updates the sill height parameter of windows on a specified level.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Level,
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
target_level_name = "Level 1"
target_value_mm = 900.0
# BuiltInParameter for 'Sill Height' on window instances
target_parameter_bip = BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM

# --- Initialization ---
target_level_id = ElementId.InvalidElementId
updated_count = 0
skipped_level_mismatch = 0
skipped_not_instance = 0
skipped_no_param = 0
skipped_read_only = 0
error_count = 0
target_value_internal = None

# --- Step 1: Find Target Level ---
level_collector = FilteredElementCollector(doc).OfClass(Level)
target_level = None
for level in level_collector:
    if level.Name == target_level_name:
        target_level = level
        target_level_id = level.Id
        break

if target_level_id == ElementId.InvalidElementId:
    print("# Error: Level named '{}' not found in the document.".format(target_level_name))
    # No further action possible if level not found
else:
    # --- Step 2: Convert Target Value to Internal Units (Feet) ---
    try:
        # Use ForgeTypeId (Revit 2021+ API) for unit conversion
        target_value_internal = UnitUtils.ConvertToInternalUnits(target_value_mm, UnitTypeId.Millimeters)
    except SystemException as conv_e:
        print("# Error converting {}mm to internal units: {}".format(target_value_mm, conv_e))
        target_value_internal = None # Prevent proceeding

    if target_value_internal is not None:
        # --- Step 3 & 4: Collect and Filter Windows ---
        # Use WhereElementIsNotElementType() to get instances
        window_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()

        # Filter windows that are hosted on the target level
        windows_on_target_level = []
        total_windows_checked = 0
        for window in window_collector:
            total_windows_checked += 1
            # Ensure it's a FamilyInstance to access LevelId reliably
            if isinstance(window, FamilyInstance):
                try:
                    # Check if the LevelId property exists and matches the target level
                    window_level_id = window.LevelId
                    if window_level_id == target_level_id:
                        windows_on_target_level.append(window)
                    else:
                        skipped_level_mismatch += 1
                except AttributeError:
                    # Some elements collected might not have LevelId, treat as mismatch
                    skipped_level_mismatch += 1
                except SystemException as e_level:
                    # Handle other errors checking level
                    error_count += 1
                    print("# Error checking level for element ID {}: {}".format(window.Id, e_level))
                    skipped_level_mismatch += 1 # Treat as mismatch if level check fails
            else:
                # If somehow a non-FamilyInstance gets through the filter
                skipped_not_instance += 1
                skipped_level_mismatch += 1 # Also count as level mismatch for simplicity

        # --- Step 5: Update Sill Height Parameter ---
        if not windows_on_target_level:
            print("# Info: No windows found on level '{}'.".format(target_level_name))
        else:
            for window in windows_on_target_level:
                try:
                    sill_height_param = window.get_Parameter(target_parameter_bip)

                    if sill_height_param is None:
                        skipped_no_param += 1
                        # print("# Info: Window ID {} does not have parameter 'Sill Height'. Skipping.".format(window.Id)) # Debug
                        continue

                    if sill_height_param.IsReadOnly:
                        skipped_read_only += 1
                        # print("# Info: Parameter 'Sill Height' for Window ID {} is read-only. Skipping.".format(window.Id)) # Debug
                        continue

                    # Set the new value for the Sill Height parameter
                    set_result = sill_height_param.Set(target_value_internal)

                    if set_result:
                        updated_count += 1
                        # print("# Updated Sill Height for Window ID {} to {}mm".format(window.Id, target_value_mm)) # Debug
                    else:
                        # This case might happen if the value is disallowed for some reason
                        error_count += 1
                        print("# Error: Failed to set Sill Height for Window ID {} to {}mm (Internal: {}). Parameter.Set returned False.".format(window.Id, target_value_mm, target_value_internal))

                except SystemException as param_ex:
                    error_count += 1
                    print("# Error processing Window ID {}: {}".format(window.Id, param_ex.Message))

            # --- Final Summary ---
            print("# --- Window Sill Height Update Summary ---")
            print("# Target Level: '{}' (ID: {})".format(target_level_name, target_level_id))
            print("# Target Sill Height: {}mm (Internal: {:.4f} ft)".format(target_value_mm, target_value_internal))
            # print("# Total Windows Checked: {}".format(total_windows_checked)) # Optional detail
            print("# Windows Found on Level: {}".format(len(windows_on_target_level)))
            print("# Successfully Updated: {}".format(updated_count))
            print("# Skipped (Not on Target Level): {}".format(skipped_level_mismatch))
            # print("# Skipped (Not FamilyInstance): {}".format(skipped_not_instance)) # Optional detail
            print("# Skipped (No Sill Height Param): {}".format(skipped_no_param))
            print("# Skipped (Param Read-Only): {}".format(skipped_read_only))
            print("# Errors Encountered: {}".format(error_count))
            if error_count > 0:
                print("# Review errors printed above for details.")

    else:
         # Error message already printed during unit conversion
         pass

# Ensure output for level not found case is printed if applicable (handled by the initial if/else)