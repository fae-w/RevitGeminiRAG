# Purpose: This script updates the top offset of structural columns between specified levels.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often useful, though not strictly required here
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    Level,
    ElementId,
    Parameter,
    BuiltInParameter
)
# Corrected Import for StructuralType:
from Autodesk.Revit.DB.Structure import StructuralType
from System import Exception as SystemException # For exception handling

# --- Configuration ---
base_level_name = "Level 2"
top_level_name = "Level 3"
# Interpretation: "Related to Upper Level" means the column's Top Level is set
# to the upper level ('Level 3') and the Top Offset is 0.0.
# The script will filter for columns already spanning Level 2 to Level 3
# and ensure their Top Offset is set to 0.0.
target_top_offset = 0.0 # Target offset in internal units (feet)

# --- Initialization ---
base_level_id = ElementId.InvalidElementId
top_level_id = ElementId.InvalidElementId
updated_count = 0
skipped_level_mismatch = 0
skipped_not_column = 0
skipped_param_missing = 0
skipped_param_readonly = 0
skipped_already_set = 0
error_count = 0
processed_count = 0
output_messages = [] # Collect messages

# --- Step 1: Find Target Levels ---
# Assume 'doc' is pre-defined and available
level_collector = FilteredElementCollector(doc).OfClass(Level)
levels = list(level_collector) # Get all levels first

for level in levels:
    if level.Name == base_level_name:
        base_level_id = level.Id
    if level.Name == top_level_name:
        top_level_id = level.Id

# Check if both levels were found
levels_found = True
if base_level_id == ElementId.InvalidElementId:
    output_messages.append("# Error: Base Level '{0}' not found.".format(base_level_name))
    levels_found = False
if top_level_id == ElementId.InvalidElementId:
    output_messages.append("# Error: Top Level '{0}' not found.".format(top_level_name))
    levels_found = False

