# Purpose: This script updates a specified parameter for Revit elements based on their element ID and phase.

﻿# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    ElementId,
    Element,
    Parameter,
    BuiltInParameter,
    StorageType,
    Phase
)
import System # For exception handling and parsing

# --- Configuration ---
input_data_string = """ID,Status
44444,Reviewed
55555,Issue Found
66666,Approved"""
target_phase_name = "New Construction"
status_parameter_name = "Status" # The name of the parameter to update

# --- Data Parsing ---
updates_to_process = []
errors_parsing = []
lines = input_data_string.strip().splitlines()

if len(lines) > 1: # Check if there's data beyond the header
    header = lines[0].strip()
    if header.lower() != "id,status":
        errors_parsing.append("# Warning: Input header does not match 'ID,Status'. Processing anyway assuming format ID,Value.")

    for i, line in enumerate(lines[1:]): # Skip header
        line = line.strip()
        if not line: continue # Skip empty lines

        parts = line.split(',', 1) # Split only once
        if len(parts) == 2:
            id_str = parts[0].strip()
            status_val = parts[1].strip()
            try:
                element_id_int = int(id_str)
                updates_to_process.append({"id": element_id_int, "status": status_val, "line_num": i + 2})
            except ValueError:
                errors_parsing.append("# Error parsing line {}: Invalid Element ID '{}'".format(i + 2, id_str))
        else:
            errors_parsing.append("# Error parsing line {}: Incorrect format '{}'. Expected 'ID,Status'".format(i + 2, line))
else:
    errors_parsing.append("# Error: No data rows found in the input string.")


# --- Main Logic ---
update_summary = []
error_messages = []

# Print parsing errors first
if errors_parsing:
    error_messages.extend(errors_parsing)
    error_messages.append("---") # Separator

if not updates_to_process:
    error_messages.append("No valid update instructions parsed.")
else:
    for update_info in updates_to_process:
        element_id_int = update_info["id"]
        new_status = update_info["status"]
        line_num = update_info["line_num"]

        try:
            target_element_id = ElementId(element_id_int)
            element = doc.GetElement(target_element_id)

            if element:
                # 1. Check Phase Created parameter
                phase_param = element.get_Parameter(BuiltInParameter.PHASE_CREATED)
                phase_matches = False
                phase_name_actual = "Not Found/Invalid"

                if phase_param and phase_param.HasValue:
                    phase_id = phase_param.AsElementId()
                    if phase_id and phase_id != ElementId.InvalidElementId:
                        phase_element = doc.GetElement(phase_id)
                        if isinstance(phase_element, Phase):
                             phase_name_actual = phase_element.Name
                             if phase_name_actual == target_phase_name:
                                 phase_matches = True
                        else:
                             error_messages.append("ID {}: Phase ID {} does not belong to a Phase element.".format(element_id_int, phase_id.IntegerValue))
                    else:
                         error_messages.append("ID {}: Invalid Phase ID found in Phase Created parameter.".format(element_id_int))
                else:
                     error_messages.append("ID {}: Phase Created parameter not found or has no value.".format(element_id_int))

                # 2. Update Status parameter if phase matches
                if phase_matches:
                    status_param = element.LookupParameter(status_parameter_name)

                    if status_param:
                        if status_param.IsReadOnly:
                            error_messages.append("ID {}: Parameter '{}' is read-only.".format(element_id_int, status_parameter_name))
                        elif status_param.StorageType != StorageType.String:
                             error_messages.append("ID {}: Parameter '{}' is not a Text parameter (Actual type: {}). Cannot set string value.".format(element_id_int, status_parameter_name, status_param.StorageType))
                        else:
                            try:
                                set_result = status_param.Set(new_status)
                                if set_result:
                                    update_summary.append("ID {}: Successfully updated '{}' to '{}' (Phase: '{}').".format(element_id_int, status_parameter_name, new_status, phase_name_actual))
                                else:
                                    error_messages.append("ID {}: Failed to set parameter '{}' to '{}'. Check value validity/constraints.".format(element_id_int, status_parameter_name, new_status))
                            except Exception as set_ex:
                                error_messages.append("ID {}: Error setting parameter '{}': {}".format(element_id_int, status_parameter_name, str(set_ex)))
                    else:
                        error_messages.append("ID {}: Parameter '{}' not found.".format(element_id_int, status_parameter_name))
                else:
                     # Phase did not match, report it clearly unless an error already occured finding the phase
                     if "ID {}:".format(element_id_int) not in " ".join(error_messages[-3:]): # Avoid duplicate reporting if phase error already logged
                        update_summary.append("ID {}: Skipped update. Phase Created ('{}') does not match target ('{}').".format(element_id_int, phase_name_actual, target_phase_name))

            else:
                error_messages.append("ID {}: Element not found in the document (Referenced on input line {}).".format(element_id_int, line_num))

        except System.Exception as ex:
            error_messages.append("ID {}: An unexpected error occurred: {}".format(element_id_int, str(ex)))

# --- Final Output ---
print("--- Element Status Update Summary ---")
if update_summary:
    for msg in update_summary:
        print(msg)
else:
    print("# No elements were updated or met the criteria.")

if error_messages:
    print("\n--- Errors/Warnings ---")
    for msg in error_messages:
        print(msg)