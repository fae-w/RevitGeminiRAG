# Purpose: This script checks Revit family type names against a naming convention and reports non-compliant types.

# Purpose: This script checks if Revit family type names follow a specific naming convention (FamilyType_Description) and reports non-compliant types.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, ElementType, BuiltInCategory

# List to store non-compliant type names and reasons
non_compliant_types = []

# Collect all FamilySymbol elements (these represent the types within loadable families)
collector = FilteredElementCollector(doc).OfClass(FamilySymbol)

# Iterate through each FamilySymbol
for symbol in collector:
    if isinstance(symbol, FamilySymbol):
        try:
            type_name = symbol.Name
            family_name = symbol.Family.Name # Get family name for context

            # Check 1: Does the type name contain exactly one underscore?
            if type_name.count('_') != 1:
                non_compliant_types.append((family_name, type_name, "Name does not contain exactly one underscore '_'."))
                continue # Skip further checks for this type

            # Check 2: Does splitting by underscore result in exactly two non-empty parts?
            parts = type_name.split('_')
            if len(parts) != 2 or not parts[0] or not parts[1]:
                non_compliant_types.append((family_name, type_name, "Name does not have non-empty text before AND after the underscore."))
                continue # Skip to next type

            # If both checks pass, the name conforms to the basic structure 'Something_Something'

        except Exception as e:
            # Handle potential errors accessing properties, though unlikely for FamilySymbol
            # print(f"# Debug: Error processing symbol ID {symbol.Id}: {e}") # Escaped
            non_compliant_types.append(("Error Processing", "ID: {}".format(symbol.Id), str(e))) # Escaped format

# Prepare output for export
if non_compliant_types:
    output_lines = []
    output_lines.append("Family Type Naming Convention Check Results")
    output_lines.append("=========================================")
    output_lines.append("Expected Format: FamilyType_Description (must contain exactly one '_' with non-empty parts)")
    output_lines.append("")
    output_lines.append("The following Family Types do NOT conform:")
    output_lines.append("-" * 40)
    # Header for the table
    output_lines.append("{:<30} | {:<40} | {}".format("Family Name", "Type Name", "Reason")) # Escaped format
    output_lines.append("-" * 90) # Separator line based on estimated column widths

    # Sort results alphabetically by Family Name, then Type Name
    non_compliant_types.sort()

    # Add each non-compliant type to the output
    for fam_name, type_name, reason in non_compliant_types:
         # Basic formatting to align columns (adjust spacing if needed)
        output_lines.append("{:<30} | {:<40} | {}".format(fam_name, type_name, reason)) # Escaped format

    # Join lines into a single string
    file_content = "\n".join(output_lines)

    # Print the export header and the formatted data
    print("EXPORT::TXT::family_type_naming_check_report.txt")
    print(file_content)
else:
    # If the list is empty, all checked types conform
    print("# All checked Family Types conform to the 'FamilyType_Description' naming convention.")