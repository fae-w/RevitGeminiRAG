# Purpose: This script updates the unconnected height of walls in Revit based on a specified level and height.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException

# Import DB classes and the DB namespace itself
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    Level,
    Wall,
    BuiltInParameter,
    Parameter,
    UnitUtils,
)

# Attempt to import newer unit classes, handle fallback
try:
    from Autodesk.Revit.DB import ForgeTypeId
    from Autodesk.Revit.DB import UnitTypeId
    use_forge_type_id = True
except ImportError:
    from Autodesk.Revit.DB import DisplayUnitType
    use_forge_type_id = False

# --- Configuration ---
target_level_name = "Level 1"
target_height_mm = 3000.0
param_unconnected_height = BuiltInParameter.WALL_USER_HEIGHT_PARAM
param_base_constraint = BuiltInParameter.WALL_BASE_CONSTRAINT
# Optional: Parameter for checking if wall is unconnected (WALL_HEIGHT_TYPE)
# param_top_constraint_type = BuiltInParameter.WALL_HEIGHT_TYPE

# --- Initialization ---
target_level_id = ElementId.InvalidElementId
target_height_internal = None
updated_count = 0
skipped_level_mismatch = 0
skipped_already_set = 0
skipped_param_not_found = 0
skipped_cannot_set = 0
# skipped_not_unconnected = 0 # Optional counter if checking top constraint
error_count = 0
processed_count = 0
output_messages = [] # Use a list to collect messages

# --- Step 1: Find Target Level ---
level_collector = FilteredElementCollector(doc).OfClass(Level)
found_level = False
for level in level_collector:
    if level.Name == target_level_name:
        target_level_id = level.Id
        found_level = True
        output_messages.append("# Info: Found target level '{{}}' with ID: {{}}".format(target_level_name, target_level_id))
        break

if not found_level:
    output_messages.append("# Error: Target level '{{}}' not found in the document. Cannot proceed.".format(target_level_name))

# --- Step 2: Convert Target Height to Internal Units (Feet) ---
conversion_success = False
if found_level: # Only proceed if level was found
    try:
        if use_forge_type_id:
            target_height_internal = UnitUtils.ConvertToInternalUnits(target_height_mm, UnitTypeId.Millimeters)
            conversion_success = True
            # output_messages.append("# Debug: Using UnitTypeId for conversion.") # Optional Debug
        else:
            target_height_internal = UnitUtils.ConvertToInternalUnits(target_height_mm, DisplayUnitType.DUT_MILLIMETERS)
            conversion_success = True
            # output_messages.append("# Debug: Using DisplayUnitType for conversion.") # Optional Debug
    except SystemException as conv_e:
        output_messages.append("# Error converting target height {{}}mm to internal units: {{}}".format(target_height_mm, conv_e))
    except AttributeError as attr_e:
        output_messages.append("# Error accessing unit types: {{}}. Check API version compatibility.".format(attr_e))

    if not conversion_success or target_height_internal is None:
        output_messages.append("# Error: Unit conversion failed. Cannot proceed.")
        found_level = False # Prevent proceeding if conversion fails after finding level

