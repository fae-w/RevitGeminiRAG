# Purpose: This script sets a material parameter on selected PanelType or WallType elements.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    Element,
    ElementType,
    Material,
    Parameter,
    StorageType,
    PanelType,
    WallType,
    BuiltInCategory # Keep for good practice
)
import System # For exception handling

# --- Configuration ---
target_material_name = "Aluminum Composite Material"
parameter_name_to_set = "Material" # Assuming a parameter named 'Material' exists on the type

# --- Helper Function to Find Material by Name ---
def find_material_id_by_name(doc, material_name):
    """Finds a material by name (case-insensitive) and returns its ElementId."""
    collector = FilteredElementCollector(doc).OfClass(Material)
    for mat in collector:
        if mat.Name.lower() == material_name.lower():
            return mat.Id
    return ElementId.InvalidElementId # Not found

# --- Pre-fetch Target Material ID ---
target_material_id = find_material_id_by_name(doc, target_material_name)

if target_material_id == ElementId.InvalidElementId:
    print("# Error: Target Material '{{}}' not found in the project. Cannot proceed.".format(target_material_name))
    # Exit or prevent modification if material not found
    target_material_id = None # Set to None to prevent attempts to set it

# --- Get Selection ---
try:
    selected_ids = uidoc.Selection.GetElementIds()
    if not selected_ids or selected_ids.Count == 0:
        print("# No elements are currently selected.")
        selected_ids = [] # Ensure it's an empty list for logic below
except System.Exception as e:
    print("# Error getting selection: {{}}".format(e))
    selected_ids = [] # Ensure it's an empty list on error

# --- Counters ---
processed_count = 0
changed_count = 0
skipped_not_type = 0
skipped_param_not_found = 0
skipped_param_readonly = 0
skipped_param_wrong_type = 0
skipped_already_target = 0
skipped_material_missing = 0 # Count skips due to target material missing
error_count = 0

# --- Process Selection ---
if target_material_id is not None and selected_ids:
    for elem_id in selected_ids:
        processed_count += 1
        element_type = None

        try:
            element = doc.GetElement(elem_id)
            if not element:
                skipped_not_type += 1 # Or treat as error? Treat as skip for now.
                continue

            # Check if the selected element is a Type (PanelType or WallType)
            # Note: ElementType is a base class. Checking specific types is safer.
            if isinstance(element, PanelType) or isinstance(element, WallType):
                element_type = element # It is a type we might process
            else:
                # Skip elements that are not PanelType or WallType
                skipped_not_type += 1
                # print("# Skipping selected element ID {} - Not a PanelType or WallType.".format(elem_id)) # Debug
                continue

            # We have a PanelType or WallType
            # Look for the parameter named 'Material'
            param = element_type.LookupParameter(parameter_name_to_set)

            if param:
                if param.IsReadOnly:
                    skipped_param_readonly += 1
                elif param.StorageType != StorageType.ElementId:
                    skipped_param_wrong_type += 1
                else:
                    current_value_id = param.AsElementId()
                    # Check if it's already the target material
                    if current_value_id == target_material_id:
                        skipped_already_target += 1
                    else:
                        # Set the parameter to the target material ID
                        set_result = param.Set(target_material_id)
                        if set_result:
                            changed_count += 1
                        else:
                            error_count += 1
                            try:
                                type_name = element_type.Name
                            except:
                                type_name = "ID: {}".format(elem_id)
                            print("# Error: Failed to set parameter '{{}}' for Type '{{}}'.".format(parameter_name_to_set, type_name))
            else:
                skipped_param_not_found += 1

        except System.Exception as proc_ex:
            error_count += 1
            print("# Error processing selected element ID {{}}: {{}}".format(elem_id, proc_ex.Message))

elif target_material_id is None and selected_ids:
    # Target material wasn't found initially, count all selected as skipped for this reason
    skipped_material_missing = len(selected_ids)
    processed_count = skipped_material_missing # All processed items resulted in this skip reason

# --- Summary ---
print("--- Change Material Parameter for Selected Types Summary ---")
print("Target Parameter Name: '{{}}'".format(parameter_name_to_set))
print("Target Material Name: '{{}}' ({{}})".format(target_material_name, "Found" if target_material_id is not None else "Not Found"))
print("Total Selected Elements Analyzed: {{}}".format(len(selected_ids) if selected_ids else 0))
print("PanelType/WallType Elements Processed: {{}}".format(processed_count - skipped_not_type))
print("Types Changed: {{}}".format(changed_count))
if skipped_material_missing > 0:
    print("Skipped (Target Material '{{}}' Not Found): {{}}".format(target_material_name, skipped_material_missing))
if skipped_already_target > 0:
    print("Skipped (Already Target Material): {{}}".format(skipped_already_target))
if skipped_not_type > 0:
    print("Skipped (Selected Element Not PanelType/WallType): {{}}".format(skipped_not_type))
if skipped_param_not_found > 0:
    print("Skipped (Parameter '{{}}' Not Found): {{}}".format(parameter_name_to_set, skipped_param_not_found))
if skipped_param_readonly > 0:
    print("Skipped (Parameter Read-Only): {{}}".format(skipped_param_readonly))
if skipped_param_wrong_type > 0:
    print("Skipped (Parameter Not Material/ElementId Type): {{}}".format(skipped_param_wrong_type))
if error_count > 0:
    print("Errors Encountered: {{}}".format(error_count))
print("--- Script Finished ---")
# Note: This script assumes the selected elements are Types (PanelType, WallType)
# and that they possess a writable parameter named 'Material' that accepts a Material ElementId.
# This might require a custom shared or project parameter setup on these types.