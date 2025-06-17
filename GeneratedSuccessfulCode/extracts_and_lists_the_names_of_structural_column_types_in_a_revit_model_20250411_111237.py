# Purpose: This script extracts and lists the names of structural column types in a Revit model.

# Purpose: This script extracts and lists the names of all structural column types used in a Revit model.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilyInstance, Element
# Import the Structure namespace to access the StructuralType enum
from Autodesk.Revit.DB import Structure

# Set to store unique type names
column_type_names = set()

# Collect all FamilyInstance elements that are Structural Columns
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType()

# Iterate through the collected elements
for element in collector:
    # Ensure the element is a FamilyInstance (though collector likely ensures this)
    if isinstance(element, FamilyInstance):
        try:
            # Check if the structural type is Column (use qualified name: Structure.StructuralType.Column)
            if element.StructuralType == Structure.StructuralType.Column:
                # Get the FamilySymbol (the type) of the instance
                symbol = element.Symbol # element.Symbol gives the FamilySymbol (type)
                if symbol:
                    # Add the type name to the set
                    column_type_names.add(symbol.Name)
        except Exception as e:
            # print(f"# Debug: Error processing element {{element.Id}}: {{e}}") # Escaped
            pass # Ignore elements that cause errors (e.g., don't have StructuralType property)

# Check if any column types were found
if column_type_names:
    # Sort the names alphabetically for better readability
    sorted_names = sorted(list(column_type_names))

    # Format the output string
    output_lines = []
    output_lines.append("Structural Column Type Names")
    output_lines.append("============================")
    output_lines.extend(sorted_names)
    file_content = "\n".join(output_lines)

    # Print the export header and data
    print("EXPORT::TXT::structural_column_type_names.txt")
    print(file_content)
else:
    print("# No structural columns found in the document.")