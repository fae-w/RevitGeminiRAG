# Purpose: This script updates the 'Scope Description' parameter of selected Revit Assembly Instances based on data from an input string.

﻿# Mandatory Imports
import clr
import System # Required for str() conversion, exceptions, Environment.NewLine
from System import StringSplitOptions, Environment

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    AssemblyInstance,
    Parameter,
    StorageType,
    BuiltInParameter,
    Element,
    ElementId
)
from System.Collections.Generic import List

# --- Input Data ---
# Raw multi-line string containing the data (header included)
# Format: AssemblyMark,ScopeLine1,ScopeLine2
input_data_string = """AssemblyMark,ScopeLine1,ScopeLine2
ASM-01,Supply and Install Fixture,Connect to Services
ASM-02,Fabricate Off-site,Deliver and Position
ASM-03,Review Submittals,Coordinate Delivery""" # Added one more for testing

# --- Configuration: Parameter Mapping ---
target_parameter_name = "Scope Description"
# Note: Multi-line text parameters are typically StorageType.String in Revit API

# --- Data Processing ---
data_to_set = {} # Dictionary to store {assembly_mark: combined_scope_description}
header = []
lines = input_data_string.strip().split('\n')

if not lines:
    print("# Error: Input data string is empty.")
else:
    # Process Header
    header_line = lines[0].strip()
    header = [h.strip() for h in header_line.split(',')]
    expected_headers = ["AssemblyMark", "ScopeLine1", "ScopeLine2"]
    if not header or header != expected_headers:
        print("# Error: Input data must have a header row exactly matching: '{}'. Found: '{}'".format(",".join(expected_headers), header_line))
        header = [] # Invalidate header

    # Process Data Rows
    if header:
        num_columns = len(header)
        for i, line in enumerate(lines[1:]):
            line = line.strip()
            if not line: continue # Skip empty lines
            values = [v.strip() for v in line.split(',')]
            if len(values) == num_columns:
                assembly_mark = values[0]
                scope_line1 = values[1]
                scope_line2 = values[2]

                if not assembly_mark:
                    print("# Warning: Skipping row {} - AssemblyMark value is empty.".format(i + 2))
                    continue

                # Combine scope lines with a newline
                combined_scope = "{}{}{}".format(scope_line1, Environment.NewLine, scope_line2)

                if assembly_mark in data_to_set:
                     print("# Warning: Duplicate AssemblyMark '{}' found in input data. Row {} will overwrite previous data for this mark.".format(assembly_mark, i + 2))
                data_to_set[assembly_mark] = combined_scope
            else:
                print("# Warning: Skipping row {} - Incorrect number of columns (expected {}, found {}). Line: '{}'".format(i + 2, num_columns, len(values), line))

# --- Get Selection ---
selected_ids = []
try:
    selected_ids_collection = uidoc.Selection.GetElementIds()
    if selected_ids_collection and selected_ids_collection.Count > 0:
        selected_ids = list(selected_ids_collection)
        print("# Found {} selected elements.".format(len(selected_ids)))
    else:
        print("# No elements are currently selected.")
except System.Exception as e:
    print("# Error getting selection: {}".format(e))


# --- Find and Update Selected Assemblies ---
if not data_to_set:
    print("# No valid data parsed from input string. Aborting element update.")
elif not selected_ids:
    print("# No elements selected. Aborting element update.")
