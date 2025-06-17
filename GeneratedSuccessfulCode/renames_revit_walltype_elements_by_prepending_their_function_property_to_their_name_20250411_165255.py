# Purpose: This script renames Revit WallType elements by prepending their Function property to their name.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallType,
    WallKind, # Enum for checking wall type kind
    WallFunction, # Enum for checking wall function
    Element
)
# No need for .NET specific imports for this task

# --- Script Core Logic ---

# Collect all WallType elements
collector = FilteredElementCollector(doc).OfClass(WallType)

renamed_count = 0
skipped_count = 0
error_count = 0

# Iterate through WallTypes
for wall_type in collector:
    # Ensure it's a WallType (robustness check)
    if not isinstance(wall_type, WallType):
        continue

    # Check if it's a Basic Wall type
    if wall_type.Kind == WallKind.Basic:
        try:
            # Get the Function property (enum value)
            wall_function_enum = wall_type.Function

            # Convert the enum value to its string representation
            # Special handling might be needed if localization is a concern,
            # but ToString() usually gives the English enum name.
            function_str = wall_function_enum.ToString()

            # Get the current name of the wall type
            current_name = Element.Name.GetValue(wall_type) # Use Element.Name static method for safety

            # Construct the potential new name
            # Use " - " as a separator as shown in the example
            new_name = function_str + " - " + current_name

            # Check if renaming is actually needed (avoids unnecessary transaction entries)
            # Also prevents adding the prefix multiple times if script is run again
            prefix_check = function_str + " - "
            if current_name != new_name and not current_name.startswith(prefix_check):
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
                # print(f"# Skipping WallType '{current_name}' (ID: {wall_type.Id}). Already has prefix or matches new name.") # Debug
                skipped_count += 1

        except Exception as e:
            # General error handling for processing a specific wall type
            error_count += 1
            try:
                current_name_for_error = Element.Name.GetValue(wall_type)
            except:
                 current_name_for_error = f"ID: {wall_type.Id}" # Fallback if name access fails too
            # print(f"# Error processing WallType '{current_name_for_error}': {e}") # Debug

# Optional: Print summary (will appear in RevitPythonShell output window)
# print("--- Basic Wall Type Renaming Summary ---")
# print(f"Renamed: {renamed_count}")
# print(f"Skipped (already correct/no change): {skipped_count}")
# print(f"Errors: {error_count}")