# Purpose: This script finds and sets parameters on specific mechanical equipment in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Added for System.InvalidOperationException and general exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilyInstance,
    BuiltInCategory,
    BuiltInParameter,
    Parameter,
    Element,
    StorageType
)
import System # For System.InvalidOperationException and general exception handling

# --- Configuration ---
target_mark = "RTU-02"
# Define parameters to set.
# 'value': The value to set, **converted to Revit's internal units**.
# 'target_type': The expected StorageType of the parameter.
# 'bip': The preferred BuiltInParameter enum value (optional).
# 'search_names': Fallback names to search for if BIP fails or isn't provided (optional).
parameters_to_set = {
    # Parameter Name (for reporting) : { parameter details }
    "Mark":             {'value': "RTU-02", # String value
                         'target_type': StorageType.String,
                         'bip': BuiltInParameter.ALL_MODEL_MARK},

    "FlowRate":         {'value': 8000.0 / 60.0, # Input 8000 CFM -> Internal CFS
                         'target_type': StorageType.Double,
                         'bip': BuiltInParameter.RBS_DUCT_FLOW_PARAM, # Common for Air Terminals/Equipment
                         'search_names': ['Flow Rate', 'Air Flow', 'Flow', 'Supply Airflow']}, # Fallback names

    "ElectricalLoad":   {'value': 15.0 * 1000.0, # Input 15 kW -> Internal Watts (base unit for Apparent Load VA is equivalent to W here)
                         'target_type': StorageType.Double,
                         'bip': BuiltInParameter.RBS_ELEC_APPARENT_LOAD, # Corrected: Use RBS_ELEC_APPARENT_LOAD for MECH equip
                         'search_names': ['Electrical Load', 'Load', 'Apparent Load', 'Total Load', 'Electrical Power']}, # Fallback names

    "Weight":           {'value': 500.0, # Input 500 kg. Assuming parameter uses kg. If lbs needed: 500.0 * 2.20462
                         'target_type': StorageType.Double,
                         'bip': None, # No common reliable BIP for simple weight
                         'search_names': ['Weight', 'Mass', 'Equipment Weight', 'Operating Weight']} # Common custom/shared names
}

# --- Find the Mechanical Equipment by Mark ---
target_element = None
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MechanicalEquipment).WhereElementIsNotElementType()

print("# Searching for Mechanical Equipment with Mark = '{}'...".format(target_mark))

found_count = 0
potential_matches = []

for element in collector:
    # Check if the element is a FamilyInstance (most mechanical equipment are)
    # This helps filter out potential non-instance elements if any slip through category filter
    if not isinstance(element, FamilyInstance):
        continue
    try:
        # Check for the Mark parameter
        mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if mark_param and mark_param.HasValue:
            # Compare as string
            if mark_param.AsString() == target_mark:
                # target_element = element # Assign inside the loop temporarily
                potential_matches.append(element)
                found_count += 1
                # Uncomment break if only the first match should be processed
                # break
    except System.Exception as e:
        # Log error checking a specific element but continue searching
        print("# Warning: Error checking element ID {}: {}".format(element.Id, e))

# --- Handle Findings ---
if found_count == 0:
    print("# Error: No Mechanical Equipment found with Mark = '{}'.".format(target_mark))
    target_element = None # Ensure it's None if not found
elif found_count > 1:
    print("# Error: Found {} elements with Mark = '{}'. Aborting parameter setting. Please ensure Marks are unique.".format(found_count, target_mark))
    # Optionally list the IDs found
    for el in potential_matches: print("  - Found ambiguous match: ID {}".format(el.Id))
    target_element = None # Prevent setting parameters if ambiguous
else:
    target_element = potential_matches[0] # Assign the unique element

