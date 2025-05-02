# Purpose: This script calculates the total volume of concrete beams in a Revit model and generates a report.

# Purpose: This script calculates the total volume of concrete beams in a Revit model and generates a report.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilyInstance
from Autodesk.Revit.DB import BuiltInParameter
# Import necessary classes from the Structure namespace
from Autodesk.Revit.DB.Structure import StructuralMaterialType, StructuralType, StructuralMaterialTypeFilter

# Initialize counters
total_volume_cubic_feet = 0.0
beam_count = 0

# Create a filter for elements with Structural Material Type set to Concrete
# Note: This filters based on the instance's 'Structural Material Type' parameter
concrete_material_filter = StructuralMaterialTypeFilter(StructuralMaterialType.Concrete)

# Create a collector for Structural Framing elements
collector = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_StructuralFraming)\
    .WhereElementIsNotElementType()\
    .WherePasses(concrete_material_filter) # Apply the concrete material filter

# Iterate through the collected elements
for element in collector:
    # Double check if it's a FamilyInstance (collector should handle this, but good practice)
    if isinstance(element, FamilyInstance):
        # Optional check: Ensure the element's Structural Type is Beam
        # This helps exclude braces if they share the same category and material
        # Uncomment the following block if you strictly want only beams
        # structural_type = element.StructuralType
        # if structural_type != StructuralType.Beam:
        #     continue # Skip if not a beam

        try:
            # Get the volume parameter
            volume_param = element.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED)

            if volume_param and volume_param.HasValue:
                # Get volume in Revit's internal units (cubic feet)
                volume = volume_param.AsDouble()
                total_volume_cubic_feet += volume
                beam_count += 1
            else:
                # Optionally log elements without a volume parameter
                # print("# Element ID {} is a concrete beam but has no volume parameter.".format(element.Id))
                pass
        except Exception as e:
            # Log potential errors during parameter access for specific elements
            # print("# Error processing element ID {}: {}".format(element.Id, str(e)))
            pass # Continue to the next element

# Prepare the output report
output_lines = []
output_lines.append("Concrete Beam Report")
output_lines.append("====================")
output_lines.append("Total Count: {}".format(beam_count))
output_lines.append("Combined Volume: {:.2f} cubic feet".format(total_volume_cubic_feet)) # Format volume to 2 decimal places

# Use EXPORT format to send data back
file_content = "\n".join(output_lines)
print("EXPORT::TXT::concrete_beam_volume_report.txt")
print(file_content)

# If no beams were found, provide feedback
if beam_count == 0:
    print("# No concrete structural framing elements (beams) found in the project.")