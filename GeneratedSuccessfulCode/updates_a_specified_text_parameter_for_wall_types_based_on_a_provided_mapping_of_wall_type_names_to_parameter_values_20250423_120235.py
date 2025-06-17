# Purpose: This script updates a specified text parameter for Wall Types based on a provided mapping of Wall Type names to parameter values.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallType,
    Parameter,
    StorageType,
    Element
)
import System # Required for String comparison

# --- Configuration ---
# Input data mapping Wall Type Name to the desired TEXT value for the parameter
# Format: TypeName,InsulationThicknessValue (as text)
input_data_string = """
TypeName,InsulationThickness
EXT-Brick-100Insul,100mm
EXT-Block-150Insul,150mm
INT-Insulated Stud,75mm
"""

# The exact, case-sensitive name of the parameter to set
TARGET_PARAMETER_NAME = "Insulation Thickness"

# --- Parse Input Data ---
wall_type_updates = {}
try:
    lines = input_data_string.strip().split('\n')
    # Skip header line (index 0)
    for line in lines[1:]:
        line = line.strip()
        if line and ',' in line:
            parts = line.split(',', 1) # Split only on the first comma
            type_name = parts[0].strip()
            text_value = parts[1].strip()
            if type_name and text_value:
                wall_type_updates[type_name] = text_value
except Exception as parse_e:
    print("# Error parsing input data string: {}".format(parse_e))
    # Stop script if parsing fails
    wall_type_updates = {} # Clear potentially partial data

# --- Script Core Logic ---
if not wall_type_updates:
    print("# No valid update data parsed from input string. Aborting.")
else:
    # Get all WallType elements in the document
    collector = FilteredElementCollector(doc).OfClass(WallType)
    all_wall_types = {wt.Name: wt for wt in collector.ToElements() if isinstance(wt, WallType)}

    updated_count = 0
    skipped_not_found = 0
    skipped_param_missing = 0
    skipped_param_readonly = 0
    skipped_param_not_text = 0
    error_count = 0
    processed_target_types = set()

    # Iterate through the requested updates
    for target_type_name, target_text_value in wall_type_updates.items():
        processed_target_types.add(target_type_name)
        wall_type = None

        # Case-sensitive search first
        if target_type_name in all_wall_types:
             wall_type = all_wall_types[target_type_name]
        else:
            # Optional: Case-insensitive fallback search (can be slower)
            # found = False
            # for wt_name, wt_element in all_wall_types.items():
            #     if wt_name.Equals(target_type_name, System.StringComparison.OrdinalIgnoreCase):
            #         wall_type = wt_element
            #         print("# Info: Found Wall Type '{}' using case-insensitive match for target '{}'.".format(wt_name, target_type_name))
            #         found = True
            #         break
            # if not found:
                skipped_not_found += 1
                # print("# Skipping: Wall Type '{}' not found in the project.".format(target_type_name)) # Optional debug
                continue

        if wall_type:
            try:
                # Find the parameter by name on the WallType
                param = wall_type.LookupParameter(TARGET_PARAMETER_NAME)

                if not param:
                    skipped_param_missing += 1
                    # print("# Skipping '{}': Parameter '{}' not found.".format(target_type_name, TARGET_PARAMETER_NAME)) # Optional debug
                    continue

                if param.IsReadOnly:
                    skipped_param_readonly += 1
                    # print("# Skipping '{}': Parameter '{}' is read-only.".format(target_type_name, TARGET_PARAMETER_NAME)) # Optional debug
                    continue

                # *** Crucial Check: Ensure the parameter accepts a String ***
                if param.StorageType != StorageType.String:
                    skipped_param_not_text += 1
                    # print("# Skipping '{}': Parameter '{}' is not a Text parameter (StorageType is {}). Cannot set text value '{}'.".format(target_type_name, TARGET_PARAMETER_NAME, param.StorageType, target_text_value)) # Optional debug
                    continue

                # Set the parameter value (as text)
                # Transaction is handled externally
                success = param.Set(target_text_value)
                if success:
                    updated_count += 1
                    # print("# Success: Set '{}' parameter for Wall Type '{}' to '{}'.".format(TARGET_PARAMETER_NAME, target_type_name, target_text_value)) # Optional debug
                else:
                    # Set returned false, indicating potential issue
                    error_count += 1
                    print("# Warning: Setting parameter '{}' for Wall Type '{}' returned false.".format(TARGET_PARAMETER_NAME, target_type_name))

            except Exception as e:
                error_count += 1
                print("# Error processing Wall Type '{}': {}".format(target_type_name, e))
        # else: # Handled by the initial check and continue statement
            # skipped_not_found += 1 - This count is done before entering this block

    # --- Summary (Optional: Print to console for feedback) ---
    # print("--- Wall Type Parameter Update Summary ---")
    # print("Target Parameter: '{}' (as Text)".format(TARGET_PARAMETER_NAME))
    # print("Successfully updated: {}".format(updated_count))
    # print("Skipped (Wall Type name not found): {}".format(skipped_not_found))
    # print("Skipped (Parameter '{}' missing): {}".format(TARGET_PARAMETER_NAME, skipped_param_missing))
    # print("Skipped (Parameter read-only): {}".format(skipped_param_readonly))
    # print("Skipped (Parameter not Text type): {}".format(skipped_param_not_text))
    # print("Errors during processing/setting: {}".format(error_count))
    # print("Total Wall Type names in input data: {}".format(len(wall_type_updates)))