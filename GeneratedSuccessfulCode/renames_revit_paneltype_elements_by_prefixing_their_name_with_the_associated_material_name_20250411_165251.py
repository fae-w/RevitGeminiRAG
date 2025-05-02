# Purpose: This script renames Revit PanelType elements by prefixing their name with the associated material name.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    PanelType,          # Class representing curtain panel types
    FamilySymbol,       # PanelType inherits from this
    Element,
    ElementId,
    Material,
    Parameter,
    StorageType,
    BuiltInParameter    # Keep for potential future use or alternative checks
)
import System # For exception handling

# --- Script Core Logic ---

# Parameter name to look for (case-sensitive)
# Assumption: The material of the panel type is defined by a type parameter named "Material".
# This is common but might need adjustment if families use a different parameter name.
material_param_name = "Material"

renamed_count = 0
skipped_no_param_count = 0
skipped_no_material_count = 0
skipped_already_prefixed_count = 0
error_count = 0
processed_count = 0

# Collect all PanelType elements in the project
try:
    collector = FilteredElementCollector(doc).OfClass(PanelType)
    panel_types_to_process = list(collector)
    processed_count = len(panel_types_to_process)

    for panel_type in panel_types_to_process:
        if not isinstance(panel_type, PanelType):
            continue

        current_name = "Unknown" # Default in case of early error
        try:
            current_name = Element.Name.GetValue(panel_type)
            if not current_name: # Handle potential null or empty names early
                current_name = "Unnamed PanelType ID: {}".format(panel_type.Id)
                # print("# Skipping PanelType ID: {}. Name is null or empty.".format(panel_type.Id))
                error_count += 1 # Consider this an error or skip? Let's count as error.
                continue

            material_name_str = None
            material_param = None

            # Try to get the 'Material' parameter by name
            material_param = panel_type.LookupParameter(material_param_name)

            # Optional: Add checks for BuiltInParameters if LookupParameter fails for certain types
            # Example: material_param = panel_type.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)
            # Be cautious as BIPs might not apply or have different meanings on types.

            if material_param and not material_param.IsReadOnly:
                # Check if the parameter stores an ElementId (expected for Material parameters)
                if material_param.StorageType == StorageType.ElementId:
                    material_id = material_param.AsElementId()
                    if material_id and material_id != ElementId.InvalidElementId:
                        material_element = doc.GetElement(material_id)
                        if isinstance(material_element, Material):
                            material_name_str = Element.Name.GetValue(material_element)
                            if not material_name_str:
                                # Material exists but has no name? Unlikely but possible.
                                material_name_str = None
                                # print(f"# Debug: Material Element ID {material_id} has no name.") # Debug
                        # else:
                        #    print(f"# Debug: Element ID {material_id} from parameter '{material_param_name}' in '{current_name}' is not a Material.") # Debug
                    # else:
                    #    print(f"# Debug: Parameter '{material_param_name}' in '{current_name}' has an invalid or null Material ID.") # Debug

                # Handle string type just in case, though less common for Material parameter
                elif material_param.StorageType == StorageType.String:
                     temp_name = material_param.AsString()
                     # Use the string directly if it's not empty or just whitespace
                     if temp_name and not temp_name.isspace():
                         material_name_str = temp_name
                #else:
                    # print(f"# Debug: Parameter '{material_param_name}' in '{current_name}' has unexpected storage type: {material_param.StorageType}") # Debug

            # Proceed if a valid material name was found
            if material_name_str:
                # Construct the potential new name
                # Format: "MaterialName - CurrentTypeName"
                prefix = material_name_str + " - "
                new_name = prefix + current_name

                # Check if renaming is needed (different name and doesn't already have the prefix)
                if current_name != new_name and not current_name.startswith(prefix):
                    try:
                        # Rename the PanelType (Transaction handled externally by C# wrapper)
                        panel_type.Name = new_name
                        renamed_count += 1
                        # print(f"# Renamed '{current_name}' (ID: {panel_type.Id}) to '{new_name}'") # Debug
                    except System.ArgumentException as arg_ex:
                        # Handle potential duplicate name errors or invalid characters
                        error_count += 1
                        print("# Error renaming PanelType '{}' (ID: {}): New name '{}' might already exist or be invalid. {}".format(current_name, panel_type.Id, new_name, arg_ex.Message))
                    except System.Exception as rename_ex:
                        # Handle other potential errors during renaming
                        error_count += 1
                        print("# Error renaming PanelType '{}' (ID: {}): {}".format(current_name, panel_type.Id, rename_ex.Message))
                else:
                    # Name already has the prefix or is somehow identical after construction
                    skipped_already_prefixed_count += 1
                    # print(f"# Skipping PanelType '{current_name}' (ID: {panel_type.Id}). Already prefixed or no change.") # Debug
            else:
                # Material parameter was either not found, or found but didn't yield a valid material name
                if material_param:
                    # Parameter found, but no valid material/name obtained
                    skipped_no_material_count += 1
                    # print(f"# Skipping PanelType '{current_name}' (ID: {panel_type.Id}). Parameter '{material_param_name}' found but no valid material/name.") # Debug
                else:
                    # Parameter not found at all
                    skipped_no_param_count += 1
                    # print(f"# Skipping PanelType '{current_name}' (ID: {panel_type.Id}). Parameter '{material_param_name}' not found.") # Debug

        except System.Exception as proc_ex:
            # Log any errors during processing a specific panel type
            error_count += 1
            # Ensure current_name was captured before the error if possible
            print("# Error processing PanelType '{}' (ID: {}): {}".format(current_name, panel_type.Id, proc_ex.Message))

except System.Exception as col_ex:
    # Error during the collection phase
    print("# Error collecting PanelTypes: {}".format(col_ex.Message))
    error_count += 1

# Summary printing is disabled as per requirements for direct execution scripts.
# print("--- PanelType Renaming Summary ---")
# print("Total PanelTypes found: {}".format(processed_count))
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (Parameter '{}' not found): {}".format(material_param_name, skipped_no_param_count))
# print("Skipped (No valid material assigned/found): {}".format(skipped_no_material_count))
# print("Skipped (Already prefixed or no change): {}".format(skipped_already_prefixed_count))
# print("Errors encountered: {}".format(error_count))