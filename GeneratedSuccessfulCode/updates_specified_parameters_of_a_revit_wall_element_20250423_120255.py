# Purpose: This script updates specified parameters of a Revit wall element.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often needed for UI interactions, though not directly used here, good practice
clr.AddReference('System') # For StringComparison
import Autodesk.Revit.DB # Import the main namespace
import Autodesk.Revit.DB.Structure # Import the Structure namespace for StructuralWallUsage
from Autodesk.Revit.DB import (
    ElementId,
    Wall,
    WallType,
    WallFunction,
    FilteredElementCollector,
    BuiltInParameter,
    Parameter,
    StorageType
)
import System # For StringComparison

# --- Configuration ---
target_wall_id_int = 78901
# Parameter values derived from the request: 'ID=78901, Function=Interior, FireRating=60 min, StructuralUsage=Non-bearing, Comments=Check acoustic seal'
target_function = WallFunction.Interior
target_fire_rating_str = "60 min"
# Use the fully qualified name for the enum
target_structural_usage = Autodesk.Revit.DB.Structure.StructuralWallUsage.NonBearing
target_comments_str = "Check acoustic seal"

# --- Get the Wall Element ---
target_wall_id = ElementId(target_wall_id_int)
wall_element = doc.GetElement(target_wall_id)

# --- Validate the Element ---
if wall_element is None:
    print("# Error: Wall with Element ID {} not found.".format(target_wall_id_int))
elif not isinstance(wall_element, Wall):
    print("# Error: Element with ID {} is not a Wall. It is a '{}'.".format(target_wall_id_int, wall_element.GetType().Name))
