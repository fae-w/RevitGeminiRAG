# Purpose: This script updates the 'Drawn By' parameter of a specific Revit sheet.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, BuiltInParameter
import System # For exception handling

# --- Configuration ---
target_sheet_number = 'G-001'
new_drawn_by_value = 'Automation Script'
target_parameter_bip = BuiltInParameter.SHEET_DRAWN_BY

# --- Main Logic ---
sheet_found = False
sheet_updated = False
error_message = None

# Collect all ViewSheet elements in the document
collector = FilteredElementCollector(doc).OfClass(ViewSheet)

# Iterate through the collected sheets
for sheet in collector:
    # Ensure the element is a valid ViewSheet
    if not isinstance(sheet, ViewSheet):
        continue

    # Check if the current sheet number matches the target
    if sheet.SheetNumber == target_sheet_number:
        sheet_found = True
        try:
            # Get the 'Drawn By' parameter using the BuiltInParameter enum
            drawn_by_param = sheet.get_Parameter(target_parameter_bip)

            # Check if the parameter exists and is not read-only
            if drawn_by_param and not drawn_by_param.IsReadOnly:
                # Check if the current value is different to avoid unnecessary operations
                current_value = drawn_by_param.AsString()
                if current_value != new_drawn_by_value:
                    # Set the new parameter value
                    drawn_by_param.Set(new_drawn_by_value)
                    sheet_updated = True
                    print("# Set 'Drawn By' parameter of sheet '{}' to '{}'.".format(target_sheet_number, new_drawn_by_value))
                else:
                    # Value is already correct
                    print("# 'Drawn By' parameter of sheet '{}' is already '{}'.".format(target_sheet_number, new_drawn_by_value))
                    sheet_updated = False # No change was made
            elif not drawn_by_param:
                error_message = "# Error: Parameter 'Drawn By' (BIP: {}) not found for sheet '{}'.".format(target_parameter_bip, target_sheet_number)
            elif drawn_by_param.IsReadOnly:
                error_message = "# Error: Parameter 'Drawn By' is read-only for sheet '{}'.".format(target_sheet_number)
            # Consider HasValue check if Set causes issues on null parameters
            # elif not drawn_by_param.HasValue:
            #     error_message = "# Error: Parameter 'Drawn By' has no value assigned yet for sheet '{}'.".format(target_sheet_number)

        except System.Exception as e:
            error_message = "# An unexpected error occurred while processing sheet '{}': {}".format(target_sheet_number, e)

        # Stop searching once the target sheet is found and processed
        break

# --- Report Final Status ---
if not sheet_found:
    print("# Error: Sheet with number '{}' was not found in the project.".format(target_sheet_number))
elif error_message:
    # Print specific error encountered during parameter setting
    print(error_message)
# elif sheet_updated: # Success message printed inside the loop
    # pass
# elif not sheet_updated and sheet_found: # Message for no change needed printed inside loop
    # pass