# Purpose: This script updates a Revit door's 'Has Fire Rating' parameter based on the 'Fire Rating' parameter.

﻿# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    BuiltInParameter,
    Parameter,
    StorageType
)
import System # For exception handling

# --- Configuration ---
# Source parameter: Built-in 'Fire Rating'
source_param_bip = BuiltInParameter.FIRE_RATING
# Target parameter: Custom 'Has Fire Rating' (Yes/No)
target_param_name = "Has Fire Rating"

# --- Counters ---
processed_doors_count = 0
updated_doors_count = 0
skipped_no_target_param = 0
skipped_target_readonly = 0
skipped_target_wrong_type = 0
skipped_already_set = 0
error_count = 0

# --- Main Logic ---
# Collect all door instances
door_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

for door in door_collector:
    if not isinstance(door, FamilyInstance):
        continue

    processed_doors_count += 1
    door_id = door.Id

    try:
        # Get the source 'Fire Rating' parameter
        source_param = door.get_Parameter(source_param_bip)

        # Determine if source parameter has a meaningful value
        source_has_value = False
        if source_param and source_param.HasValue:
            if source_param.StorageType == StorageType.String:
                source_value_str = source_param.AsString()
                # Consider non-empty string as having a value
                if source_value_str and source_value_str.strip():
                    source_has_value = True
            elif source_param.StorageType == StorageType.Double:
                 # Example: Check if non-zero for numeric rating
                 if source_param.AsDouble() != 0.0:
                      source_has_value = True
            elif source_param.StorageType == StorageType.Integer:
                 # Example: Check if non-zero for integer rating
                 if source_param.AsInteger() != 0:
                      source_has_value = True
            # Add other StorageType checks if necessary (e.g., ElementId)
            else:
                 # If just HasValue is enough (regardless of content)
                 source_has_value = True # Fallback: If it has *any* value

        # Determine the target value (1 for Yes, 0 for No)
        target_value_to_set = 1 if source_has_value else 0

        # Get the target 'Has Fire Rating' parameter
        target_param = door.LookupParameter(target_param_name)

        if target_param:
            if target_param.IsReadOnly:
                skipped_target_readonly += 1
            elif target_param.StorageType != StorageType.Integer:
                # Yes/No parameters are stored as Integers (0 or 1)
                skipped_target_wrong_type += 1
            else:
                # Check if the parameter needs updating
                current_value = target_param.AsInteger()
                if current_value != target_value_to_set:
                    try:
                        set_result = target_param.Set(target_value_to_set)
                        if set_result:
                            updated_doors_count += 1
                        else:
                            # Failed to set for some reason
                            error_count += 1
                    except Exception as set_ex:
                        # print("Error setting parameter for door {{}}: {{}}".format(door_id, set_ex)) # Debug
                        error_count += 1
                else:
                    skipped_already_set += 1 # Already has the correct value
        else:
            skipped_no_target_param += 1 # Target parameter not found on this door

    except System.Exception as ex:
        # Catch unexpected errors during processing for a specific door
        # print("Error processing Door ID {{}}: {{}}".format(door_id, ex)) # Debug
        error_count += 1

# --- Final Output ---
print("--- Door 'Has Fire Rating' Parameter Update Summary ---")
print("Total Door Instances Processed: {}".format(processed_doors_count))
print("Successfully Updated: {}".format(updated_doors_count))
print("Skipped (Already Correct Value): {}".format(skipped_already_set))
print("Skipped (Target Param '{}' Not Found): {}".format(target_param_name, skipped_no_target_param))
print("Skipped (Target Param Read-Only): {}".format(skipped_target_readonly))
print("Skipped (Target Param Not Yes/No Type): {}".format(skipped_target_wrong_type))
print("Errors During Processing: {}".format(error_count))