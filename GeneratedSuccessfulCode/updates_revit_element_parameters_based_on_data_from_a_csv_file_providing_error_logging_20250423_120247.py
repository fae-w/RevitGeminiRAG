# Purpose: This script updates Revit element parameters based on data from a CSV file, providing error logging.

﻿# IronPython script for Revit - Update Parameters from CSV Data with Error Logging (Manual CSV Parsing)

import clr
import System

clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often useful, though not strictly needed for this specific logic yet
clr.AddReference('System')

# Import everything from DB namespace - often more reliable in IronPython for resolving specific types
from Autodesk.Revit.DB import *

# --- Configuration ---
# Assume 'doc' variable is pre-defined and represents the active Revit Document
# Assume input CSV data is provided as a string variable 'csv_data'
# Note: Transactions (t.Start(), t.Commit()) are handled externally by the C# wrapper

csv_data = """ID,LengthParam,StatusText
55555,1500,OK
66666,NA,Failed
77777,2000,OK"""

# --- Script ---

error_log = []
processed_rows = 0
updated_params_count = 0

# Manual CSV Parsing
lines = csv_data.strip().split('\n')

if not lines or not lines[0].strip():
    print("Error: CSV data is empty or missing header.")
else:
    header_line = lines[0]
    header = [h.strip() for h in header_line.split(',')]
    data_lines = lines[1:]

    # Find the index of the ID column (case-insensitive check)
    id_col_name = 'ID'
    id_col_index = -1
    for i, col_name in enumerate(header):
        if col_name.strip().upper() == id_col_name.upper():
            id_col_index = i
            break

    if id_col_index == -1:
        print("Error: '{0}' column not found in CSV header.".format(id_col_name))
        header = None # Prevent further processing

    if header:
        for row_index, line in enumerate(data_lines):
            row_num = row_index + 2 # Start counting data rows after header (Row 1 is header)
            processed_rows += 1

            if not line.strip(): # Skip empty lines
                continue

            row_values = [val.strip() for val in line.split(',')]

            if len(row_values) != len(header):
                error_log.append("Row {0}: Incorrect number of columns (expected {1}, got {2}). Skipping row: '{3}'".format(row_num, len(header), len(row_values), line))
                continue

            element_id_str = row_values[id_col_index].strip()
            element = None

            # --- 1. Get Element by ID ---
            try:
                element_id_long = System.Int64.Parse(element_id_str)
                element_id = ElementId(element_id_long)
                element = doc.GetElement(element_id)

                if not element:
                     error_log.append("Row {0}: Element with ID {1} not found.".format(row_num, element_id_str))
                     continue # Skip to next row if element not found
            except System.FormatException: # Handles non-integer strings for Int64.Parse
                error_log.append("Row {0}: Invalid Element ID format '{1}'. Must be an integer.".format(row_num, element_id_str))
                continue # Skip to next row if ID is invalid format
            except Autodesk.Revit.Exceptions.ArgumentException: # Handles invalid ElementId value (e.g., -1)
                 error_log.append("Row {0}: Element ID '{1}' is invalid or does not correspond to a valid element.".format(row_num, element_id_str))
                 continue
            except Exception as e:
                 error_log.append("Row {0}: Error retrieving element with ID {1}: {2}".format(row_num, element_id_str, str(e)))
                 continue # Skip to next row on other errors

            # --- 2. Process Parameters for the Element ---
            for i, param_name in enumerate(header):
                if i == id_col_index: # Skip the ID column itself
                    continue

                param_name = param_name.strip()
                value_str = row_values[i].strip() # Get value and remove leading/trailing whitespace

                if not param_name:
                    error_log.append("Row {0}: Element ID {1}: Empty parameter name found in header column {2}.".format(row_num, element_id_str, i + 1))
                    continue

                # --- 2a. Find Parameter on Element ---
                param = element.LookupParameter(param_name)

                # If not found by name, try finding common Built-in Parameters (case-insensitive check)
                if not param:
                    try:
                        # Attempt to parse as BuiltInParameter enum value
                        bip_enum_str = param_name.replace(" ", "_").upper() # Basic formatting attempt
                        # Use Enum.TryParse for safer parsing in potentially different .NET versions
                        found, bip_val = System.Enum.TryParse[BuiltInParameter](bip_enum_str, True, None) # Case-insensitive parse
                        if found and bip_val is not None and int(bip_val) != int(BuiltInParameter.INVALID): # Check it's a valid BIP value
                           param = element.get_Parameter(bip_val)
                    except System.ArgumentException:
                         # Enum parse failed (invalid name), ignore and proceed
                         pass
                    except Exception as bip_ex:
                         # Catch other potential errors during BIP lookup
                         # error_log.append("Row {0}: Element ID {1}: Minor error checking BuiltInParameter for '{2}': {3}".format(row_num, element_id_str, param_name, str(bip_ex)))
                         pass

                if not param:
                    error_log.append("Row {0}: Element ID {1}: Parameter '{2}' not found.".format(row_num, element_id_str, param_name))
                    continue # Skip to next parameter

                if param.IsReadOnly:
                    # Optional: Log read-only skips if needed
                    # error_log.append("Row {0}: Element ID {1}: Parameter '{2}' is read-only. Cannot update.".format(row_num, element_id_str, param_name))
                    continue # Skip read-only parameters

                # --- 2b. Set Parameter Value with Type Handling ---
                storage_type = param.StorageType
                try:
                    if value_str.upper() == 'NA' or value_str == '': # Handle common non-value entries before type conversion
                         # Decide whether to clear the parameter or log an error/skip
                         # For this example, we'll log and skip if it's not a String type that can accept "NA"
                         if storage_type != StorageType.String:
                             error_log.append("Row {0}: Element ID {1}: Cannot set non-text parameter '{2}' with value '{3}'. Skipping.".format(row_num, element_id_str, param_name, value_str))
                             continue
                         # If it's a string type, allow setting "NA" or empty string
                         param.Set(value_str)
                         updated_params_count += 1
                         continue # Go to next parameter after setting NA/empty string

                    # Proceed with type-specific conversion and setting for non-"NA"/non-empty values
                    if storage_type == StorageType.String:
                        param.Set(value_str)
                        updated_params_count += 1
                    elif storage_type == StorageType.Integer:
                         try:
                            int_value = int(value_str)
                            param.Set(int_value)
                            updated_params_count += 1
                         except ValueError:
                             error_log.append("Row {0}: Element ID {1}: Cannot set Integer parameter '{2}' with value '{3}'. Data type mismatch.".format(row_num, element_id_str, param_name, value_str))
                    elif storage_type == StorageType.Double:
                         try:
                            double_value = float(value_str)
                            internal_value = double_value
                            definition = param.Definition

                            # Attempt to get units (handle different Revit API versions)
                            display_unit_type = DisplayUnitType.DUT_UNDEFINED # Default
                            unit_type_id = None # For Revit 2021+ ForgeTypeId
                            param_type = definition.ParameterType # Fallback

                            try:
                                if hasattr(definition, "GetUnitTypeId"): # Revit 2021+
                                    unit_type_id = definition.GetUnitTypeId()
                                    # ForgeTypeId requires RevitAPI >= 2021. Comparing TypeId strings is one way.
                                    # Direct use of ForgeTypeId constants (e.g., UnitTypeId.Millimeters) requires Revit 2021+ API access.
                                    # Using DisplayUnitType remains more broadly compatible for simple cases.
                                    # Let's stick to DisplayUnitType based conversion for simplicity here.
                                    # We can try getting DUT from ParameterType as a fallback below if ForgeTypeId is complex.
                                    pass
                                elif hasattr(param, "DisplayUnitType"): # Check param object itself (older mechanism)
                                     display_unit_type = param.DisplayUnitType
                                else: # Fallback using ParameterType (less reliable for specific units)
                                    if param_type == ParameterType.Length:
                                        # Assume default project units might be active, but DUT_MILLIMETERS is a common explicit CSV format
                                        display_unit_type = DisplayUnitType.DUT_MILLIMETERS # ASSUMPTION for conversion
                                    elif param_type == ParameterType.Area:
                                        display_unit_type = DisplayUnitType.DUT_SQUARE_METERS # ASSUMPTION
                                    elif param_type == ParameterType.Volume:
                                         display_unit_type = DisplayUnitType.DUT_CUBIC_METERS # ASSUMPTION
                                     # Add other common types if needed

                                # Refinement: If DisplayUnitType was found via param.DisplayUnitType or derived from ParameterType
                                if display_unit_type != DisplayUnitType.DUT_UNDEFINED and display_unit_type != DisplayUnitType.DUT_CUSTOM:
                                    internal_value = UnitUtils.ConvertToInternalUnits(double_value, display_unit_type)
                                elif param_type == ParameterType.Length and display_unit_type == DisplayUnitType.DUT_UNDEFINED:
                                    # Explicit fallback for Length if units couldn't be determined otherwise
                                    internal_value = UnitUtils.ConvertToInternalUnits(double_value, DisplayUnitType.DUT_MILLIMETERS) # ASSUMPTION

                            except Exception as unit_ex:
                                # Optional: Log minor unit errors if needed
                                # error_log.append("Row {0}: Element ID {1}: Minor error getting units for '{2}': {3}".format(row_num, element_id_str, param_name, str(unit_ex)))
                                pass # Proceed without unit conversion if error occurs or units are ambiguous

                            param.Set(internal_value)
                            updated_params_count += 1
                         except ValueError:
                             error_log.append("Row {0}: Element ID {1}: Cannot set Double/Number parameter '{2}' with value '{3}'. Data type mismatch.".format(row_num, element_id_str, param_name, value_str))
                    elif storage_type == StorageType.ElementId:
                         try:
                            # Assume the value is an integer representing an ElementId
                            id_value_long = System.Int64.Parse(value_str)
                            element_id_value = ElementId(id_value_long)
                            # Optional check: Ensure the target element ID exists?
                            # target_elem = doc.GetElement(element_id_value)
                            # if not target_elem and element_id_value != ElementId.InvalidElementId:
                            #    raise ValueError("Target ElementId does not exist")
                            param.Set(element_id_value)
                            updated_params_count += 1
                         except System.FormatException:
                             error_log.append("Row {0}: Element ID {1}: Cannot set ElementId parameter '{2}' with value '{3}'. Invalid ID format (must be integer).".format(row_num, element_id_str, param_name, value_str))
                         except Autodesk.Revit.Exceptions.ArgumentException: # Catches invalid ElementId values passed to Set
                             error_log.append("Row {0}: Element ID {1}: Value '{2}' for ElementId parameter '{3}' is not a valid Element ID representable in this document.".format(row_num, element_id_str, value_str, param_name))
                         except ValueError as val_err: # Catch custom error like non-existent target element
                             error_log.append("Row {0}: Element ID {1}: Cannot set ElementId parameter '{2}' with value '{3}': {4}".format(row_num, element_id_str, param_name, value_str, str(val_err)))

                    else:
                         # Handle other types like Set if needed, otherwise log as unhandled
                         error_log.append("Row {0}: Element ID {1}: Parameter '{2}' has unhandled StorageType: {3}".format(row_num, element_id_str, param_name, storage_type))

                except System.FormatException as fmt_ex:
                     error_log.append("Row {0}: Element ID {1}: Formatting error setting parameter '{2}' with value '{3}': {4}".format(row_num, element_id_str, param_name, value_str, str(fmt_ex)))
                except Autodesk.Revit.Exceptions.ArgumentException as arg_ex:
                     # This might catch invalid value types more broadly than specific conversions
                     error_log.append("Row {0}: Element ID {1}: Invalid argument or data type error setting parameter '{2}' with value '{3}': {4}".format(row_num, element_id_str, param_name, value_str, str(arg_ex)))
                except Exception as ex:
                    # Catch other potential errors during the param.Set() call
                    error_log.append("Row {0}: Element ID {1}: Error setting parameter '{2}' with value '{3}': {4}".format(row_num, element_id_str, param_name, value_str, str(ex)))


# --- 3. Print Summary / Log ---
# Using string formatting compatible with IronPython 2.7+
summary_lines = []
summary_lines.append("--- Parameter Update Summary ---")
summary_lines.append("Processed {0} data rows.".format(processed_rows))
summary_lines.append("Successfully updated {0} parameters.".format(updated_params_count))

if error_log:
    summary_lines.append("\n--- Errors Encountered ({0}) ---".format(len(error_log)))
    # Truncate log if it gets too long for RevitPythonShell or console
    max_log_lines = 50
    log_lines_to_show = error_log[:max_log_lines]
    for i, log_entry in enumerate(log_lines_to_show):
        summary_lines.append("{0}: {1}".format(i + 1, log_entry))
    if len(error_log) > max_log_lines:
        summary_lines.append("... (additional {0} errors truncated)".format(len(error_log) - max_log_lines))

else:
    summary_lines.append("\n--- No errors encountered. ---")

# Print combined summary and errors
print("\n".join(summary_lines))

# Example of how data export would be triggered if needed (not requested here)
# print("EXPORT::CSV::parameter_update_log.csv")
# print("Row Number,Element ID,Parameter Name,Value,Status/Error\n" + "\n".join(error_log)) # Just an example structure