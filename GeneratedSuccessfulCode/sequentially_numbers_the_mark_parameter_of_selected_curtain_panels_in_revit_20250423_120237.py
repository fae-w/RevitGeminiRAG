# Purpose: This script sequentially numbers the 'Mark' parameter of selected curtain panels in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    Element,
    Panel,
    BuiltInParameter,
    Parameter,
    StorageType
)
from System.Collections.Generic import List
import System # For exception handling

# --- Configuration ---
mark_prefix = "CP-"
start_number = 1
padding_digits = 2 # e.g., 2 for 01, 02... 3 for 001, 002...

# --- Get Selection ---
selected_ids = []
try:
    selected_ids_collection = uidoc.Selection.GetElementIds()
    if selected_ids_collection and selected_ids_collection.Count > 0:
        # Convert to a standard Python list for easier sorting
        selected_ids = list(selected_ids_collection)
    else:
        print("# No elements are currently selected.")
except System.Exception as e:
    print("# Error getting selection: {}".format(e))

# --- Filter and Sort Selected Panels ---
panels_to_process = []
skipped_not_panel = 0
if selected_ids:
    for elem_id in selected_ids:
        try:
            element = doc.GetElement(elem_id)
            if element and isinstance(element, Panel):
                panels_to_process.append(element)
            elif element:
                skipped_not_panel += 1
            # Silently ignore if element is None (shouldn't happen with valid IDs)
        except System.Exception as e:
            print("# Error retrieving or checking element ID {}: {}".format(elem_id, e))
            skipped_not_panel += 1 # Count errors as skips

    # Sort panels by their ElementId for consistent numbering run-to-run
    panels_to_process.sort(key=lambda p: p.Id.IntegerValue)

# --- Process Filtered Panels ---
processed_count = 0
updated_count = 0
skipped_readonly = 0
skipped_no_param = 0
error_count = 0
current_number = start_number

if not panels_to_process:
    if selected_ids and skipped_not_panel == len(selected_ids):
        print("# Selection contained elements, but none were Curtain Panels.")
    elif not selected_ids:
        pass # Already printed "No elements selected"
    else:
        # This case might occur if filtering errors happened
        print("# No valid Curtain Panels found in the selection to process.")

else:
    print("# Found {} Curtain Panels in selection to process.".format(len(panels_to_process)))
    for panel in panels_to_process:
        processed_count += 1
        panel_id = panel.Id
        panel_name_info = panel.Name # Get type name for context if needed

        try:
            # Get the 'Mark' parameter
            mark_param = panel.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)

            if mark_param:
                if mark_param.IsReadOnly:
                    skipped_readonly += 1
                    print("# Skipping Panel ID {} (Type: '{}') - Mark parameter is read-only.".format(panel_id, panel_name_info))
                elif mark_param.StorageType != StorageType.String:
                     # Should not happen for Mark, but good practice
                     error_count += 1
                     print("# Error: Panel ID {} (Type: '{}') - Mark parameter is not a String type.".format(panel_id, panel_name_info))
                else:
                    # Format the new mark value
                    mark_value = "{}{:0{}}".format(mark_prefix, current_number, padding_digits)

                    # Set the parameter value (Transaction handled externally)
                    set_result = mark_param.Set(mark_value)

                    if set_result:
                        updated_count += 1
                        current_number += 1 # Increment only on successful update
                    else:
                        error_count += 1
                        print("# Error: Failed to set Mark parameter for Panel ID {} (Type: '{}'). Set method returned false.".format(panel_id, panel_name_info))
            else:
                skipped_no_param += 1
                print("# Skipping Panel ID {} (Type: '{}') - Mark parameter not found.".format(panel_id, panel_name_info))

        except System.Exception as proc_ex:
            error_count += 1
            print("# Error processing Panel ID {}: {}".format(panel_id, proc_ex.Message))

# --- Summary ---
print("--- Set Sequential Mark on Selected Curtain Panels Summary ---")
print("Prefix: '{}'".format(mark_prefix))
print("Starting Number: {}".format(start_number))
print("Total Selected Elements: {}".format(len(selected_ids)))
print("Curtain Panels Found in Selection: {}".format(len(panels_to_process)))
print("Successfully Updated Marks: {}".format(updated_count))
if updated_count > 0:
    last_mark = "{}{:0{}}".format(mark_prefix, current_number - 1, padding_digits)
    print("  (Last Mark Assigned: '{}')".format(last_mark))
print("Skipped (Not a Panel): {}".format(skipped_not_panel))
print("Skipped (Mark Parameter Not Found): {}".format(skipped_no_param))
print("Skipped (Mark Parameter Read-Only): {}".format(skipped_readonly))
print("Errors Encountered: {}".format(error_count))
print("--- Script Finished ---")