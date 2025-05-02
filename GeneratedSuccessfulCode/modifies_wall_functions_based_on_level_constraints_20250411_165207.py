# Purpose: This script modifies wall functions based on level constraints.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # For StringComparison
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Level,
    Wall,
    WallType,
    WallFunction,
    ParameterValueProvider,
    LogicalAndFilter,
    FilterElementIdRule,
    FilterNumericEquals # Needed for ElementId comparison in FilterElementIdRule
)
import System # For StringComparison

# --- Configuration ---
target_base_level_name = "Level -1"
target_top_level_name = "Level 1"
new_wall_function = WallFunction.Retaining

# --- Helper Function to Find Level by Name (Simplified) ---
def find_level_by_name(doc, level_name):
    """Finds the first Level element with the specified name."""
    collector = FilteredElementCollector(doc).OfClass(Level)
    # Use FirstOrDefault with a lambda for cleaner LINQ-style filtering if available,
    # otherwise iterate for broader IronPython compatibility.
    for level in collector:
        # Case-insensitive comparison for robustness
        if level.Name.Equals(level_name, System.StringComparison.InvariantCultureIgnoreCase):
            return level.Id
    return ElementId.InvalidElementId

# --- Find Target Levels ---
base_level_id = find_level_by_name(doc, target_base_level_name)
top_level_id = find_level_by_name(doc, target_top_level_name)

# Check if levels were found
if base_level_id == ElementId.InvalidElementId:
    print("# Error: Base Level '{}' not found.".format(target_base_level_name))
elif top_level_id == ElementId.InvalidElementId:
    print("# Error: Top Level '{}' not found.".format(target_top_level_name))
