# Purpose: This script renames Revit materials by replacing spaces in their names with underscores.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from System import Exception as SystemException
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Material,
    ElementId # Not directly used for renaming but good practice
)
import System # For ArgumentException

# --- Script Core Logic ---

renamed_count = 0
skipped_count = 0
error_count = 0
processed_count = 0

# Collect all Material elements in the project
try:
    collector = FilteredElementCollector(doc).OfClass(Material)
    materials_to_process = list(collector) # Convert iterator to list for stable processing if needed
    processed_count = len(materials_to_process)

    for material in materials_to_process:
        if not isinstance(material, Material):
            # This check is somewhat redundant with OfClass but provides extra safety
            continue

        try:
            current_name = material.Name

            if current_name and ' ' in current_name:
                # Replace all spaces with underscores
                new_name = current_name.replace(' ', '_')

                # Check if rename is actually needed (it should be if spaces were found)
                if current_name != new_name:
                    try:
                        # Rename the material
                        material.Name = new_name
                        renamed_count += 1
                        # print("# Renamed Material ID {} from '{}' to '{}'".format(material.Id, current_name, new_name)) # Debug
                    except System.ArgumentException as arg_ex:
                        # Handle potential duplicate name errors
                        error_count += 1
                        print("# Error renaming Material '{}' (ID: {}): New name '{}' might already exist or be invalid. {}".format(current_name, material.Id, new_name, arg_ex.Message))
                    except SystemException as rename_ex:
                        # Handle other potential errors during renaming
                        error_count += 1
                        print("# Error renaming Material '{}' (ID: {}): {}".format(current_name, material.Id, rename_ex.Message))
                else:
                     # This case should ideally not be hit if ' ' in current_name is true
                     skipped_count += 1
                     # print("# Skipped Material ID {}: Name '{}' unchanged after replacement.".format(material.Id, current_name)) # Debug
            else:
                # Name has no spaces or is empty/null
                skipped_count += 1
                # print("# Skipped Material ID {}: Name '{}' contains no spaces.".format(material.Id, current_name)) # Debug

        except SystemException as proc_ex:
            # Log any errors during processing a specific material (e.g., accessing Name failed)
            error_count += 1
            print("# Error processing Material ID {}: {}".format(material.Id, proc_ex.Message))

except SystemException as col_ex:
    print("# Error collecting materials: {}".format(col_ex.Message))
    error_count += 1 # Count collection error

# Optional: Print summary (commented out as per instructions against printing unless exporting)
# print("--- Material Renaming Summary ---")
# print("Total Materials found: {}".format(processed_count))
# print("Successfully renamed (spaces replaced): {}".format(renamed_count))
# print("Skipped (no spaces or no change): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))