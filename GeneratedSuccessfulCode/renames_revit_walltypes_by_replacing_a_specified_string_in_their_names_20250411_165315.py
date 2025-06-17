# Purpose: This script renames Revit WallTypes by replacing a specified string in their names.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallType,
    Element
)

# --- Script Core Logic ---

# String to find and replace
string_to_find = 'Generic'
string_to_replace = 'GEN'

# Collect all WallType elements
collector = FilteredElementCollector(doc).OfClass(WallType)

renamed_count = 0
skipped_count = 0
error_count = 0

# Iterate through WallTypes
for wall_type in collector:
    # Ensure it's a WallType (robustness check, though OfClass should handle this)
    if not isinstance(wall_type, WallType):
        skipped_count += 1
        continue

    try:
        # Get the current name of the wall type using the safer static method
        current_name = Element.Name.GetValue(wall_type)

        # Check if the string to find is in the current name
        if string_to_find in current_name:
            # Create the potential new name
            new_name = current_name.replace(string_to_find, string_to_replace)

            # Check if renaming is actually needed (avoids unnecessary transaction entries)
            if new_name != current_name:
                try:
                    # Rename the wall type (Transaction handled externally by C# wrapper)
                    wall_type.Name = new_name
                    renamed_count += 1
                    # print(f"# Renamed '{current_name}' to '{new_name}'") # Debug
                except Exception as rename_err:
                    # Handle potential errors during renaming (e.g., duplicate names)
                    error_count += 1
                    # print(f"# Error renaming WallType '{current_name}' (ID: {wall_type.Id}) to '{new_name}': {rename_err}") # Debug
            else:
                # Name contains 'Generic' but replacing results in the same name (unlikely here but possible)
                # Or it might have already been renamed if script is run multiple times, though the check avoids re-applying
                skipped_count += 1
                # print(f"# Skipping WallType '{current_name}' (ID: {wall_type.Id}). Replace results in no change.") # Debug
        else:
            # Name does not contain 'Generic'
            skipped_count += 1
            # print(f"# Skipping WallType '{current_name}' (ID: {wall_type.Id}). Does not contain '{string_to_find}'.") # Debug

    except Exception as e:
        # General error handling for processing a specific wall type (e.g., accessing name)
        error_count += 1
        try:
            element_id_for_error = wall_type.Id
        except:
             element_id_for_error = "Unknown ID" # Fallback
        # print(f"# Error processing WallType with ID '{element_id_for_error}': {e}") # Debug

# Optional: Print summary (will appear in RevitPythonShell output window)
# print("--- Wall Type Renaming Summary ('{}' -> '{}') ---".format(string_to_find, string_to_replace))
# print(f"Renamed: {renamed_count}")
# print(f"Skipped (no change needed or no '{string_to_find}'): {skipped_count}")
# print(f"Errors: {error_count}")