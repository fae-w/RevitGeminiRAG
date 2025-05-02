# Purpose: This script updates parameters of a Revit door instance based on an input string.

﻿# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    ElementId,
    BuiltInCategory,
    FamilyInstance,
    Parameter,
    BuiltInParameter,
    StorageType,
    Element
)
import System # For exception handling and parsing

# --- Configuration ---
target_element_id_int = 23456
input_data_string = "ID=23456, FireRating=90 min, FrameMaterial=Steel, Comments=Heavy Duty Use"

# --- Data Parsing ---
parameters_to_update = {}
try:
    # Remove the ID part first if present, as we use the integer ID directly
    if input_data_string.startswith("ID="):
        parts = input_data_string.split(',', 1)
        if len(parts) > 1:
            input_data_string = parts[1].strip()
        else:
            input_data_string = "" # Only ID was provided

    if input_data_string:
        pairs = input_data_string.split(',')
        for pair in pairs:
            key_value = pair.split('=', 1)
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                parameters_to_update[key] = value
            else:
                print("# Warning: Skipping malformed pair: '{}'".format(pair))

except Exception as parse_ex:
    print("# Error parsing input string: {}".format(str(parse_ex)))
    parameters_to_update = {} # Clear if parsing fails

# --- Parameter Mapping (Input Key -> Revit Parameter Identifier) ---
# Using a dictionary where value is a tuple: (Parameter Identifier, Expected StorageType)
# Using None for identifier means try LookupParameter
# Using None for StorageType means skip type check (use with caution)
parameter_map = {
    "FireRating": (BuiltInParameter.FIRE_RATING, StorageType.String),
    "FrameMaterial": (BuiltInParameter.DOOR_FRAME_MATERIAL, StorageType.String), # Often a type parameter, might fail on instance
    "Comments": (BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, StorageType.String)
}
# Alternative name lookup if BuiltInParameter fails for FrameMaterial
alternative_lookup = {
    "FrameMaterial": "Frame Material"
}


# --- Main Logic ---
update_summary = []
error_messages = []
element_found = False
element_is_door = False

if not parameters_to_update:
    error_messages.append("No valid parameters found in the input string.")
else:
    try:
        target_element_id = ElementId(target_element_id_int)
        element = doc.GetElement(target_element_id)

        if element:
            element_found = True
            # Check if it's a Door Instance
            if element.Category and element.Category.Id == ElementId(BuiltInCategory.OST_Doors) and isinstance(element, FamilyInstance):
                element_is_door = True
                door_instance = element # Cast for clarity

                for key, value_to_set in parameters_to_update.items():
                    param_identifier = None
                    expected_type = None
                    param_name_for_lookup = None

                    if key in parameter_map:
                        param_identifier, expected_type = parameter_map[key]
                    elif key in alternative_lookup:
                        # Fallback to name lookup if not in primary map
                        param_name_for_lookup = alternative_lookup[key]
                        expected_type = StorageType.String # Assume string for lookup if not defined
                    else:
                        error_messages.append("Parameter key '{}' not recognized or mapped.".format(key))
                        continue # Skip to next parameter

                    param = None
                    try:
                        if param_identifier:
                            # Try getting parameter using BuiltInParameter first
                             param = door_instance.get_Parameter(param_identifier)
                             # If BuiltInParameter returned None, maybe it's a type parameter? Try lookup as fallback.
                             if not param and key in alternative_lookup:
                                 param_name_for_lookup = alternative_lookup[key]

                        # If BuiltInParameter didn't work or wasn't specified, try LookupParameter
                        if not param and param_name_for_lookup:
                            param = door_instance.LookupParameter(param_name_for_lookup)
                            # Check type parameter as well if instance lookup fails
                            if not param and door_instance.Symbol:
                                param = door_instance.Symbol.LookupParameter(param_name_for_lookup)


                        if param:
                            if param.IsReadOnly:
                                error_messages.append("Parameter '{}' is read-only.".format(key))
                            elif expected_type and param.StorageType != expected_type:
                                error_messages.append("Parameter '{}' has wrong type (Expected: {}, Actual: {}).".format(key, expected_type, param.StorageType))
                            else:
                                # Attempt to set the value
                                try:
                                    set_result = False
                                    if param.StorageType == StorageType.String:
                                        set_result = param.Set(value_to_set)
                                    elif param.StorageType == StorageType.Double:
                                        # Try converting value to double (assuming feet if unit applies)
                                         try_val = float(value_to_set)
                                         set_result = param.Set(try_val)
                                    elif param.StorageType == StorageType.Integer:
                                         # Try converting value to integer
                                         try_val = int(value_to_set)
                                         set_result = param.Set(try_val)
                                    # Add ElementId handling if needed
                                    # elif param.StorageType == StorageType.ElementId:
                                    #    try_val = ElementId(int(value_to_set)) # Example
                                    #    set_result = param.Set(try_val)

                                    if set_result:
                                        update_summary.append("Successfully updated '{}' to '{}'.".format(key, value_to_set))
                                    else:
                                        error_messages.append("Failed to set parameter '{}' (Check value validity/constraints). Value: '{}'".format(key, value_to_set))
                                except Exception as set_ex:
                                    error_messages.append("Error setting parameter '{}': {}".format(key, str(set_ex)))
                        else:
                             # Parameter not found by either method
                             error_messages.append("Parameter '{}' (Identifier: {}, Lookup: {}) not found on element {} or its type.".format(key, param_identifier, param_name_for_lookup, target_element_id_int))

                    except System.Exception as param_ex:
                        error_messages.append("Error processing parameter '{}': {}".format(key, str(param_ex)))

            else:
                 error_messages.append("Element with ID {} found, but it is not a Door instance.".format(target_element_id_int))
                 if element.Category:
                     error_messages.append("Element Category: {}".format(element.Category.Name))
                 else:
                     error_messages.append("Element has no Category.")


        else:
            error_messages.append("Element with ID {} not found in the document.".format(target_element_id_int))

    except System.Exception as ex:
        error_messages.append("An unexpected error occurred: {}".format(str(ex)))

# --- Final Output ---
print("--- Update Summary for Door ID {} ---".format(target_element_id_int))
if update_summary:
    for msg in update_summary:
        print(msg)
if error_messages:
    print("\n--- Errors/Warnings ---")
    for msg in error_messages:
        print(msg)

if not update_summary and not error_messages:
     print("No parameters were processed or no element found.")