# --- Step 3: Collect and Process Walls ---
if found_level and conversion_success and target_height_internal is not None:
    wall_collector = FilteredElementCollector(doc).OfClass(Wall).WhereElementIsNotElementType()
    walls = list(wall_collector) # Convert iterator to list

    if not walls:
        output_messages.append("# No Wall instances found in the document.")
    else:
        # --- Iterate and Update Parameter ---
        for wall in walls:
            processed_count += 1
            wall_id_str = "ID: {}".format(wall.Id)
            try:
                # Check Base Constraint
                base_constraint_param = wall.get_Parameter(param_base_constraint)
                if base_constraint_param and base_constraint_param.AsElementId() == target_level_id:
                    # Base constraint matches, now check/set Unconnected Height

                    # --- Optional Check: Is the Wall's Top Constraint 'Unconnected'? ---
                    # top_constraint_param = wall.get_Parameter(param_top_constraint_type)
                    # if top_constraint_param and top_constraint_param.AsElementId() != ElementId.InvalidElementId:
                    #     output_messages.append("# Info: Wall {} is constrained to a level/ref plane, not 'Unconnected'. Setting 'Unconnected Height' may not affect its current geometry.".format(wall_id_str))
                    #     # skipped_not_unconnected += 1
                    #     # continue # Uncomment this 'continue' to only modify truly unconnected walls

                    # --- Modify Unconnected Height ---
                    unconnected_height_param = wall.get_Parameter(param_unconnected_height)

                    if unconnected_height_param is None:
                        # output_messages.append("# Warning: 'Unconnected Height' parameter not found for Wall {}. Skipping.".format(wall_id_str)) # Optional Warning
                        skipped_param_not_found += 1
                        continue

                    if unconnected_height_param.IsReadOnly:
                        # output_messages.append("# Warning: 'Unconnected Height' parameter is read-only for Wall {}. Skipping.".format(wall_id_str)) # Optional Warning
                        skipped_cannot_set += 1
                        continue

                    # Check if current value is already the target value
                    current_value = unconnected_height_param.AsDouble()
                    tolerance = 0.0001 # Tolerance for floating point comparison
                    if abs(current_value - target_height_internal) < tolerance:
                        # output_messages.append("# Info: Wall {} already has the target Unconnected Height. Skipping.".format(wall_id_str)) # Optional Info
                        skipped_already_set += 1
                        continue

                    # Set the value
                    try:
                        set_result = unconnected_height_param.Set(target_height_internal)
                        if set_result:
                            updated_count += 1
                            # output_messages.append("# Debug: Updated Unconnected Height for Wall {}".format(wall_id_str)) # Optional Debug
                        else:
                             # This case might be redundant if IsReadOnly check works, but good for safety
                             output_messages.append("# Warning: Failed to set 'Unconnected Height' for Wall {} (Set returned false). Skipping.".format(wall_id_str))
                             skipped_cannot_set += 1
                    except SystemException as set_ex:
                        output_messages.append("# Error setting 'Unconnected Height' for Wall {}: {}".format(wall_id_str, set_ex.Message))
                        error_count += 1

                else:
                    # Base constraint doesn't match or parameter not found
                    skipped_level_mismatch += 1

            except SystemException as ex:
                output_messages.append("# Error processing Wall {}: {}".format(wall_id_str, ex.Message))
                error_count += 1

        # --- Final Summary ---
        output_messages.append("\n# --- Wall Unconnected Height Update Summary ---")
        output_messages.append("# Target Level: '{}' (ID: {})".format(target_level_name, target_level_id if target_level_id else "Not Found"))
        output_messages.append("# Target Height: {}mm (Internal: {:.4f} ft)".format(target_height_mm, target_height_internal if target_height_internal else 0.0))
        output_messages.append("# Total Walls Found: {}".format(processed_count))
        output_messages.append("# Walls Matching Base Constraint ('{}'): {}".format(target_level_name, processed_count - skipped_level_mismatch))
        output_messages.append("# Successfully Updated: {}".format(updated_count))
        output_messages.append("# Skipped (Already Set): {}".format(skipped_already_set))
        output_messages.append("# Skipped (Incorrect Base Level): {}".format(skipped_level_mismatch))
        output_messages.append("# Skipped (Parameter Not Found): {}".format(skipped_param_not_found))
        output_messages.append("# Skipped (Cannot Set/Read-Only): {}".format(skipped_cannot_set))
        # output_messages.append("# Skipped (Top Not Unconnected): {}".format(skipped_not_unconnected)) # Optional
        output_messages.append("# Errors Encountered: {}".format(error_count))
        if error_count > 0:
            output_messages.append("# Review errors printed above for details.")

# --- Print Collected Messages ---
for msg in output_messages:
    print(msg)