else:
    # --- Filter Walls based on Constraints ---
    # Create providers for base and top constraint parameters
    base_provider = ParameterValueProvider(ElementId(BuiltInParameter.WALL_BASE_CONSTRAINT))
    top_provider = ParameterValueProvider(ElementId(BuiltInParameter.WALL_TOP_CONSTRAINT)) # Correct parameter for top level

    # Create rules comparing parameter values to the target level IDs
    comparer = FilterNumericEquals()
    base_rule = FilterElementIdRule(base_provider, comparer, base_level_id)
    top_rule = FilterElementIdRule(top_provider, comparer, top_level_id)

    # Combine rules with a logical AND
    level_constraint_filter = LogicalAndFilter(base_rule, top_rule)

    # Collect walls passing the combined filter
    wall_collector = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_Walls)\
        .WhereElementIsNotElementType()\
        .WherePasses(level_constraint_filter)

    # Ensure elements are valid Walls (some system families might sneak through filters)
    walls_to_modify = [w for w in wall_collector if isinstance(w, Wall)]


    # --- Process Matching Walls ---
    modified_count = 0
    skipped_count = 0
    error_count = 0
    # Dictionary to cache: {original_type_id: retaining_type_id}
    # Initialize retaining_type_id to InvalidElementId if not found/created yet.
    processed_types = {}

    # Note: Modifications (Duplicate, Set Parameter, Set WallTypeId) require a Transaction,
    # which is assumed to be handled by the calling C# code.

    for wall in walls_to_modify:
        try:
            original_wall_type = wall.WallType
            original_type_id = original_wall_type.Id

            # Skip if already the desired function
            if original_wall_type.Function == new_wall_function:
                skipped_count += 1
                continue

            retaining_type = None
            retaining_type_id = ElementId.InvalidElementId

            # Check cache first
            if original_type_id in processed_types:
                retaining_type_id = processed_types[original_type_id]
                if retaining_type_id != ElementId.InvalidElementId:
                    retaining_type_candidate = doc.GetElement(retaining_type_id)
                    # Verify the cached type is still valid and has the correct function
                    if isinstance(retaining_type_candidate, WallType) and retaining_type_candidate.Function == new_wall_function:
                         retaining_type = retaining_type_candidate
                    else:
                        # Cached type is invalid, reset and try finding/creating again
                        retaining_type_id = ElementId.InvalidElementId
                        processed_types[original_type_id] = retaining_type_id # Update cache
                        retaining_type = None
            else:
                 # Mark this original type as being processed, initially with no retaining type found
                 processed_types[original_type_id] = ElementId.InvalidElementId


            # If no valid retaining type found/cached yet, try to find or create one
            if not retaining_type:
                # Construct the expected name for the retaining version
                original_name = original_wall_type.Name
                possible_retaining_type_name = "{}-{}".format(original_name, new_wall_function.ToString())

                # Search for an existing WallType with the correct name and function
                existing_type_collector = FilteredElementCollector(doc).OfClass(WallType)
                existing_retaining_type = None
                for wt in existing_type_collector:
                    # Case-insensitive name check and function check
                    if wt.Name.Equals(possible_retaining_type_name, System.StringComparison.InvariantCultureIgnoreCase) and wt.Function == new_wall_function:
                        existing_retaining_type = wt
                        break # Found one

                if existing_retaining_type:
                    retaining_type = existing_retaining_type
                    retaining_type_id = retaining_type.Id
                    # print("# Found existing WallType '{}' (ID: {})".format(retaining_type.Name, retaining_type.Id)) # Debug
                    processed_types[original_type_id] = retaining_type_id # Update cache
                else:
                    # If not found, create a new one by duplicating
                    try:
                        # Ensure unique name for the new type
                        new_type_name = possible_retaining_type_name
                        name_counter = 1
                        while FilteredElementCollector(doc).OfClass(WallType).Where(lambda wt: wt.Name.Equals(new_type_name, System.StringComparison.InvariantCultureIgnoreCase)).Any():
                           new_type_name = "{}_{}".format(possible_retaining_type_name, name_counter)
                           name_counter += 1
                           if name_counter > 100: # Safety break
                               raise Exception("Could not generate unique name for base '{}' after 100 attempts.".format(possible_retaining_type_name))

                        # --- Modification Start --- (Requires Transaction)
                        new_wall_type = original_wall_type.Duplicate(new_type_name)
                        if isinstance(new_wall_type, WallType):
                            # Set the function parameter on the new type
                            func_param = new_wall_type.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
                            if func_param and not func_param.IsReadOnly:
                                func_param.Set(int(new_wall_function)) # Cast enum to int
                                retaining_type = new_wall_type
                                retaining_type_id = retaining_type.Id
                                # print("# Created new WallType '{}' (ID: {})".format(retaining_type.Name, retaining_type.Id)) # Debug
                                processed_types[original_type_id] = retaining_type_id # Update cache
                            else:
                                # Clean up the partially created type if possible? Difficult without transaction control here.
                                # Log the error and mark as failed.
                                raise Exception("Could not get or set Function parameter for new type '{}'.".format(new_wall_type.Name))
                        else:
                             raise Exception("Duplication of '{}' did not return a WallType.".format(original_name))
                        # --- Modification End ---

                    except Exception as creation_ex:
                        print("# Error creating retaining type for original Wall Type '{}' (ID: {}): {}".format(original_wall_type.Name, original_type_id, creation_ex))
                        error_count += 1
                        # Ensure cache reflects failure for this original type ID
                        processed_types[original_type_id] = ElementId.InvalidElementId
                        continue # Skip assigning type to this wall instance

            # Assign the new/found retaining type to the wall instance
            if retaining_type and isinstance(retaining_type, WallType) and retaining_type_id != ElementId.InvalidElementId:
                # Double check the function just before assigning, in case it changed
                if retaining_type.Function == new_wall_function:
                    # Check if change is actually needed
                    if wall.WallTypeId != retaining_type_id:
                        try:
                            # --- Modification Start --- (Requires Transaction)
                            wall.WallTypeId = retaining_type_id # Assign by ID is safer
                            # --- Modification End ---
                            modified_count += 1
                        except Exception as assign_ex:
                            print("# Error assigning type '{}' (ID: {}) to Wall ID {}: {}".format(retaining_type.Name, retaining_type_id, wall.Id, assign_ex))
                            error_count += 1
                    else:
                        # Wall already has the correct retaining type (perhaps assigned manually or in a previous loop iteration)
                        skipped_count += 1
                else:
                    # This might happen if the found/cached type was modified externally or creation failed partially
                    print("# Error: Target retaining type '{}' (ID: {}) does not have Function = Retaining. Skipping assignment for Wall ID {}.".format(retaining_type.Name, retaining_type_id, wall.Id))
                    error_count += 1
                    # Invalidate cache if it points to this wrong type
                    if processed_types.get(original_type_id) == retaining_type_id:
                         processed_types[original_type_id] = ElementId.InvalidElementId

            elif original_type_id in processed_types and processed_types[original_type_id] == ElementId.InvalidElementId:
                 # This case means finding/creating the type failed previously for this original_type_id
                 # Error was already counted during the failed step. No action needed here.
                 # print("# Info: Skipping Wall ID {} as obtaining retaining type failed previously.".format(wall.Id)) # Optional Debug
                 pass
            else:
                # Should not happen if logic is correct, but catch potential errors
                 print("# Error: Failed to obtain a valid retaining WallType for Wall ID {}. Original Type: '{}' (ID: {}). State unexpected.".format(wall.Id, original_wall_type.Name, original_type_id))
                 error_count += 1


        except Exception as ex:
            print("# Error processing Wall ID {}: {}".format(wall.Id, ex))
            error_count += 1
            # Ensure the loop continues processing other walls
            continue

    # --- Summary Output ---
    print("--- Wall Function Update Summary ---")
    print("Base Level: '{}' (ID: {})".format(target_base_level_name, base_level_id))
    print("Top Level: '{}' (ID: {})".format(target_top_level_name, top_level_id))
    print("Initial Walls Matching Constraints: {}".format(len(walls_to_modify)))
    print("Walls Changed to Retaining Type: {}".format(modified_count))
    print("Walls Skipped (Already Retaining/Correct Type): {}".format(skipped_count))
    # Calculate how many unique types were successfully created or found
    valid_retaining_types_count = len([tid for tid in processed_types.values() if tid != ElementId.InvalidElementId])
    print("Unique Retaining Types Created/Found: {}".format(valid_retaining_types_count))
    print("Errors Encountered: {}".format(error_count))