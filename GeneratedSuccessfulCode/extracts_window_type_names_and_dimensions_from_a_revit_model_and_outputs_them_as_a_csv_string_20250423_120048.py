# Purpose: This script extracts window type names and dimensions from a Revit model and outputs them as a CSV string.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilySymbol, BuiltInParameter, UnitUtils, UnitTypeId

# List to hold CSV lines
csv_lines = []
# Add header row - Assuming dimensions in millimeters based on example format '1200 x 1500'
csv_lines.append('"Window Type Name","Dimensions (mm Width x Height)"')

# Collect all FamilySymbol elements belonging to the OST_Windows category
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsElementType()

# Iterate through window types (FamilySymbols) and get data
for symbol in collector:
    if isinstance(symbol, FamilySymbol):
        try:
            type_name = symbol.Name

            # Get Type Width and Type Height parameters
            # Common BuiltInParameters for type dimensions are FAMILY_WIDTH_PARAM and FAMILY_HEIGHT_PARAM
            width_param = symbol.get_Parameter(BuiltInParameter.FAMILY_WIDTH_PARAM)
            height_param = symbol.get_Parameter(BuiltInParameter.FAMILY_HEIGHT_PARAM)

            dimensions_str = "N/A" # Default value if parameters are missing

            if width_param and height_param:
                width_internal = width_param.AsDouble() # Width in internal units (decimal feet)
                height_internal = height_param.AsDouble() # Height in internal units (decimal feet)

                # Convert dimensions from internal units (feet) to millimeters
                width_mm = UnitUtils.ConvertFromInternalUnits(width_internal, UnitTypeId.Millimeters)
                height_mm = UnitUtils.ConvertFromInternalUnits(height_internal, UnitTypeId.Millimeters)

                # Format the dimensions string as "Width x Height" with integer values
                dimensions_str = "{:.0f} x {:.0f}".format(width_mm, height_mm)
            # else: # Attempt fallback parameters if primary ones failed (less common for Type parameters)
            #    width_param_alt = symbol.get_Parameter(BuiltInParameter.WINDOW_WIDTH) # Often instance, but check type
            #    height_param_alt = symbol.get_Parameter(BuiltInParameter.WINDOW_HEIGHT) # Often instance, but check type
            #    if width_param_alt and height_param_alt:
            #       # ... repeat conversion and formatting ...
            #       pass

            # Escape quotes in type name for CSV safety
            safe_type_name = '"' + type_name.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_type_name, '"' + dimensions_str + '"'])) # Enclose dimension string in quotes too

        except Exception as e:
            # print("# Error processing Window Type {}: {}".format(symbol.Id, e)) # Optional: Log errors for debugging
            pass # Silently skip types that cause errors

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::window_type_dimensions.csv")
    print(file_content)
else:
    print("# No Window Type elements found or processed.")