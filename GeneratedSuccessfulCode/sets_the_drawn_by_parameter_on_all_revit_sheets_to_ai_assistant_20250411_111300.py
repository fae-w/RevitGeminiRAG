# Purpose: This script sets the 'Drawn By' parameter on all Revit sheets to 'AI Assistant'.

# Purpose: This script sets the "Drawn By" parameter on all Revit sheets to "AI Assistant".

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, BuiltInCategory, BuiltInParameter, Parameter

# Define the new value for the "Drawn By" parameter
new_drawn_by_value = "AI Assistant"

# Assuming "Drawn By" corresponds to the built-in parameter SHEET_DRAWN_BY
target_parameter_id = BuiltInParameter.SHEET_DRAWN_BY

# Collect all ViewSheet elements in the document
# Using OfClass(ViewSheet) is generally reliable for sheets
collector = FilteredElementCollector(doc).OfClass(ViewSheet)

# Iterate through the collected sheets
for sheet in collector:
    # Ensure the element is a valid ViewSheet
    if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet):
        try:
            # Get the 'Drawn By' parameter using the BuiltInParameter enum
            drawn_by_param = sheet.get_Parameter(target_parameter_id)

            # Check if the parameter exists and is not read-only
            if drawn_by_param and drawn_by_param.HasValue and not drawn_by_param.IsReadOnly:
                # Check if the current value is different to avoid unnecessary operations
                current_value = drawn_by_param.AsString()
                if current_value != new_drawn_by_value:
                    # Set the new parameter value
                    drawn_by_param.Set(new_drawn_by_value)
            # else: # Optional: Log skipped sheets
                # if not drawn_by_param:
                #     print("# Parameter 'Drawn By' not found for sheet ID: {}".format(sheet.Id))
                # elif drawn_by_param.IsReadOnly:
                #     print("# Parameter 'Drawn By' is read-only for sheet ID: {}".format(sheet.Id))
                # elif not drawn_by_param.HasValue:
                #      print("# Parameter 'Drawn By' has no value for sheet ID: {}".format(sheet.Id))
        except Exception as e:
            # print("# Error processing sheet ID {}: {}".format(sheet.Id, e)) # Optional: Log errors
            pass # Silently continue if an error occurs for a specific sheet

# No explicit output required, changes are made directly to the model elements.