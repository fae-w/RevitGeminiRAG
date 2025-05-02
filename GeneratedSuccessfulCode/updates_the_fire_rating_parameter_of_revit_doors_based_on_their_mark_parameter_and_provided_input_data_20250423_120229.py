# Purpose: This script updates the 'Fire Rating' parameter of Revit doors based on their 'Mark' parameter and provided input data.

﻿# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    BuiltInParameter,
    Parameter,
    StorageType,
    ParameterValueProvider,
    FilterStringRule,
    FilterStringEquals,
    FilterStringContains, # Might be useful if Mark lookup is not exact
    ElementParameterFilter
)
import System # For exception handling

# --- Configuration ---
# Input data string: Mark,Rating
input_data = """
Mark,Rating
D-SRV-01,60 min
D-SRV-02,90 min
D-STR-01,120 min
"""

# Parameter identifiers
mark_param_bip = BuiltInParameter.ALL_MODEL_MARK
fire_rating_param_bip = BuiltInParameter.FIRE_RATING

# --- Data Parsing ---
door_ratings_to_set = {}
try:
    lines = input_data.strip().split('\n')
    if len(lines) > 1: # Check if there's more than just a header potentially
        header = lines[0].lower().strip()
        if header == "mark,rating": # Simple check for expected header
            for line in lines[1:]:
                parts = line.strip().split(',', 1) # Split only on the first comma
                if len(parts) == 2:
                    mark = parts[0].strip()
                    rating = parts[1].strip()
                    if mark: # Ensure mark is not empty
                        door_ratings_to_set[mark] = rating
        else:
             # Attempt parsing even without header if format seems correct
             for line in lines:
                parts = line.strip().split(',', 1)
                if len(parts) == 2:
                    mark = parts[0].strip()
                    rating = parts[1].strip()
                    if mark:
                        door_ratings_to_set[mark] = rating

except Exception as parse_ex:
    print("# Error parsing input data: {}".format(str(parse_ex)))
    door_ratings_to_set = {} # Clear data if parsing fails

# --- Status Flags/Counters ---
processed_doors_count = 0
updated_doors_count = 0
skipped_same_value = 0
skipped_mark_not_in_list = 0
skipped_no_rating_param = 0
skipped_rating_param_readonly = 0
skipped_rating_param_wrong_type = 0
skipped_no_mark_param = 0
error_count = 0

# --- Main Logic ---
if not door_ratings_to_set:
    print("# No valid Mark-Rating pairs found in the input data. No updates will be performed.")
else:
    # Collect all door instances
    door_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

    for door in door_collector:
        if not isinstance(door, FamilyInstance):
            continue

        processed_doors_count += 1
        door_id = door.Id

        try:
            # Get the 'Mark' parameter
            mark_param = door.get_Parameter(mark_param_bip)

            if mark_param and mark_param.HasValue and mark_param.StorageType == StorageType.String:
                mark_value = mark_param.AsString()

                # Check if this door's mark is in our target list
                if mark_value in door_ratings_to_set:
                    target_rating_value = door_ratings_to_set[mark_value]

                    # Get the 'Fire Rating' parameter
                    fire_rating_param = door.get_Parameter(fire_rating_param_bip)

                    if fire_rating_param:
                        if fire_rating_param.IsReadOnly:
                            skipped_rating_param_readonly += 1
                        elif fire_rating_param.StorageType != StorageType.String:
                            skipped_rating_param_wrong_type += 1
                        else:
                            # Get current value, handle potential null
                            current_rating_value = fire_rating_param.AsString() or ""

                            # Compare current value with the target value
                            if current_rating_value != target_rating_value:
                                try:
                                    set_result = fire_rating_param.Set(target_rating_value)
                                    if set_result:
                                        updated_doors_count += 1
                                    else:
                                        # Failed to set (e.g., invalid value format for parameter constraints)
                                        error_count += 1
                                except Exception as set_ex:
                                    # print("# Error setting Fire Rating for Door ID {}: {}".format(door_id, set_ex)) # Debug
                                    error_count += 1
                            else:
                                # Value is already correct
                                skipped_same_value += 1
                    else:
                        # Fire Rating parameter doesn't exist on this door
                        skipped_no_rating_param += 1
                else:
                    # Door's mark was not found in the provided list
                    skipped_mark_not_in_list += 1
            else:
                # Mark parameter not found, has no value, or is not text
                 skipped_no_mark_param += 1

        except System.Exception as ex:
            # Catch unexpected errors during processing for a specific door
            # print("# Error processing Door ID {}: {}".format(door_id, ex)) # Debug
            error_count += 1

    # --- Final Output ---
    print("--- Door Fire Rating Update Summary ---")
    print("Input Mark-Rating Pairs Provided: {}".format(len(door_ratings_to_set)))
    print("Total Door Instances Processed: {}".format(processed_doors_count))
    print("Successfully Updated: {}".format(updated_doors_count))
    print("Skipped (Value Already Correct): {}".format(skipped_same_value))
    print("Skipped (Mark Not in Input List): {}".format(skipped_mark_not_in_list))
    print("Skipped (Door Has No 'Mark' Parameter/Value): {}".format(skipped_no_mark_param))
    print("Skipped (Door Has No 'Fire Rating' Parameter): {}".format(skipped_no_rating_param))
    print("Skipped ('Fire Rating' Parameter Read-Only): {}".format(skipped_rating_param_readonly))
    print("Skipped ('Fire Rating' Parameter Not Text Type): {}".format(skipped_rating_param_wrong_type))
    print("Errors During Update Attempts: {}".format(error_count))