else:
    print("# Processing Wall ID: {}".format(target_wall_id_int))
    success_messages = []
    error_messages = []

    # --- 1. Handle Wall Function (May require changing the WallType) ---
    try:
        original_wall_type = wall_element.WallType
        original_type_id = original_wall_type.Id

        if original_wall_type.Function == target_function:
            # Function parameter is already correct via the current type
            success_messages.append("Function: Already uses WallType ('{}') with Function = {}.".format(original_wall_type.Name, target_function.ToString()))
        else:
            # Need to find or create a suitable WallType
            target_type = None
            target_type_id = ElementId.InvalidElementId
            original_name = original_wall_type.Name
            # Define a naming convention for the potentially new type
            target_type_name_base = "{}-{}".format(original_name, target_function.ToString())

            # Search for an existing WallType with the desired name pattern and function
            existing_type_collector = FilteredElementCollector(doc).OfClass(WallType)
            found_existing_type = None
            for wt in existing_type_collector:
                # Case-insensitive name check and exact function check
                if wt.Name.Equals(target_type_name_base, System.StringComparison.InvariantCultureIgnoreCase) and wt.Function == target_function:
                    found_existing_type = wt
                    break # Found a suitable existing type

            if found_existing_type:
                target_type = found_existing_type
                target_type_id = target_type.Id
                success_messages.append("Function: Found existing WallType '{}' (ID: {}) for desired function.".format(target_type.Name, target_type_id))
            else:
                # If not found, create a new type by duplicating the original
                # NOTE: This part requires a Transaction, which is assumed to be handled externally by the C# wrapper
                try:
                    # Ensure the new type name is unique
                    new_type_name = target_type_name_base
                    name_counter = 1
                    # Use a temporary list to avoid modifying collection while iterating implicitly
                    existing_names = [wt.Name for wt in FilteredElementCollector(doc).OfClass(WallType)]
                    while any(name.Equals(new_type_name, System.StringComparison.InvariantCultureIgnoreCase) for name in existing_names):
                       new_type_name = "{}_{}".format(target_type_name_base, name_counter)
                       name_counter += 1
                       if name_counter > 100: # Safety break to prevent infinite loops
                           raise Exception("Could not generate unique name for base '{}' after 100 attempts.".format(target_type_name_base))

                    # --- Modification Start (Requires Transaction - handled externally) ---
                    new_wall_type = original_wall_type.Duplicate(new_type_name)
                    if isinstance(new_wall_type, WallType):
                        # Set the function parameter on the *new* type
                        func_param = new_wall_type.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
                        if func_param and not func_param.IsReadOnly:
                            # Set parameter using the integer value of the WallFunction enum
                            param_set_success = func_param.Set(int(target_function))
                            if param_set_success:
                                target_type = new_wall_type
                                target_type_id = target_type.Id
                                success_messages.append("Function: Created new WallType '{}' (ID: {}) with Function = {}.".format(target_type.Name, target_type_id, target_function.ToString()))
                            else:
                                # Attempt to clean up partially created type might be complex without transaction control here
                                raise Exception("Failed to set Function parameter for newly created type '{}'.".format(new_wall_type.Name))
                        else:
                            raise Exception("Could not get Function parameter or it was read-only for new type '{}'.".format(new_wall_type.Name))
                    else:
                         raise Exception("Duplication of WallType '{}' failed or returned unexpected type.".format(original_name))
                    # --- Modification End ---

                except Exception as creation_ex:
                    error_messages.append("Function: Error creating target WallType: {}".format(creation_ex))
                    target_type = None # Ensure type is None if creation failed

            # --- Assign the New/Found Type to the Wall Instance ---
            if target_type and isinstance(target_type, WallType) and target_type_id != ElementId.InvalidElementId:
                 # Double check the function just before assigning
                if target_type.Function == target_function:
                     # Check if change is actually needed (WallTypeId might have changed externally)
                     if wall_element.WallTypeId != target_type_id:
                         try:
                             # --- Modification Start (Requires Transaction - handled externally) ---
                             wall_element.WallTypeId = target_type_id # Assign by ID
                             # --- Modification End ---
                             success_messages.append("Function: Changed Wall instance to use WallType '{}' (ID: {}).".format(target_type.Name, target_type_id))
                         except Exception as assign_ex:
                             error_messages.append("Function: Error assigning WallType '{}' (ID: {}) to Wall instance: {}".format(target_type.Name, target_type_id, assign_ex))
                     else:
                         # Wall already has the correct target type
                         success_messages.append("Function: Wall instance already uses target WallType '{}'.".format(target_type.Name))
                else:
                     # This might happen if the found/created type was modified externally or creation failed partially
                     error_messages.append("Function: Target type '{}' (ID: {}) does not have correct Function = {}. Assignment skipped.".format(target_type.Name, target_type_id, target_function.ToString()))
            elif target_type is None and original_wall_type.Function != target_function:
                 # This path means finding/creating the type failed previously. Error already logged.
                 error_messages.append("Function: Failed to obtain a valid target WallType. Wall function not changed.")

    except Exception as func_ex:
        error_messages.append("Function: General error processing wall function change: {}".format(func_ex))

    # --- 2. Handle Fire Rating Parameter ---
    try:
        # Assuming Fire Rating is the standard BuiltInParameter
        fire_rating_param = wall_element.get_Parameter(BuiltInParameter.FIRE_RATING)
        if fire_rating_param and not fire_rating_param.IsReadOnly:
            # Check storage type - typically String for Fire Rating
            if fire_rating_param.StorageType == StorageType.String:
                current_value = fire_rating_param.AsString()
                if current_value != target_fire_rating_str:
                    # --- Modification Start (Requires Transaction - handled externally) ---
                    set_success = fire_rating_param.Set(target_fire_rating_str)
                    # --- Modification End ---
                    if set_success:
                        success_messages.append("FireRating: Set to '{}'.".format(target_fire_rating_str))
                    else:
                        error_messages.append("FireRating: Failed to set value '{}' using Set().".format(target_fire_rating_str))
                else:
                    success_messages.append("FireRating: Already set to '{}'.".format(target_fire_rating_str))
            else:
                 error_messages.append("FireRating: Parameter is not a String type (found {}). Cannot set '{}'.".format(fire_rating_param.StorageType.ToString(), target_fire_rating_str))
        elif fire_rating_param is None:
             error_messages.append("FireRating: Parameter (FIRE_RATING) not found on Wall ID {}.".format(target_wall_id_int))
        else: # Parameter exists but is read-only
             error_messages.append("FireRating: Parameter is read-only.")
    except Exception as fr_ex:
        error_messages.append("FireRating: Error setting parameter: {}".format(fr_ex))

    # --- 3. Handle Structural Usage Parameter ---
    try:
        struct_usage_param = wall_element.get_Parameter(BuiltInParameter.STRUCTURAL_USAGE_PARAM)
        if struct_usage_param and not struct_usage_param.IsReadOnly:
            # This parameter typically stores an Integer corresponding to the StructuralWallUsage enum
            if struct_usage_param.StorageType == StorageType.Integer:
                target_value_int = int(target_structural_usage)
                current_value = struct_usage_param.AsInteger()
                if current_value != target_value_int:
                    # --- Modification Start (Requires Transaction - handled externally) ---
                    set_success = struct_usage_param.Set(target_value_int)
                    # --- Modification End ---
                    if set_success:
                        success_messages.append("StructuralUsage: Set to {} (Value: {}).".format(target_structural_usage.ToString(), target_value_int))
                    else:
                        error_messages.append("StructuralUsage: Failed to set value {} using Set().".format(target_value_int))
                else:
                    success_messages.append("StructuralUsage: Already set to {} (Value: {}).".format(target_structural_usage.ToString(), target_value_int))
            else:
                error_messages.append("StructuralUsage: Parameter is not an Integer type (found {}). Cannot set enum value.".format(struct_usage_param.StorageType.ToString()))
        elif struct_usage_param is None:
             error_messages.append("StructuralUsage: Parameter (STRUCTURAL_USAGE_PARAM) not found.")
        else: # Parameter exists but is read-only
             error_messages.append("StructuralUsage: Parameter is read-only.")
    except Exception as su_ex:
        error_messages.append("StructuralUsage: Error setting parameter: {}".format(su_ex))

    # --- 4. Handle Comments Parameter ---
    try:
        comments_param = wall_element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if comments_param and not comments_param.IsReadOnly:
             # Comments parameter is typically String
             if comments_param.StorageType == StorageType.String:
                 current_value = comments_param.AsString()
                 if current_value != target_comments_str:
                    # --- Modification Start (Requires Transaction - handled externally) ---
                    set_success = comments_param.Set(target_comments_str)
                    # --- Modification End ---
                    if set_success:
                        success_messages.append("Comments: Set to '{}'.".format(target_comments_str))
                    else:
                        error_messages.append("Comments: Failed to set value '{}' using Set().".format(target_comments_str))
                 else:
                    success_messages.append("Comments: Already set to '{}'.".format(target_comments_str))
             else:
                 error_messages.append("Comments: Parameter is not a String type (found {}).".format(comments_param.StorageType.ToString()))
        elif comments_param is None:
             error_messages.append("Comments: Parameter (ALL_MODEL_INSTANCE_COMMENTS) not found.")
        else: # Parameter exists but is read-only
             error_messages.append("Comments: Parameter is read-only.")
    except Exception as cm_ex:
        error_messages.append("Comments: Error setting parameter: {}".format(cm_ex))

    # --- Final Report ---
    print("--- Update Report for Wall ID: {} ---".format(target_wall_id_int))
    if success_messages:
        print("Successful Updates/Checks:")
        for msg in success_messages:
            print("  + {}".format(msg))
    if error_messages:
        print("Errors/Warnings:")
        for msg in error_messages:
            print("  - {}".format(msg))
    if not success_messages and not error_messages:
        print("  No changes were attempted or needed based on checks.")