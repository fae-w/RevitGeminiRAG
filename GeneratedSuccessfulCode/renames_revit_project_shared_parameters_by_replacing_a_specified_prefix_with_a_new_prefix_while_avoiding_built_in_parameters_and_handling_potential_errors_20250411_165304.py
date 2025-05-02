# Purpose: This script renames Revit project/shared parameters by replacing a specified prefix with a new prefix, while avoiding built-in parameters and handling potential errors.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterElement,
    Definition, # Base class for definitions
    InternalDefinition, # To check for built-in parameters
    BuiltInParameter, # Enum for checking against INVALID
    Element # Base class for Name property reference (though ParameterElement implements it)
)
import System # For exception handling

# --- Configuration ---
old_prefix = "TEMP_"
new_prefix = "ARCHIVED_"

# --- Assumption ---
# This script assumes "parameters" refers to Project Parameters and Shared Parameters
# visible in the project environment (represented by ParameterElement objects).
# It attempts to rename them by setting the ParameterElement.Name property.
# It specifically avoids renaming Built-in Parameters.
# Renaming parameters defined *within* families would require editing each family document.

# --- Initialization ---
renamed_count = 0
skipped_builtin_count = 0
skipped_no_prefix_count = 0
error_count = 0
processed_count = 0

# --- Get all Parameter Elements ---
# Using OfClass(ParameterElement) is the correct way to get project/shared/global parameters
collector = FilteredElementCollector(doc).OfClass(ParameterElement)
parameter_elements = list(collector) # Collect to avoid modifying collection while iterating

# --- Iterate and Rename ---
for param_elem in parameter_elements:
    processed_count += 1
    # Basic check, though collector should guarantee this
    if not isinstance(param_elem, ParameterElement):
        continue

    try:
        # Get the definition to check if it's a built-in parameter
        definition = param_elem.GetDefinition()
        if definition is None:
             # Log error if definition cannot be retrieved
             print("# Error: Could not get Definition for ParameterElement ID {}. Skipping.".format(param_elem.Id))
             error_count += 1
             continue

        # Check if it's a built-in parameter by inspecting InternalDefinition
        is_builtin = False
        # ParameterElement definition can be InternalDefinition or ExternalDefinition
        if isinstance(definition, InternalDefinition):
            # Only InternalDefinitions can represent BuiltInParameters
             internal_def = definition
             if internal_def.BuiltInParameter != BuiltInParameter.INVALID:
                 is_builtin = True

        if is_builtin:
            # Skip built-in parameters - they cannot and should not be renamed
            skipped_builtin_count += 1
            continue

        # Get the current name of the ParameterElement
        # This name is the user-visible name of the project/shared parameter
        current_name = ""
        try:
            # Use Element.Name property getter
            current_name = param_elem.Name
        except Exception as name_ex:
             print("# Error retrieving name for ParameterElement ID {}: {}. Skipping.".format(param_elem.Id, name_ex))
             error_count += 1
             continue

        if current_name is None:
             # Skip if name is None (shouldn't typically happen for ParameterElements)
             skipped_no_prefix_count += 1 # Treat as not matching prefix
             continue

        # Check if the name starts with the old prefix
        if current_name.startswith(old_prefix):
            # Construct the new name
            new_name = new_prefix + current_name[len(old_prefix):]

            # Avoid renaming if the new name is the same (e.g., empty suffix after prefix)
            if new_name == current_name:
                skipped_no_prefix_count += 1
                continue

            # Check if new name is empty or invalid (basic check)
            if not new_name or new_name.isspace():
                 print("# Error: New name for parameter '{}' (ID: {}) would be empty or whitespace. Skipping.".format(current_name, param_elem.Id))
                 error_count += 1
                 continue

            # Attempt to rename by setting the Name property
            try:
                # Use Element.Name property setter
                param_elem.Name = new_name
                renamed_count += 1
            except System.ArgumentException as arg_ex:
                # Handle potential errors like duplicate names or invalid characters
                error_count += 1
                print("# Error renaming parameter '{}' (ID: {}): {}. New name '{}' might already exist or be invalid.".format(current_name, param_elem.Id, arg_ex.Message, new_name))
            except System.InvalidOperationException as inv_op_ex:
                # Handle cases where renaming this specific element/parameter type is not allowed
                 error_count += 1
                 print("# Error renaming parameter '{}' (ID: {}): {}. Renaming might not be permitted for this parameter.".format(current_name, param_elem.Id, inv_op_ex.Message))
            except Exception as e:
                 # Handle other potential errors during renaming
                 error_count += 1
                 print("# Unexpected error renaming parameter '{}' (ID: {}): {}".format(current_name, param_elem.Id, e))
        else:
            # Name does not start with the specified prefix
            skipped_no_prefix_count += 1

    except Exception as outer_e:
        # Catch errors during definition check or other unexpected issues
        error_count += 1
        # Try to get Id for error message, might fail if param_elem is weird
        elem_id_str = "Unknown ID"
        try:
             elem_id_str = str(param_elem.Id)
        except:
             pass
        print("# Error processing ParameterElement ID {}: {}".format(elem_id_str, outer_e))

# --- Optional Summary ---
# print("--- Parameter Renaming Summary ---")
# print("Total ParameterElements processed: {}".format(processed_count))
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (Built-in): {}".format(skipped_builtin_count))
# print("Skipped (Prefix not found or name unchanged): {}".format(skipped_no_prefix_count))
# print("Errors encountered: {}".format(error_count))
# print("--- End Summary ---")