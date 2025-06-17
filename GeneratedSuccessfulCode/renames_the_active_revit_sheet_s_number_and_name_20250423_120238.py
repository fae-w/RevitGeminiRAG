# Purpose: This script renames the active Revit sheet's number and name.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ViewSheet, BuiltInParameter
import System # Required for exception handling

# --- Configuration ---
new_sheet_number = 'A-201'
new_sheet_name = 'L2 Reflected Ceiling Plan'

# --- Main Logic ---
active_view = doc.ActiveView

# Check if the active view is a sheet
if active_view is not None and isinstance(active_view, ViewSheet):
    sheet = active_view
    sheet_updated = False
    error_messages = []

    # Try setting the Sheet Number
    try:
        # Check if the number needs changing
        if sheet.SheetNumber != new_sheet_number:
            sheet.SheetNumber = new_sheet_number
            sheet_updated = True
            print("# Set Sheet Number to: '{}'".format(new_sheet_number))
        else:
            print("# Sheet Number is already '{}'.".format(new_sheet_number))
    except System.ArgumentException as ex:
        error_messages.append("# Error setting Sheet Number: {}. The number '{}' might be invalid or already in use.".format(ex.Message, new_sheet_number))
    except Exception as ex:
        error_messages.append("# An unexpected error occurred while setting Sheet Number: {}".format(ex))

    # Try setting the Sheet Name
    try:
        # Check if the name needs changing
        if sheet.Name != new_sheet_name:
             # Use the Name property directly if available and preferred
             sheet.Name = new_sheet_name
             sheet_updated = True
             print("# Set Sheet Name to: '{}'".format(new_sheet_name))
            # Alternatively, use the parameter if Name property gives issues (less common)
            # name_param = sheet.get_Parameter(BuiltInParameter.SHEET_NAME)
            # if name_param and not name_param.IsReadOnly:
            #     if name_param.AsString() != new_sheet_name:
            #         name_param.Set(new_sheet_name)
            #         sheet_updated = True
            #         print("# Set Sheet Name parameter to: '{}'".format(new_sheet_name))
            #     else:
            #         print("# Sheet Name is already '{}'.".format(new_sheet_name))
            # elif not name_param:
            #      error_messages.append("# Could not find the Sheet Name parameter.")
            # elif name_param.IsReadOnly:
            #      error_messages.append("# Sheet Name parameter is read-only.")
        else:
             print("# Sheet Name is already '{}'.".format(new_sheet_name))

    except System.ArgumentException as ex:
        error_messages.append("# Error setting Sheet Name: {}. The name '{}' might be invalid.".format(ex.Message, new_sheet_name))
    except Exception as ex:
        error_messages.append("# An unexpected error occurred while setting Sheet Name: {}".format(ex))

    # Report results
    if not error_messages:
        if sheet_updated:
            print("# Successfully updated active sheet properties.")
        else:
            print("# Active sheet properties already matched the target values. No changes made.")
    else:
        for msg in error_messages:
            print(msg)
        print("# Could not fully update sheet properties due to errors.")

elif active_view is None:
    print("# Error: There is no active view.")
else:
    print("# Error: The active view ('{}') is not a sheet. It is a '{}'.".format(active_view.Name, active_view.GetType().Name))