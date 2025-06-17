# Purpose: This script updates door frame materials based on door type names.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    ElementId,
    ElementType,
    Material,
    BuiltInParameter,
    Parameter,
    StorageType,
    FamilyInstance # Instances of doors are FamilyInstances
)
import System # For exception handling

# --- Configuration ---
# Mapping from keyword (lowercase) found in Type Name to the *exact* Material Name in the project
# IMPORTANT: Ensure these Material names exist in your Revit project.
keyword_to_material_name = {
    "wood": "Wood - Generic", # Example: If type name contains 'wood', use 'Wood - Generic' material
    "metal": "Metal - Steel", # Example: If type name contains 'metal', use 'Metal - Steel' material
    "aluminum": "Metal - Aluminum", # Example: If type name contains 'aluminum', use 'Metal - Aluminum' material
    "steel": "Metal - Steel" # Example: If type name contains 'steel', use 'Metal - Steel' material
    # Add more mappings as needed
}

# Built-in parameter for Door Frame Material (adjust if using a custom parameter)
# If using a custom shared/project parameter, use LookupParameter("Your Parameter Name") instead
target_param_bip = BuiltInParameter.DOOR_FRAME_MATERIAL
# Alternatively, if it's a custom parameter:
# target_param_name = "Frame Material" # Use this if target_param_bip is None
# target_param_bip = None

# --- Pre-fetch Material IDs ---
material_name_to_id = {}
material_collector = FilteredElementCollector(doc).OfClass(Material)
materials_found_count = 0
configured_material_names = set(keyword_to_material_name.values())

for mat in material_collector:
    # Element.Name is obsolete, use mat.Name directly for Material
    try:
        mat_name = mat.Name
        if mat_name in configured_material_names:
            material_name_to_id[mat_name] = mat.Id
            materials_found_count += 1
            # print("# Found Material: '{}' with ID: {}".format(mat_name, mat.Id)) # Debug
    except AttributeError:
        # Some elements might not have a Name property accessible like this, though unlikely for Material
        continue


if materials_found_count == 0:
    print("# Warning: No materials matching the configured names found in the project.")
elif materials_found_count < len(configured_material_names):
     print("# Warning: Not all configured material names were found in the project.")

# --- Process Doors ---
# Collect door instances (FamilyInstance)
door_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

updated_count = 0
skipped_no_type_count = 0
skipped_no_param_count = 0
skipped_param_readonly_count = 0
skipped_param_wrong_type_count = 0
skipped_no_keyword_match_count = 0
skipped_material_not_found_count = 0
error_count = 0
processed_count = 0

