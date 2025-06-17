# Purpose: This script extracts Element ID and Mark values from structural columns in a Revit model and outputs them to a text file.

# Purpose: This script extracts the Element ID and Mark value of structural columns in a Revit model and formats the output for export to a text file.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    ElementId,
    BuiltInParameter,
    Element
)
# Import the Structure namespace to access the StructuralType enum
from Autodesk.Revit.DB import Structure

# List to hold the output lines
output_lines = []
# Add header row
output_lines.append("Element ID,Mark Value")

# Collect all FamilyInstance elements that are Structural Columns
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType()

# Iterate through the collected elements
for element in collector:
    # Ensure the element is a FamilyInstance and is specifically a Column type structurally
    if isinstance(element, FamilyInstance):
        try:
            # Verify its StructuralType is Column
            if element.StructuralType == Structure.StructuralType.Column:
                element_id_str = element.Id.ToString()

                # Get the 'Mark' parameter
                mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)

                mark_value = "" # Default to empty string if parameter doesn't exist or has no value
                if mark_param and mark_param.HasValue:
                    mark_value_raw = mark_param.AsString()
                    # Ensure AsString() didn't return None or an empty string before assigning
                    if mark_value_raw:
                        mark_value = mark_value_raw
                        # Basic handling for potential commas in mark value if exporting as CSV later,
                        # but for TXT, just keep the raw value. If CSV were intended, use quotes.
                        # mark_value = '"{}"'.format(mark_value_raw.replace('"', '""'))

                # Append the formatted string: "ElementID,MarkValue"
                output_lines.append("{},{}".format(element_id_str, mark_value))

        except AttributeError:
            # Some elements in the category might not have the StructuralType property (unlikely for columns, but safe to check)
            # print("# Debug: Skipping element {} - Does not have StructuralType property.".format(element.Id)) # Escaped
            pass
        except Exception as e:
            # Catch other potential errors during processing
            # print("# Debug: Error processing element {}: {}".format(element.Id, e)) # Escaped
            pass # Continue with the next element

# Check if any column data was collected
if len(output_lines) > 1: # More than just the header
    # Format the final output string for export
    file_content = "\n".join(output_lines)
    # Print the export header and data
    print("EXPORT::TXT::structural_column_marks.txt")
    print(file_content)
else:
    # Print a message if no structural columns were found or processed
    print("# No structural columns found or processed in the document.")