# Proceed only if both levels were found
if levels_found:
    output_messages.append("# Info: Found Base Level '{0}' (ID: {1})".format(base_level_name, base_level_id))
    output_messages.append("# Info: Found Top Level '{0}' (ID: {1})".format(top_level_name, top_level_id))

    # --- Step 2: Collect Structural Columns ---
    column_collector = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralColumns)\
        .WhereElementIsNotElementType()

    columns = list(column_collector) # Convert iterator to list

    if not columns:
        output_messages.append("# Info: No structural column instances found in the document.")
    else:
         # --- Step 3: Iterate and Update Columns ---
        # Transaction is assumed to be handled externally
        for column in columns:
            processed_count += 1
            col_id_str = "ID: {0}".format(column.Id)

            # Basic check: Ensure it's a FamilyInstance
            if not isinstance(column, FamilyInstance):
                skipped_not_column += 1
                continue

            # Optional check: Verify it's a structural column type using the corrected import
            # Note: This might skip some valid columns if they don't report StructuralType correctly.
            # Relying on category filter + parameter checks might be sufficient.
            try:
                if hasattr(column, 'StructuralType'):
                    if column.StructuralType != StructuralType.Column:
                        skipped_not_column += 1
                        # output_messages.append("# Debug: Skipped {0} - Not StructuralType.Column".format(col_id_str))
                        continue
                # If StructuralType attribute doesn't exist, we might still proceed if parameters are found
                # else:
                #    output_messages.append("# Debug: Column {0} lacks StructuralType property, proceeding based on parameters.".format(col_id_str))

            except SystemException as type_ex:
                 output_messages.append("# Warning: Error checking StructuralType for Column {0}: {1}. Proceeding.".format(col_id_str, type_ex.Message))
                 pass # Continue to parameter checks even if StructuralType check failed

            try:
                # Get Base and Top Level parameters
                base_level_param = column.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
                top_level_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)

                # Check if parameters exist and match the target levels
                if (base_level_param and top_level_param and
                        base_level_param.HasValue and top_level_param.HasValue and
                        base_level_param.AsElementId() == base_level_id and
                        top_level_param.AsElementId() == top_level_id):

                    # Levels match, now check and set the 'Top Offset'
                    top_offset_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_OFFSET_PARAM)

                    if top_offset_param:
                        if not top_offset_param.IsReadOnly:
                            current_offset = top_offset_param.AsDouble()
                            # Using feet internally, define a small tolerance
                            tolerance = 0.0001 # ~ 1/10000th of a foot

                            # Check if already set to the target value within tolerance
                            if abs(current_offset - target_top_offset) < tolerance:
                                skipped_already_set += 1
                                # output_messages.append("# Debug: Column {0} already has Top Offset ~{1}. Skipping.".format(col_id_str, target_top_offset))
                                continue
                            else:
                                # Set the Top Offset to 0.0
                                try:
                                    # Transaction is handled externally
                                    set_result = top_offset_param.Set(target_top_offset)
                                    if set_result:
                                        updated_count += 1
                                        # output_messages.append("# Debug: Updated Top Offset for Column {0}".format(col_id_str))
                                    else:
                                        output_messages.append("# Warning: Failed to set Top Offset for Column {0} (Set returned false). Check permissions/constraints. Skipping.".format(col_id_str))
                                        skipped_param_readonly += 1 # Count as failure similar to read-only
                                except SystemException as set_ex:
                                     output_messages.append("# Error setting Top Offset for Column {0}: {1}".format(col_id_str, set_ex.Message))
                                     error_count += 1
                        else:
                            # output_messages.append("# Warning: Top Offset parameter is read-only for Column {0}. Skipping.".format(col_id_str))
                            skipped_param_readonly += 1
                    else:
                        # output_messages.append("# Warning: Top Offset parameter (FAMILY_TOP_OFFSET_PARAM) not found for Column {0}. Skipping.".format(col_id_str))
                        skipped_param_missing += 1
                else:
                    # Levels didn't match or parameters missing/invalid
                    skipped_level_mismatch += 1

            except SystemException as ex:
                output_messages.append("# Error processing Column {0}: {1}".format(col_id_str, ex.Message))
                error_count += 1

        # --- Final Summary ---
        output_messages.append("\n# --- Column Update Summary ---")
        output_messages.append("# Target Base Level: '{0}' (ID: {1})".format(base_level_name, base_level_id))
        output_messages.append("# Target Top Level: '{0}' (ID: {1})".format(top_level_name, top_level_id))
        output_messages.append("# Action: Set Top Offset to {0} ft for matching columns.".format(target_top_offset))
        output_messages.append("# Total Structural Column Instances Found (Category Filter): {0}".format(len(columns)))
        output_messages.append("# Columns Processed: {0}".format(processed_count))
        # Estimate columns matching levels = sum of subsequent outcomes for those columns
        matching_level_cols = updated_count + skipped_already_set + skipped_param_missing + skipped_param_readonly + error_count # Note: Errors might occur before/during level check
        output_messages.append("# Columns Matching Target Levels ('{0}' to '{1}'): {2}".format(base_level_name, top_level_name, matching_level_cols ))
        output_messages.append("# Successfully Updated (Top Offset set to {0}): {1}".format(target_top_offset, updated_count))
        output_messages.append("# Skipped (Not FamilyInstance / Filtered by StructuralType): {0}".format(skipped_not_column))
        output_messages.append("# Skipped (Incorrect Base/Top Level or Level Param Missing): {0}".format(skipped_level_mismatch))
        output_messages.append("# Skipped (Top Offset Already ~{0}): {1}".format(target_top_offset, skipped_already_set))
        output_messages.append("# Skipped (Top Offset Param Missing on Matching Level Col): {0}".format(skipped_param_missing))
        output_messages.append("# Skipped (Top Offset Param Read-Only/Set Failed on Matching Level Col): {0}".format(skipped_param_readonly))
        output_messages.append("# Errors Encountered during processing/setting: {0}".format(error_count))
        if error_count > 0:
            output_messages.append("# Review specific error messages printed above for details.")

# --- Print Collected Messages ---
final_output = "\n".join(output_messages)
print(final_output)

# Optional: Add a final confirmation line if needed by the external runner
# print("SCRIPT_EXECUTION_COMPLETE")