else:
    print("# Parsed {} data entries. Starting element update...".format(len(data_to_set)))
    updated_count = 0
    skipped_not_assembly = 0
    skipped_mark_not_found = 0
    skipped_param_not_found = 0
    skipped_param_readonly = 0
    skipped_param_wrong_type = 0
    error_count = 0
    found_marks_in_selection = set() # Track marks found among selected assemblies

    for elem_id in selected_ids:
        try:
            element = doc.GetElement(elem_id)
            if not element:
                print("# Warning: Could not retrieve element for ID {}".format(elem_id))
                skipped_not_assembly += 1
                continue

            if isinstance(element, AssemblyInstance):
                assembly_instance = element
                assembly_mark = None
                mark_param = None

                # Try to get the Mark parameter (common way to identify instances)
                try:
                    mark_param = assembly_instance.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                    if mark_param and mark_param.HasValue:
                        assembly_mark = mark_param.AsString()
                    else:
                        # Fallback: Try Assembly Name if Mark is not set/found
                        # assembly_mark = assembly_instance.Name # Or assembly_instance.AssemblyTypeName
                        pass # Stick to Mark based on input data header 'AssemblyMark'
                except Exception as mark_ex:
                    print("# Error getting Mark for Assembly ID {}: {}".format(elem_id, mark_ex))
                    # Continue processing other parameters if possible, but likely fails lookup

                if assembly_mark and assembly_mark in data_to_set:
                    found_marks_in_selection.add(assembly_mark)
                    print("\n# Processing Assembly: Mark='{}', ID={}".format(assembly_mark, elem_id))
                    scope_value_to_set = data_to_set[assembly_mark]

                    # Find the target parameter "Scope Description"
                    scope_param = None
                    try:
                        scope_param = assembly_instance.LookupParameter(target_parameter_name)
                    except Exception as lookup_ex:
                         print("  - Error looking up parameter '{}': {}".format(target_parameter_name, lookup_ex))
                         error_count += 1
                         continue # Skip to next element

                    if scope_param:
                        # Validate parameter
                        if scope_param.IsReadOnly:
                            print("  - Skipping: Parameter '{}' is read-only.".format(target_parameter_name))
                            skipped_param_readonly += 1
                        elif scope_param.StorageType != StorageType.String:
                             print("  - Skipping: Parameter '{}' has wrong type (Expected: String, Actual: {}).".format(
                                 target_parameter_name, scope_param.StorageType))
                             skipped_param_wrong_type += 1
                        else:
                            # Set the parameter value
                            try:
                                set_result = scope_param.Set(scope_value_to_set)
                                if set_result:
                                    print("  - Success: Set '{}' parameter.".format(target_parameter_name))
                                    # print("    Value set:\n---\n{}\n---".format(scope_value_to_set)) # Optional detail
                                    updated_count += 1
                                else:
                                    print("  - Failed: Could not set parameter '{}'. Set method returned false.".format(target_parameter_name))
                                    error_count += 1
                            except System.Exception as set_ex:
                                print("  - Failed: Error setting parameter '{}': {}".format(target_parameter_name, set_ex))
                                error_count += 1
                    else:
                        print("  - Skipping: Parameter '{}' not found on this assembly.".format(target_parameter_name))
                        skipped_param_not_found += 1

                elif assembly_mark:
                    # Assembly mark found, but not in input data
                    print("# Info: Selected Assembly Mark '{}' (ID {}) not found in input data.".format(assembly_mark, elem_id))
                    skipped_mark_not_found += 1
                else:
                    # Could not retrieve a mark from the assembly instance
                    print("# Warning: Could not retrieve 'Mark' from selected AssemblyInstance ID {}. Skipping.".format(elem_id))
                    skipped_mark_not_found += 1 # Count as mark not found for matching purposes
            else:
                # Selected element is not an AssemblyInstance
                skipped_not_assembly += 1

        except System.Exception as proc_ex:
            error_count += 1
            print("# Error processing element ID {}: {}".format(elem_id, proc_ex))

    # --- Final Report ---
    print("\n# --- Update Summary ---")
    print("# Total Selected Elements: {}".format(len(selected_ids)))
    print("# Selected elements that were Assembly Instances: {}".format(len(selected_ids) - skipped_not_assembly))
    print("# Successfully Updated Assemblies: {}".format(updated_count))
    print("# Skipped (Not an Assembly Instance): {}".format(skipped_not_assembly))
    print("# Skipped (Assembly Mark mismatch or not found on instance): {}".format(skipped_mark_not_found))
    print("# Skipped (Parameter '{}' not found): {}".format(target_parameter_name, skipped_param_not_found))
    print("# Skipped (Parameter '{}' read-only): {}".format(target_parameter_name, skipped_param_readonly))
    print("# Skipped (Parameter '{}' wrong type): {}".format(target_parameter_name, skipped_param_wrong_type))
    print("# Errors Encountered: {}".format(error_count))

    # Report on unmatched input data
    input_marks = set(data_to_set.keys())
    unmatched_input_marks = sorted(list(input_marks - found_marks_in_selection))
    if unmatched_input_marks:
        print("# The following AssemblyMarks from the input data were NOT found among the selected Assembly Instances:")
        for mark in unmatched_input_marks:
            print("  - {}".format(mark))
    elif input_marks and found_marks_in_selection:
         print("# All AssemblyMarks from the input data that matched a selected Assembly Instance were processed.")
    elif not input_marks:
         print("# Input data was empty or invalid.")


# --- Script Finished ---