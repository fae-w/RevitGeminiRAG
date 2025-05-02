# Purpose: This script updates the 'Type Mark' parameter of Revit door types with a prefixed, sequentially numbered value.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementType,
    BuiltInParameter,
    Parameter,
    StorageType
)
import System # For exception handling

# --- Configuration ---
param_bip = BuiltInParameter.ALL_MODEL_TYPE_MARK
prefix = "D-"
start_number = 1
number_padding = 3 # e.g., 3 -> 001, 010, 100

# --- Collect Door Types ---
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsElementType()

# --- Process Door Types ---
updated_count = 0
skipped_no_param_count = 0
skipped_param_readonly_count = 0
skipped_param_wrong_type_count = 0
error_count = 0
processed_count = 0
current_number = start_number

# Get all elements found by the collector into a list first
# This is safer if modifying elements while iterating, although here we modify types
door_types = list(collector)
total_types = len(door_types)
print("# Found {} Door Types to process.".format(total_types))

for door_type in door_types:
    if not isinstance(door_type, ElementType):
        continue # Should not happen with the collector settings, but good practice

    processed_count += 1
    type_id = door_type.Id
    type_name = "Unknown"
    try:
        # Element.Name is obsolete, use specific properties or GetName()
        type_name = door_type.Name # Direct property for ElementType
    except AttributeError:
        try:
            type_name = Element.Name.GetValue(door_type) # Fallback
        except Exception:
             pass # Keep type_name as "Unknown"

    try:
        # Get the 'Type Mark' parameter
        param = door_type.get_Parameter(param_bip)

        if param:
            param_name = param.Definition.Name # Get actual parameter name for logging
            # Check if parameter is suitable for setting a string value
            if param.IsReadOnly:
                skipped_param_readonly_count += 1
                print("# Skipping Type ID {0} ('{1}'): Parameter '{2}' is read-only.".format(type_id, type_name, param_name))
            elif param.StorageType != StorageType.String:
                skipped_param_wrong_type_count += 1
                print("# Skipping Type ID {0} ('{1}'): Parameter '{2}' has wrong storage type ({3}), expected String.".format(type_id, type_name, param_name, param.StorageType))
            else:
                # Generate the new unique value
                new_value = "{}{:0{}}".format(prefix, current_number, number_padding)

                # Set the parameter value (Transaction handled externally)
                set_result = param.Set(new_value)

                if set_result:
                    updated_count += 1
                    # print("# Updated Type ID {0} ('{1}'): Set '{2}' to '{3}'.".format(type_id, type_name, param_name, new_value)) # Debug
                    current_number += 1 # Increment counter only on successful update
                else:
                    error_count += 1
                    print("# Failed to set parameter '{0}' for Type ID {1} ('{2}').".format(param_name, type_id, type_name))

        else:
            skipped_no_param_count += 1
            param_identifier_str = str(param_bip) # Use BIP enum name for logging
            print("# Skipping Type ID {0} ('{1}'): Parameter {2} ('Type Mark') not found.".format(type_id, type_name, param_identifier_str))

    except System.Exception as ex:
        error_count += 1
        param_identifier_str = str(param_bip)
        if param and hasattr(param, 'Definition'):
            param_identifier_str = "'{}'".format(param.Definition.Name)
        print("# Error processing Type ID {0} ('{1}') for parameter {2}: {3}".format(type_id, type_name, param_identifier_str, ex.Message))

# Final summary
print("--- Door Type Mark Update Summary ---")
print("Total Door Types Checked: {}".format(processed_count))
print("Successfully Updated: {}".format(updated_count))
print("Skipped (Parameter Not Found): {}".format(skipped_no_param_count))
print("Skipped (Parameter Read-Only): {}".format(skipped_param_readonly_count))
print("Skipped (Parameter Wrong Type): {}".format(skipped_param_wrong_type_count))
print("Errors During Processing: {}".format(error_count))
print("Next available number: {}".format(current_number))