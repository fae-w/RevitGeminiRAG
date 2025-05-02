# Purpose: This script updates the material of curtain wall panel types based on a specified parameter.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often needed, included for safety
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallType,
    WallKind,
    Material,
    ElementId,
    Element,
    Parameter,
    StorageType,
    # BuiltInParameter, # Not needed with simplified find function
    # ParameterFilterRuleFactory, # Not needed with simplified find function
    # ElementParameterFilter, # Not needed with simplified find function
    BuiltInCategory # Keep for good practice, though not strictly used now
)
import System # For exception handling

# Accessing pre-defined variables (assuming they exist in the execution context)
# doc = __revit__.ActiveUIDocument.Document # Example if not pre-defined

# --- Configuration ---
target_param_name = "Panel Material" # The name of the parameter on the Wall Type to check/update
current_material_name = "Default"    # The name of the material to replace
new_material_name = "Glass - Insulated" # The name of the material to set

# --- Helper Function to Find Material by Name (Simplified) ---
def find_material_id_by_name(doc, material_name):
    """Finds a material by name (case-insensitive) and returns its ElementId."""
    collector = FilteredElementCollector(doc).OfClass(Material)
    # Iterate and compare names directly (case-insensitive)
    for mat in collector:
        if mat.Name.lower() == material_name.lower():
            return mat.Id
    return ElementId.InvalidElementId # Not found

# --- Pre-fetch Material IDs ---
default_material_id = find_material_id_by_name(doc, current_material_name)
new_material_id = find_material_id_by_name(doc, new_material_name)

# Check if materials were found
if default_material_id == ElementId.InvalidElementId:
    print("# Error: Material '{}' not found in the project. Cannot proceed.".format(current_material_name))
    default_material_id = None # Ensure comparisons fail later

if new_material_id == ElementId.InvalidElementId:
    print("# Error: Material '{}' not found in the project. Cannot proceed.".format(new_material_name))
    new_material_id = None # Ensure no updates happen

# --- Script Core Logic ---
updated_count = 0
skipped_no_param = 0
skipped_param_readonly = 0
skipped_param_wrong_type = 0
skipped_not_default = 0
skipped_material_missing = 0 # Count skips due to Default or New material missing
error_count = 0
processed_count = 0

# Only proceed if both materials were found
if default_material_id is not None and new_material_id is not None:
    try:
        # Collect all WallType elements
        collector = FilteredElementCollector(doc).OfClass(WallType)

        for wall_type in collector:
            # Check if it's a Curtain Wall type
            try:
                if wall_type.Kind != WallKind.Curtain:
                    continue
            except System.Exception as kind_ex:
                # Handle potential issues accessing Kind (e.g., invalid wall type)
                # print("# Warning: Could not determine Kind for WallType ID {}: {}".format(wall_type.Id, kind_ex.Message))
                continue # Skip this type if Kind cannot be determined

            processed_count += 1
            wall_type_name = "Unknown" # Default in case of error getting name
            try:
                # Attempt to get the name using the Name property
                wall_type_name = wall_type.Name
                if not wall_type_name: wall_type_name = "Unnamed WallType ID: {}".format(wall_type.Id)

                # Assumption: A parameter named 'Panel Material' exists directly on the WallType.
                # This might be a custom/project parameter.
                param = wall_type.LookupParameter(target_param_name)

                if param:
                    if param.IsReadOnly:
                        skipped_param_readonly += 1
                    elif param.StorageType != StorageType.ElementId:
                        skipped_param_wrong_type += 1
                    else:
                        current_value_id = param.AsElementId()
                        # Check if the current value is the 'Default' material ID
                        if current_value_id == default_material_id:
                            # Set the parameter to the 'New' material ID (Transaction handled externally)
                            set_result = param.Set(new_material_id)
                            if set_result:
                                updated_count += 1
                            else:
                                error_count += 1
                                print("# Error: Failed to set parameter '{}' for WallType '{}' (ID: {}).".format(target_param_name, wall_type_name, wall_type.Id))
                        else:
                            skipped_not_default += 1
                else:
                    skipped_no_param += 1

            except System.Exception as proc_ex:
                error_count += 1
                # Attempt to get name for error message even if previous attempt failed
                try:
                     wall_type_name_err = wall_type.Name if wall_type else "Unknown"
                     if not wall_type_name_err: wall_type_name_err = "ID: {}".format(wall_type.Id)
                except:
                     wall_type_name_err = "ID: {}".format(wall_type.Id if wall_type else "Unknown")
                print("# Error processing WallType '{}': {}".format(wall_type_name_err, proc_ex.Message))

    except System.Exception as col_ex:
        # Error during the collection phase
        print("# Error collecting WallTypes: {}".format(col_ex.Message))
        error_count += 1
else:
    # Log that we skipped processing because materials weren't found
    # Count the number of Curtain Wall Types
    temp_collector = FilteredElementCollector(doc).OfClass(WallType)
    count = 0
    for wt in temp_collector:
        try:
            if wt.Kind == WallKind.Curtain:
                count += 1
        except Exception:
             # Handle potential issues accessing Kind property
             pass
    skipped_material_missing = count
    if skipped_material_missing > 0:
        print("# Skipping all {} Curtain Wall Types because '{}' or '{}' material was not found.".format(skipped_material_missing, current_material_name, new_material_name))
    else:
         print("# No Curtain Wall Types found to process.")


# Summary printing (optional, useful for pyRevit/RPS)
print("--- Curtain Wall Type 'Panel Material' Update Summary ---")
print("Searched Parameter Name: '{}'".format(target_param_name))
print("Current Material Name Target: '{}'".format(current_material_name))
print("New Material Name Target: '{}'".format(new_material_name))
print("Total Curtain Wall Types Checked: {}".format(processed_count))
print("Successfully Updated: {}".format(updated_count))
# Only show skipped_material_missing if it's > 0 and materials were actually missing
if (default_material_id is None or new_material_id is None) and skipped_material_missing > 0:
    print("Skipped (Required Material Not Found): {}".format(skipped_material_missing))
print("Skipped (Parameter Not Found): {}".format(skipped_no_param))
print("Skipped (Parameter Read-Only): {}".format(skipped_param_readonly))
print("Skipped (Parameter Wrong Type): {}".format(skipped_param_wrong_type))
print("Skipped (Parameter Not '{}'): {}".format(current_material_name, skipped_not_default))
print("Errors Encountered: {}".format(error_count))
print("--- Script Finished ---")

# Note: This script assumes the parameter 'Panel Material' exists directly on the WallType
# and is intended to store a Material ID. This might be a custom parameter.
# Standard Revit Curtain Walls use a 'Curtain Panel' type parameter (BuiltInParameter.CURTAIN_WALL_PANELS)
# which links to a Panel Family Type (e.g., 'System Panel: Glazed').
# Modifying the material *within* that Panel Type requires a different approach.