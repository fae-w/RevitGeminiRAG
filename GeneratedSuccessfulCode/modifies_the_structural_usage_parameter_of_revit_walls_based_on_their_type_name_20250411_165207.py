# Purpose: This script modifies the structural usage parameter of Revit walls based on their type name.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    WallType,
    Element,
    ElementId
)
# Import necessary enum from Structure namespace
from Autodesk.Revit.DB.Structure import StructuralWallUsage

# --- Script Core Logic ---

# String to search for in the Wall Type name
search_string = "Shear Wall" # Case-sensitive search
# Target structural usage value
target_usage = StructuralWallUsage.Shear

# Collect all Wall instances in the document
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

modified_count = 0
skipped_count = 0
error_count = 0

# Iterate through Wall instances
for wall in collector:
    if not isinstance(wall, Wall):
        skipped_count += 1
        continue

    try:
        # Get the WallType ID associated with the wall instance
        wall_type_id = wall.GetTypeId()
        if wall_type_id == ElementId.InvalidElementId:
            skipped_count += 1
            # print(f"# Skipping Wall ID: {wall.Id}. Cannot get WallType ID.") # Debug
            continue

        # Get the WallType element
        wall_type = doc.GetElement(wall_type_id)
        if not isinstance(wall_type, WallType):
            skipped_count += 1
            # print(f"# Skipping Wall ID: {wall.Id}. Could not retrieve valid WallType for ID: {wall_type_id}.") # Debug
            continue

        # Get the name of the WallType
        type_name = Element.Name.GetValue(wall_type)

        # Check if the WallType name contains the search string
        if search_string in type_name:
            # Check if the current usage is already Shear
            current_usage = wall.StructuralUsage
            if current_usage != target_usage:
                try:
                    # Change the Structural Usage parameter
                    # Transaction is handled externally by C# wrapper
                    wall.StructuralUsage = target_usage
                    modified_count += 1
                    # print(f"# Modified Wall ID: {wall.Id}. Set StructuralUsage to Shear.") # Debug
                except Exception as modify_err:
                    error_count += 1
                    # print(f"# Error modifying Wall ID: {wall.Id}. Could not set StructuralUsage: {modify_err}") # Debug
            else:
                # Already set to Shear, skip modification
                skipped_count += 1
                # print(f"# Skipping Wall ID: {wall.Id}. Already set to Shear.") # Debug
        else:
            # Type name does not contain the search string
            skipped_count += 1
            # print(f"# Skipping Wall ID: {wall.Id}. Type Name '{type_name}' does not contain '{search_string}'.") # Debug

    except Exception as e:
        error_count += 1
        try:
            wall_id_for_error = wall.Id
        except:
            wall_id_for_error = "Unknown ID" # Fallback
        # print(f"# Error processing Wall with ID '{wall_id_for_error}': {e}") # Debug

# Optional: Print summary (will appear in RevitPythonShell output window)
# print("--- Wall Structural Usage Modification Summary ---")
# print(f"Modified: {modified_count}")
# print(f"Skipped (no match, already correct, or error getting type): {skipped_count}")
# print(f"Errors during modification/processing: {error_count}")