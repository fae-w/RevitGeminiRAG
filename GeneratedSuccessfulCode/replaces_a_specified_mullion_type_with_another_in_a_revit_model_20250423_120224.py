# Purpose: This script replaces a specified mullion type with another in a Revit model.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Mullion, MullionType, ElementId
# Using System Exception for more specific error handling if needed
import System

# --- Configuration ---
target_type_name = 'Rectangular Mullion 50x150mm'
replacement_type_name = 'Circular Mullion 100mm'

# --- Find Mullion Types ---
target_mullion_type = None
replacement_mullion_type = None

# Collect all MullionType elements in the document
mullion_types_collector = FilteredElementCollector(doc).OfClass(MullionType)

# Iterate through the collected types to find the target and replacement types by name
for mt in mullion_types_collector:
    try:
        # Using GetName() method which is safer than .Name property in some edge cases
        current_name = mt.Name # Element.Name works fine for Type elements too
        if current_name == target_type_name:
            target_mullion_type = mt
        if current_name == replacement_type_name:
            replacement_mullion_type = mt
        # Optimization: Stop searching if both types have been found
        if target_mullion_type and replacement_mullion_type:
            break
    except Exception as e:
        print("# Warning: Could not process MullionType ID {}: {}".format(mt.Id, e))


# --- Validation ---
if not target_mullion_type:
    print("# Error: Target Mullion Type '{}' not found.".format(target_type_name))
elif not replacement_mullion_type:
    print("# Error: Replacement Mullion Type '{}' not found.".format(replacement_type_name))
else:
    print("# Found Target Mullion Type: '{}' (ID: {})".format(target_mullion_type.Name, target_mullion_type.Id))
    print("# Found Replacement Mullion Type: '{}' (ID: {})".format(replacement_mullion_type.Name, replacement_mullion_type.Id))

    # --- Collect and Modify Mullion Instances ---
    # Collect all Mullion instances in the project
    mullion_instances_collector = FilteredElementCollector(doc)\
                                  .OfCategory(BuiltInCategory.OST_CurtainWallMullions)\
                                  .WhereElementIsNotElementType()

    changed_count = 0
    error_count = 0
    skipped_locked_count = 0
    processed_count = 0

    for mullion_instance in mullion_instances_collector:
        processed_count += 1
        # Ensure it's a Mullion object (though collector should handle this)
        if isinstance(mullion_instance, Mullion):
            try:
                # Check if the mullion's current type ID matches the target type ID
                if mullion_instance.GetTypeId() == target_mullion_type.Id:
                    # Attempt to change the mullion's type using the MullionType property setter
                    mullion_instance.MullionType = replacement_mullion_type
                    changed_count += 1

            except System.InvalidOperationException as lock_ex:
                 # Catch exception often thrown for locked mullions when trying to change type
                 # print("# Info: Skipping locked/constrained Mullion ID {}: {}".format(mullion_instance.Id, lock_ex.Message)) # Optional detailed log
                 skipped_locked_count += 1
            except Exception as e:
                print("# Error processing Mullion ID {}: {}".format(mullion_instance.Id, e))
                error_count += 1

    # --- Report Results ---
    print("# --- Update Results ---")
    print("# Successfully changed type for {} mullions.".format(changed_count))
    if skipped_locked_count > 0:
        print("# Skipped {} potentially locked/constrained mullions.".format(skipped_locked_count))
    if error_count > 0:
        print("# Encountered errors processing {} mullions.".format(error_count))
    print("# Total mullion instances checked: {}".format(processed_count))

# Final message if operation couldn't proceed due to missing types
if not target_mullion_type or not replacement_mullion_type:
    print("# Operation could not proceed: One or both specified Mullion Types were not found in the document.")