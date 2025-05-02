# Purpose: This script renames Revit project and shared parameters by replacing specified special characters.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterElement,
    Definition, # Base class for definitions
    InternalDefinition, # To check for built-in parameters
    ExternalDefinition, # To check for shared parameters (though not strictly needed for renaming via ParameterElement)
    BuiltInParameter, # Enum for checking against INVALID
    Element # Base class for Name property reference
)
import System # For exception handling

# --- Configuration ---
# Characters to find and replace in parameter names
chars_to_find = ['/', '(', ')']
replacement_char = '_' # Character to replace the special characters with

# --- Assumption ---
# This script assumes "parameters" refers to Project Parameters and Shared Parameters
# visible in the project environment (represented by ParameterElement objects).
# It attempts to rename them by replacing specified special characters in their names.
# It specifically avoids renaming Built-in Parameters.
# Renaming parameters defined *within* families would require editing each family document.

# --- Initialization ---
renamed_count = 0
skipped_builtin_count = 0
skipped_no_special_chars_count = 0
skipped_name_unchanged_count = 0
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
             # print("# Debug: Could not get Definition for ParameterElement ID {}. Skipping.".format(param_elem.Id))
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
            # print("# Debug: Skipping Built-in Parameter ID {}".format(param_elem.Id))
            continue

        # Get the current name of the ParameterElement
        current_name = ""
        try:
            # Use Element.Name property getter
            current_name = param_elem.Name
        except Exception as name_ex:
             # print("# Error retrieving name for ParameterElement ID {}: {}. Skipping.".format(param_elem.Id, name_ex))
             error_count += 1
             continue

        if not current_name:
             # Skip if name is None or empty
             skipped_no_special_chars_count += 1 # Treat as not needing change
             continue

        # Check if the name contains any of the special characters
        contains_special_char = False
        for char in chars_to_find:
            if char in current_name:
                contains_special_char = True
                break

        if contains_special_char:
            # Construct the new name by replacing each special character
            new_name = current_name
            for char in chars_to_find:
                new_name = new_name.replace(char, replacement_char)

            # Avoid renaming if the new name is the same as the old name
            # (e.g., if replacement results in the original name, though unlikely here)
            if new_name == current_name:
                skipped_name_unchanged_count += 1
                continue

            # Check if new name is empty or invalid (basic check)
            if not new_name or new_name.isspace():
                 # print("# Error: New name for parameter '{}' (ID: {}) would be empty or whitespace. Skipping.".format(current_name, param_elem.Id))
                 error_count += 1
                 continue

            # Attempt to rename by setting the Name property
            try:
                # Use Element.Name property setter
                param_elem.Name = new_name
                renamed_count += 1
                # print("# Renamed '{}' (ID: {}) to '{}'".format(current_name, param_elem.Id, new_name)) # Debug
            except System.ArgumentException as arg_ex:
                # Handle potential errors like duplicate names or invalid characters
                error_count += 1
                # print("# Error renaming parameter '{}' (ID: {}): {}. New name '{}' might already exist or be invalid.".format(current_name, param_elem.Id, arg_ex.Message, new_name))
            except System.InvalidOperationException as inv_op_ex:
                # Handle cases where renaming this specific element/parameter type is not allowed
                 error_count += 1
                 # print("# Error renaming parameter '{}' (ID: {}): {}. Renaming might not be permitted for this parameter.".format(current_name, param_elem.Id, inv_op_ex.Message))
            except Exception as e:
                 # Handle other potential errors during renaming
                 error_count += 1
                 # print("# Unexpected error renaming parameter '{}' (ID: {}): {}".format(current_name, param_elem.Id, e))
        else:
            # Name does not contain any of the specified special characters
            skipped_no_special_chars_count += 1

    except Exception as outer_e:
        # Catch errors during definition check or other unexpected issues
        error_count += 1
        # Try to get Id for error message, might fail if param_elem is weird
        elem_id_str = "Unknown ID"
        try:
             elem_id_str = str(param_elem.Id)
        except:
             pass
        # print("# Error processing ParameterElement ID {}: {}".format(elem_id_str, outer_e))

# --- Optional Summary ---
# print("--- Parameter Renaming Summary ---")
# print("Total ParameterElements processed: {}".format(processed_count))
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (Built-in): {}".format(skipped_builtin_count))
# print("Skipped (No special chars found): {}".format(skipped_no_special_chars_count))
# print("Skipped (Name unchanged after replacement): {}".format(skipped_name_unchanged_count))
# print("Errors encountered: {}".format(error_count))
# print("--- End Summary ---")