for door in door_collector:
    # Basic check if it's a FamilyInstance (though collector should guarantee this)
    if not isinstance(door, FamilyInstance):
        continue

    processed_count += 1
    door_id = door.Id
    door_type = None
    type_name = None

    try:
        # Get the ElementType associated with the door instance
        door_type_id = door.GetTypeId()
        if door_type_id != ElementId.InvalidElementId:
            door_type_element = doc.GetElement(door_type_id)
            # Check if the retrieved element is an ElementType
            if isinstance(door_type_element, ElementType):
                 door_type = door_type_element
                 # Element.Name is obsolete, use ElementType.Name directly or GetName extension method
                 try:
                     type_name = door_type.Name # Direct property access if available
                 except AttributeError:
                     try:
                          # Try using Element.Name static method as a fallback for older APIs or specific types
                          type_name = Element.Name.GetValue(door_type)
                     except Exception as e_name:
                          # print("# Warning: Could not get Name for ElementType ID {}: {}".format(door_type_id, e_name)) # Debug
                          pass # Continue without type_name

            # else: # Debugging if needed
            #     print("# Warning: Element retrieved by TypeId {} for Door ID {} is not an ElementType.".format(door_type_id, door_id)) # Debug
    except System.Exception as ex_type:
        # print("# Error getting type for Door ID {}: {}".format(door_id, ex_type.Message)) # Debug
        error_count += 1
        continue # Skip this door if type retrieval fails

    if not door_type or not type_name:
        skipped_no_type_count += 1
        # print("# Skipping Door ID {}: Could not retrieve valid type or type name.".format(door_id)) # Debug
        continue

    type_name_lower = type_name.lower()
    matched_material_name = None
    found_match = False

    # Find the first matching keyword in the type name
    for keyword, material_name in keyword_to_material_name.items():
        if keyword in type_name_lower:
            matched_material_name = material_name
            found_match = True
            break # Use the first keyword found

    if not found_match:
        skipped_no_keyword_match_count += 1
        # print("# Skipping Door ID {} (Type: '{}'): No keyword match.".format(door_id, type_name)) # Debug
        continue

    # Get the target material ID based on the matched name
    target_material_id = material_name_to_id.get(matched_material_name)

    if not target_material_id or target_material_id == ElementId.InvalidElementId:
        skipped_material_not_found_count += 1
        # print("# Skipping Door ID {} (Type: '{}'): Material '{}' not found in project.".format(door_id, type_name, matched_material_name)) # Debug
        continue

    # Get the 'Frame Material' parameter on the instance
    param = None
    param_identifier_str = "Unknown" # Default identifier for logging
    try:
        if target_param_bip is not None:
             param = door.get_Parameter(target_param_bip)
             param_identifier_str = str(target_param_bip)
        # elif target_param_name: # Fallback for custom parameter name
        #     param = door.LookupParameter(target_param_name)
        #     param_identifier_str = target_param_name
        # else: # Should not happen based on config block, but safe check
        #     print("# Error: Parameter identification (BIP or Name) is not configured.")
        #     error_count += 1
        #     continue # Skip door

        if param:
            param_name = param.Definition.Name # Get actual parameter name for logging
            param_identifier_str = "'{}'".format(param_name) # Use actual name if found
            # Check if parameter is suitable for setting Material ID
            if param.IsReadOnly:
                skipped_param_readonly_count += 1
                # print("# Skipping Door ID {}: Parameter {} is read-only.".format(door_id, param_identifier_str)) # Debug
            elif param.StorageType != StorageType.ElementId:
                skipped_param_wrong_type_count += 1
                # print("# Skipping Door ID {}: Parameter {} has wrong storage type ({}), expected ElementId.".format(door_id, param_identifier_str, param.StorageType)) # Debug
            else:
                # Check if update is needed
                current_value_id = param.AsElementId()
                if current_value_id != target_material_id:
                    # Set the parameter value (Transaction handled externally)
                    set_result = param.Set(target_material_id)
                    if set_result:
                        updated_count += 1
                        # print("# Updated Door ID {} (Type: '{}'): Set {} to Material ID {} ('{}').".format(door_id, type_name, param_identifier_str, target_material_id, matched_material_name)) # Debug
                    else:
                        # print("# Failed to set parameter {} for Door ID {}.".format(param_identifier_str, door_id)) # Debug
                        error_count += 1 # Count as error if Set fails
                # else: # Parameter already has the correct value
                    # print("# Skipping Door ID {} (Type: '{}'): Parameter {} already set correctly.".format(door_id, type_name, param_identifier_str)) # Debug
                    pass # Optionally count as skipped_already_correct
        else:
            skipped_no_param_count += 1
            # Update identifier string if BIP was used but param wasn't found
            if target_param_bip is not None: param_identifier_str = str(target_param_bip)
            # elif target_param_name: param_identifier_str = "'{}'".format(target_param_name)
            # print("# Skipping Door ID {}: Parameter {} not found.".format(door_id, param_identifier_str)) # Debug

    except System.Exception as ex_param:
        error_count += 1
        # Use the most specific identifier known at the point of error
        if param and hasattr(param, 'Definition'):
            param_identifier_str = "'{}'".format(param.Definition.Name)
        elif target_param_bip is not None:
             param_identifier_str = str(target_param_bip)
        # elif target_param_name:
        #      param_identifier_str = "'{}'".format(target_param_name)

        print("# Error processing Door ID {} (Type: '{}') for parameter {}: {}".format(door_id, type_name if type_name else 'N/A', param_identifier_str, ex_param.Message))

# Final summary (optional, useful for logging in pyRevit/RPS)
print("--- Door Frame Material Update Summary ---")
print("Total Door Instances Checked: {}".format(processed_count))
print("Successfully Updated: {}".format(updated_count))
print("Skipped (No Type/Name): {}".format(skipped_no_type_count))
print("Skipped (Keyword not in Type Name): {}".format(skipped_no_keyword_match_count))
print("Skipped (Target Material Not Found): {}".format(skipped_material_not_found_count))
print("Skipped (Parameter Not Found): {}".format(skipped_no_param_count))
print("Skipped (Parameter Read-Only): {}".format(skipped_param_readonly_count))
print("Skipped (Parameter Wrong Type): {}".format(skipped_param_wrong_type_count))
# Add count for already correct if needed
print("Errors During Processing: {}".format(error_count))