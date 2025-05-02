# Purpose: This script identifies and lists basic wall types with an undefined function parameter in a Revit model.

# Purpose: This script identifies and lists all basic wall types in a Revit model that have an undefined 'Function' parameter, exporting the results to a text file.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WallType,
    WallKind, # Enum for checking wall type kind
    WallFunction # Enum for checking wall function
)

# List to store names of WallTypes with undefined function
undefined_function_types = []

# Collect all WallType elements
collector = FilteredElementCollector(doc).OfClass(WallType)

# Iterate through WallTypes
for wall_type in collector:
    # Check if it's a Basic Wall type
    if wall_type.Kind == WallKind.Basic:
        try:
            # Get the Function property
            # This directly accesses the enum value for the wall type's function
            wall_function = wall_type.Function

            # Check if the function is Undefined
            if wall_function == WallFunction.Undefined:
                undefined_function_types.append(wall_type.Name)
        except Exception as e:
            # print(f"# Debug: Error processing WallType {wall_type.Name} (ID: {wall_type.Id}): {e}") # Escaped
            # Silently skip types that cause errors, although unlikely for this property
            pass

# Prepare the output
if undefined_function_types:
    output_lines = []
    output_lines.append("Basic Wall Types with Undefined Function")
    output_lines.append("=======================================")
    # Sort for consistent output
    undefined_function_types.sort()
    output_lines.extend(undefined_function_types)
    file_content = "\n".join(output_lines)

    # Print the export header and data
    print("EXPORT::TXT::undefined_wall_function_types.txt")
    print(file_content)
else:
    print("# All Basic Wall types found have a defined Function (not Undefined).")