# --- Set Parameters if a Unique Element Found ---
if target_element:
    print("# Found unique element ID: {}. Attempting to set parameters...".format(target_element.Id))
    success_count = 0
    fail_count = 0
    skipped_count = 0
    notfound_count = 0

    # Ensure we are within a Transaction (handled externally by C# wrapper)
    # t = Transaction(doc, "Set Mechanical Equipment Parameters")
    # t.Start()

    try: # Wrap parameter setting attempts
        for param_name, param_info in parameters_to_set.items():
            param_to_set = None
            param_found_by = None

            # 1. Try BuiltInParameter first if provided
            if param_info.get('bip') is not None and param_info['bip'] != BuiltInParameter.INVALID:
                try:
                    # Use get_Parameter for BuiltInParameters
                    param_to_set = target_element.get_Parameter(param_info['bip'])
                    if param_to_set:
                        param_found_by = "BuiltInParameter ({})".format(param_info['bip'].ToString()) # Use ToString() for readable name
                except System.Exception as e:
                     # Catch potential errors, although get_Parameter with valid BIP usually just returns None if not present
                     # print("# Debug: Error checking BIP {} for '{}': {}".format(param_info['bip'], param_name, e))
                     param_to_set = None # Ensure it's None if error occurred

            # 2. If not found by BIP (or BIP not provided), try searching by name(s)
            if not param_to_set and param_info.get('search_names'):
                for name in param_info['search_names']:
                    try:
                        # Use LookupParameter for searching by name
                        param_to_set = target_element.LookupParameter(name)
                        if param_to_set:
                            param_found_by = "Name ('{}')".format(name)
                            break # Stop searching once found by name
                    except System.Exception as e:
                        # Catch potential errors during lookup
                        # print("# Debug: Error looking up parameter '{}' by name: {}".format(name, e))
                        param_to_set = None # Ensure it's None if error occurred

            # 3. Process the found parameter (if any)
            if param_to_set:
                try:
                    if param_to_set.IsReadOnly:
                        print("# Skipping: Parameter '{}' (found by {}) is read-only.".format(param_name, param_found_by))
                        skipped_count += 1
                        continue # Move to next parameter

                    # Check if storage type matches the expected type
                    if param_to_set.StorageType != param_info['target_type']:
                        print("# Skipping: Parameter '{}' (found by {}) has wrong storage type (Expected: {}, Actual: {}).".format(
                            param_name, param_found_by, param_info['target_type'], param_to_set.StorageType))
                        skipped_count += 1
                        continue # Move to next parameter

                    # Attempt to set the value
                    value_to_set = param_info['value']
                    set_result = False
                    original_fail_count = fail_count # Track if an exception increments fail_count

                    # Call appropriate Set method based on StorageType
                    try:
                        if param_info['target_type'] == StorageType.String:
                            set_result = param_to_set.Set(str(value_to_set))
                        elif param_info['target_type'] == StorageType.Double:
                            set_result = param_to_set.Set(float(value_to_set))
                        elif param_info['target_type'] == StorageType.Integer:
                            set_result = param_to_set.Set(int(value_to_set))
                        elif param_info['target_type'] == StorageType.ElementId:
                            # Assumes 'value' is already an ElementId object if target_type is ElementId
                            set_result = param_to_set.Set(value_to_set)
                        else:
                            print("# Skipping: Parameter '{}' has unhandled StorageType: {}.".format(param_name, param_to_set.StorageType))
                            skipped_count += 1
                            continue # Move to next parameter in the loop

                    except System.InvalidOperationException as inv_op_ex: # Catch cases like trying to set formula-driven parameters
                         print("# Failed: Cannot set parameter '{}' (found by {}). Reason: {}".format(param_name, param_found_by, inv_op_ex.Message))
                         fail_count += 1
                         set_result = False # Ensure failure is recorded
                    except System.Exception as set_ex_inner:
                        # Catch other potential errors during Set()
                        print("# Failed: Error calling Set() for parameter '{}' (found by {}): {}".format(param_name, param_found_by, set_ex_inner))
                        fail_count += 1
                        set_result = False # Ensure failure is recorded


                    # Report outcome of the Set operation
                    if set_result:
                        # Use standard formatting for float to avoid excessive decimals in printout
                        if isinstance(value_to_set, float):
                            print_val = "{:.3f}".format(value_to_set)
                        else:
                            print_val = value_to_set
                        print("# Success: Set '{}' (found by {}) to '{}'.".format(param_name, param_found_by, print_val))
                        success_count += 1
                    # Check if Set() returned false *and* no exception was caught during the Set() try block *and* not skipped
                    elif not set_result and fail_count == original_fail_count and param_name not in [p[0] for p in parameters_to_set.items()][:success_count+fail_count+skipped_count]: # A bit complex check to ensure it wasn't skipped or already failed
                         print("# Failed: Could not set parameter '{}' (found by {}). Set method returned false.".format(param_name, param_found_by))
                         fail_count += 1 # Increment fail count here if Set returned false without exception

                except System.Exception as process_ex:
                    # Catch unexpected errors during parameter processing (e.g., checking IsReadOnly)
                    print("# Failed: Error processing parameter '{}' (found by {}): {}".format(param_name, param_found_by, process_ex))
                    fail_count += 1
            else:
                # Parameter was not found by BIP or any search name
                print("# Failed: Parameter '{}' not found on element ID {}.".format(param_name, target_element.Id))
                notfound_count += 1

        # Commit transaction if successful (handled externally)
        # if fail_count == 0 and skipped_count == 0 and notfound_count == 0: # Or adjust logic based on desired outcome
        #     t.Commit()
        # else:
        #     t.RollBack()
        #     print("# Warning: Transaction rolled back due to errors/skipped/not found parameters.")

    except System.Exception as outer_ex:
        # Catch any errors during the main loop or transaction management
        print("# Critical Error: An unexpected error occurred during parameter setting: {}".format(outer_ex))
        # t.RollBack() # Ensure rollback on unexpected errors
        # print("# Transaction rolled back due to critical error.")
        # Re-raise if needed or handle appropriately

    # --- Print Summary ---
    print("# --- Parameter Setting Summary for Element ID: {} ---".format(target_element.Id))
    print("# Parameters targeted: {}".format(len(parameters_to_set)))
    print("# Successfully Set: {}".format(success_count))
    print("# Failed (Set error/exception/returned false): {}".format(fail_count))
    print("# Skipped (Read-Only/Wrong Type/Unhandled): {}".format(skipped_count))
    print("# Not Found: {}".format(notfound_count))

# --- Script Finished ---
# Final status indicated by messages above.