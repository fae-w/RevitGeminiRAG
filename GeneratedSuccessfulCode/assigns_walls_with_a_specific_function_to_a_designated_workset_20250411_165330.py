# Purpose: This script assigns walls with a specific function to a designated workset.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
from System import Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    WorksetTable,
    BuiltInParameter,
    Workset,
    WorksetId,
    FilteredWorksetCollector,
    WorksetKind,
    Parameter, # Explicitly import Parameter
    ElementId # Required for Parameter.Set(ElementId) if needed, though Set(Int32) preferred for WorksetId
)
# Although WallFunction is an enum, comparing the integer value is often easier/more reliable
# from Autodesk.Revit.DB import WallFunction

# --- Configuration ---
target_workset_name = "Workset - Core Elements"
target_category = BuiltInCategory.OST_Walls
target_function_value = 2 # Integer value for WallFunction.CoreShaft

# --- Initialization ---
modified_count = 0
skipped_count = 0
error_count = 0
target_workset_id = -1 # Initialize with an invalid value
target_workset = None

# --- Check if worksharing is enabled ---
if not doc.IsWorkshared:
    print("# Info: Project is not workshared. Cannot assign elements to worksets.")
else:
    try:
        # --- Find the target Workset ID ---
        workset_table = doc.GetWorksetTable()
        workset_collector = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
        found_workset = None
        for ws in workset_collector:
            if ws.Name == target_workset_name:
                found_workset = ws
                break

        if found_workset:
            target_workset_id = found_workset.Id.IntegerValue # Get the integer ID for setting the parameter
            target_workset = found_workset # Keep the Workset object for reference if needed
            # print("# Found target workset '{}' with ID: {}".format(target_workset_name, target_workset_id)) # Debug
        else:
            print("# Error: Target workset '{}' not found in the document.".format(target_workset_name))
            target_workset_id = -1 # Ensure it remains invalid

        # --- Process Elements only if target workset was found ---
        if target_workset_id != -1:
            # --- Collect target elements ---
            collector = FilteredElementCollector(doc).OfCategory(target_category).WhereElementIsNotElementType()
            walls_to_process = [w for w in collector if isinstance(w, Wall)] # Ensure they are Wall objects

            # print("# Found {} Walls to check.".format(len(walls_to_process))) # Debug

            for wall in walls_to_process:
                try:
                    # --- Check the 'Function' parameter ---
                    func_param = wall.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
                    if func_param and func_param.HasValue:
                        wall_function_int = func_param.AsInteger()

                        if wall_function_int == target_function_value:
                            # --- Check and Set the 'Workset' parameter ---
                            workset_param = wall.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
                            if workset_param and not workset_param.IsReadOnly:
                                current_workset_id = workset_param.AsInteger()

                                if current_workset_id != target_workset_id:
                                    try:
                                        # Transaction is handled externally
                                        # Set the parameter using the integer value of the WorksetId
                                        workset_param.Set(target_workset_id)
                                        modified_count += 1
                                        # print("# Modified Wall ID: {}. Set Workset to '{}' (ID: {})".format(wall.Id, target_workset_name, target_workset_id)) # Debug
                                    except SystemException as set_err:
                                        error_count += 1
                                        print("# Error setting workset for Wall ID {}: {}".format(wall.Id, set_err.Message))
                                else:
                                    # Already on the correct workset
                                    skipped_count += 1
                                    # print("# Skipped Wall ID: {}. Already on workset '{}'".format(wall.Id, target_workset_name)) # Debug
                            else:
                                # Cannot get or modify the workset parameter
                                skipped_count += 1
                                # print("# Skipped Wall ID: {}. Workset parameter not found or is read-only.".format(wall.Id)) # Debug
                        else:
                            # Function does not match
                            skipped_count += 1
                            # print("# Skipped Wall ID: {}. Function does not match (Value: {}).".format(wall.Id, wall_function_int)) # Debug
                    else:
                        # Function parameter not found or has no value
                        skipped_count += 1
                        # print("# Skipped Wall ID: {}. Could not read Function parameter.".format(wall.Id)) # Debug

                except SystemException as proc_err:
                    error_count += 1
                    print("# Error processing Wall ID {}: {}".format(wall.Id, proc_err.Message))

            # --- Final Summary --- (Optional: uncomment if needed)
            # print("# --- Workset Assignment Summary ---")
            # print("# Target Workset: '{}' (ID: {})".format(target_workset_name, target_workset_id))
            # print("# Elements Modified: {}".format(modified_count))
            # print("# Elements Skipped (Wrong function, parameter issue, or already correct): {}".format(skipped_count))
            # print("# Errors during processing/setting: {}".format(error_count))
            # if error_count > 0:
            #    print("# Review errors printed above for details.")

    except SystemException as general_ex:
        print("# Error during script execution: {}".format(general_ex.Message))