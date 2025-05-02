# Purpose: This script changes a Revit wall's WallType to one with a specified WallFunction, creating a new WallType if necessary.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # For StringComparison
from Autodesk.Revit.DB import (
    ElementId,
    Wall,
    WallType,
    WallFunction,
    FilteredElementCollector,
    BuiltInParameter
)
import System # For StringComparison

# --- Configuration ---
target_wall_id_int = 67890
target_function = WallFunction.Retaining

# --- Get the Wall Element ---
target_wall_id = ElementId(target_wall_id_int)
wall_element = doc.GetElement(target_wall_id)

# --- Validate the Element ---
if wall_element is None:
    print("# Error: Wall with Element ID {} not found.".format(target_wall_id_int))
elif not isinstance(wall_element, Wall):
    print("# Error: Element with ID {} is not a Wall. It is a '{}'.".format(target_wall_id_int, wall_element.GetType().Name))
else:
    # --- Process the Wall ---
    try:
        original_wall_type = wall_element.WallType
        original_type_id = original_wall_type.Id

        # Check if the current type already has the desired function
        if original_wall_type.Function == target_function:
            print("# Info: Wall ID {} already uses a WallType ('{}') with Function = {}.".format(target_wall_id_int, original_wall_type.Name, target_function.ToString()))
        else:
            # --- Find or Create a Suitable WallType ---
            target_type = None
            target_type_id = ElementId.InvalidElementId

            # Construct the expected name for the target type
            original_name = original_wall_type.Name
            # Use a consistent naming convention, e.g., "[Original Name]-[Function]"
            target_type_name_base = "{}-{}".format(original_name, target_function.ToString())

            # Search for an existing WallType with the correct base name and function
            existing_type_collector = FilteredElementCollector(doc).OfClass(WallType)
            found_existing_type = None
            for wt in existing_type_collector:
                # Case-insensitive name check (match base name) and function check
                if wt.Name.Equals(target_type_name_base, System.StringComparison.InvariantCultureIgnoreCase) and wt.Function == target_function:
                    found_existing_type = wt
                    break # Found a suitable existing type

            if found_existing_type:
                target_type = found_existing_type
                target_type_id = target_type.Id
                print("# Info: Found existing WallType '{}' (ID: {}) with desired function.".format(target_type.Name, target_type_id))
            else:
                # If not found, create a new one by duplicating
                try:
                    # Ensure unique name for the new type
                    new_type_name = target_type_name_base
                    name_counter = 1
                    # Check if the base name itself is unique before adding counters
                    while FilteredElementCollector(doc).OfClass(WallType).Where(lambda wt: wt.Name.Equals(new_type_name, System.StringComparison.InvariantCultureIgnoreCase)).Any():
                       new_type_name = "{}_{}".format(target_type_name_base, name_counter)
                       name_counter += 1
                       if name_counter > 100: # Safety break
                           raise Exception("Could not generate unique name for base '{}' after 100 attempts.".format(target_type_name_base))

                    # --- Modification Start (Requires Transaction - handled externally) ---
                    new_wall_type = original_wall_type.Duplicate(new_type_name)
                    if isinstance(new_wall_type, WallType):
                        # Set the function parameter on the new type
                        func_param = new_wall_type.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
                        if func_param and not func_param.IsReadOnly:
                            # Set parameter using the integer value of the enum
                            param_set_success = func_param.Set(int(target_function))
                            if param_set_success:
                                target_type = new_wall_type
                                target_type_id = target_type.Id
                                print("# Info: Created new WallType '{}' (ID: {}) with Function = {}.".format(target_type.Name, target_type_id, target_function.ToString()))
                            else:
                                # Clean up the partially created type if possible? Difficult without transaction control here.
                                # Log the error and mark as failed.
                                raise Exception("Failed to set Function parameter for new type '{}'.".format(new_wall_type.Name))
                        else:
                            raise Exception("Could not get or set Function parameter (read-only or missing) for new type '{}'.".format(new_wall_type.Name))
                    else:
                         raise Exception("Duplication of '{}' did not return a WallType.".format(original_name))
                    # --- Modification End ---

                except Exception as creation_ex:
                    print("# Error creating target type for original Wall Type '{}' (ID: {}): {}".format(original_wall_type.Name, original_type_id, creation_ex))
                    # Ensure target_type remains None if creation failed

            # --- Assign the New/Found Type to the Wall Instance ---
            if target_type and isinstance(target_type, WallType) and target_type_id != ElementId.InvalidElementId:
                # Double check the function just before assigning
                if target_type.Function == target_function:
                     # Check if change is actually needed (might have been set manually between checks)
                     if wall_element.WallTypeId != target_type_id:
                         try:
                             # --- Modification Start (Requires Transaction - handled externally) ---
                             wall_element.WallTypeId = target_type_id # Assign by ID is safer
                             # --- Modification End ---
                             print("# Success: Changed Wall ID {} to WallType '{}' (ID: {}) with Function = {}.".format(target_wall_id_int, target_type.Name, target_type_id, target_function.ToString()))
                         except Exception as assign_ex:
                             print("# Error assigning type '{}' (ID: {}) to Wall ID {}: {}".format(target_type.Name, target_type_id, target_wall_id_int, assign_ex))
                     else:
                         # Wall already has the correct target type (perhaps assigned manually or race condition)
                         print("# Info: Wall ID {} already has the target WallType '{}'.".format(target_wall_id_int, target_type.Name))
                else:
                     # This might happen if the found/created type was modified externally or creation failed partially
                     print("# Error: Target type '{}' (ID: {}) does not have Function = {}. Assignment skipped for Wall ID {}.".format(target_type.Name, target_type_id, target_function.ToString(), target_wall_id_int))
            elif not target_type:
                 # This case means finding/creating the type failed previously. Error already printed.
                 print("# Error: Failed to obtain a valid target WallType. Cannot change Wall ID {}.".format(target_wall_id_int))

    except Exception as ex:
        print("# Error processing Wall ID {}: {}".format(target_wall_id_int, ex))