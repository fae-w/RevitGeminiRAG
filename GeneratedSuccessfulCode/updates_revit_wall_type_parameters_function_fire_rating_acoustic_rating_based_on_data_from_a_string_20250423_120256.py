# Purpose: This script updates Revit wall type parameters (function, fire rating, acoustic rating) based on data from a string.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB
clr.AddReference('System') # Required for Enum parsing
import System # Required for Enum parsing

# --- Input Data ---
# Represents the desired state for specific Wall Types.
# Format: TypeName,Function,FireRating,AcousticRating
data_string = """TypeName,Function,FireRating,AcousticRating
INT-Stud-Std,Interior,30 min,STC 40
INT-Stud-Acoustic,Interior,60 min,STC 55
BLK-Shaft,Core Shaft,120 min,STC 50"""

# --- Configuration ---
# Get the WallFunction enum type once
wall_function_enum_type = clr.GetClrType(DB.WallFunction)

# Mapping from string values in the data to Revit API WallFunction enum values
# Using System.Enum.Parse for potentially increased robustness over direct attribute access
try:
    function_map = {
        "Interior": System.Enum.Parse(wall_function_enum_type, "Interior"),
        "Exterior": System.Enum.Parse(wall_function_enum_type, "Exterior"),
        "Foundation": System.Enum.Parse(wall_function_enum_type, "Foundation"),
        "Retaining": System.Enum.Parse(wall_function_enum_type, "Retaining"),
        "Soffit": System.Enum.Parse(wall_function_enum_type, "Soffit"),
        "Core Shaft": System.Enum.Parse(wall_function_enum_type, "CoreShaft"),
        "Core-Shaft": System.Enum.Parse(wall_function_enum_type, "CoreShaft") # Handle common variation
    }
except System.ArgumentException as enum_parse_err:
    print("# FATAL ERROR: Could not parse WallFunction enum values. Check Revit API version or enum names.")
    print("# Details: {}".format(repr(enum_parse_err)))
    function_map = None # Prevent script from proceeding

# Parameter names to update (case-sensitive)
fire_rating_param_name = "Fire Rating"
acoustic_rating_param_name = "Acoustic Rating"

# --- Script Core Logic ---

if function_map is not None: # Only proceed if enum map was created successfully
    # Parse the input data string
    lines = data_string.strip().split('\n')
    if not lines or len(lines) < 2:
        print("# Error: Input data string is empty or has no data rows.")
    else:
        header = [h.strip() for h in lines[0].split(',')]
        # Verify required headers exist
        required_headers = ['TypeName', 'Function', 'FireRating', 'AcousticRating']
        if not all(h in header for h in required_headers):
            print("# Error: Input data header is missing required columns. Expected: {}".format(", ".join(required_headers)))
        else:
            data_rows = []
            for i, line in enumerate(lines[1:], 1):
                values = [v.strip() for v in line.split(',')]
                if len(values) == len(header):
                    row_dict = dict(zip(header, values))
                    data_rows.append(row_dict)
                else:
                    print("# Warning: Skipping malformed data line {}: {}".format(i + 1, line))

            # Collect all WallType elements in the document and create a lookup map
            wall_type_collector = DB.FilteredElementCollector(doc).OfClass(DB.WallType)
            # Use element.Name directly for WallType name retrieval
            wall_type_map = {wt.Name: wt for wt in wall_type_collector}

            updated_count = 0
            types_processed_count = 0
            not_found_count = 0
            param_error_count = 0
            function_error_count = 0
            general_error_count = 0
            param_not_found_log = set()
            param_read_only_log = set()

            # Iterate through the parsed data and update Wall Types
            for row in data_rows:
                type_name = row.get('TypeName')
                if not type_name:
                    print("# Warning: Skipping row due to missing 'TypeName': {}".format(row))
                    general_error_count += 1
                    continue

                wall_type = wall_type_map.get(type_name)
                if not wall_type:
                    not_found_count += 1
                    # print("# Info: WallType '{}' not found in the project.".format(type_name)) # Optional info message
                    continue

                types_processed_count += 1
                type_updated_this_iteration = False
                try:
                    # 1. Update Function Parameter (Built-in)
                    # We set the FUNCTION_PARAM (Type Parameter), not the read-only WallType.Function property.
                    function_str = row.get('Function')
                    if function_str:
                        target_function_enum = function_map.get(function_str)
                        if target_function_enum is not None:
                            func_param = wall_type.get_Parameter(DB.BuiltInParameter.FUNCTION_PARAM)
                            if func_param and not func_param.IsReadOnly:
                                current_func_val = func_param.AsInteger()
                                target_func_val = int(target_function_enum) # Cast enum to its integer value

                                if current_func_val != target_func_val:
                                    try:
                                        # Transaction is handled externally by C# wrapper
                                        func_param.Set(target_func_val)
                                        type_updated_this_iteration = True
                                        # print("# Updated Function parameter for '{}' to {}".format(type_name, function_str)) # Debug
                                    except Exception as func_set_err:
                                        print("# Error setting Function parameter for WallType '{}': {}".format(type_name, repr(func_set_err)))
                                        function_error_count += 1
                            elif func_param and func_param.IsReadOnly:
                                # Only log as read-only if we intended to change it and couldn't
                                current_func_val = func_param.AsInteger()
                                target_func_val = int(target_function_enum)
                                if current_func_val != target_func_val:
                                    param_read_only_log.add("Function (Built-in)")
                                    function_error_count += 1 # Count as error if we intended to change it
                            elif not func_param:
                                param_not_found_log.add("Function (Built-in)")
                                function_error_count += 1 # Count as error if we intended to change it
                        else:
                            print("# Warning: Unknown Function value '{}' for WallType '{}'. Skipping Function update.".format(function_str, type_name))
                            function_error_count += 1

                    # 2. Update Fire Rating Parameter
                    fire_rating_val = row.get('FireRating')
                    if fire_rating_val is not None: # Check if key exists, even if value is empty string
                        # Try BuiltInParameter first, then LookupParameter as fallback
                        fire_rating_param = wall_type.get_Parameter(DB.BuiltInParameter.FIRE_RATING)
                        if not fire_rating_param:
                            fire_rating_param = wall_type.LookupParameter(fire_rating_param_name)

                        if fire_rating_param:
                            if not fire_rating_param.IsReadOnly:
                                # Check current value to avoid unnecessary updates
                                current_val_str = fire_rating_param.AsValueString() or fire_rating_param.AsString() or ""
                                if current_val_str != fire_rating_val:
                                    try:
                                        # Transaction is handled externally by C# wrapper
                                        fire_rating_param.Set(fire_rating_val)
                                        type_updated_this_iteration = True
                                        # print("# Updated '{}' for '{}' to {}".format(fire_rating_param_name, type_name, fire_rating_val)) # Debug
                                    except Exception as param_set_err:
                                        print("# Error setting '{}' for WallType '{}': {}".format(fire_rating_param_name, type_name, repr(param_set_err)))
                                        param_error_count += 1
                            else:
                                # Only log as read-only if we intended to change it and couldn't
                                current_val_str = fire_rating_param.AsValueString() or fire_rating_param.AsString() or ""
                                if current_val_str != fire_rating_val:
                                     param_read_only_log.add(fire_rating_param_name)
                                     param_error_count += 1 # Count as error if we intended to change
                        else:
                             param_not_found_log.add(fire_rating_param_name)
                             # Don't increment error count if value was empty/not intended for update? Assume intent if key exists.
                             param_error_count += 1


                    # 3. Update Acoustic Rating Parameter
                    acoustic_rating_val = row.get('AcousticRating')
                    if acoustic_rating_val is not None: # Check if key exists
                        acoustic_rating_param = wall_type.LookupParameter(acoustic_rating_param_name) # No standard BuiltInParameter

                        if acoustic_rating_param:
                            if not acoustic_rating_param.IsReadOnly:
                                # Check current value to avoid unnecessary updates
                                current_val_str = acoustic_rating_param.AsValueString() or acoustic_rating_param.AsString() or ""
                                if current_val_str != acoustic_rating_val:
                                    try:
                                        # Transaction is handled externally by C# wrapper
                                        acoustic_rating_param.Set(acoustic_rating_val)
                                        type_updated_this_iteration = True
                                        # print("# Updated '{}' for '{}' to {}".format(acoustic_rating_param_name, type_name, acoustic_rating_val)) # Debug
                                    except Exception as param_set_err:
                                        print("# Error setting '{}' for WallType '{}': {}".format(acoustic_rating_param_name, type_name, repr(param_set_err)))
                                        param_error_count += 1
                            else:
                                # Only log as read-only if we intended to change it and couldn't
                                current_val_str = acoustic_rating_param.AsValueString() or acoustic_rating_param.AsString() or ""
                                if current_val_str != acoustic_rating_val:
                                    param_read_only_log.add(acoustic_rating_param_name)
                                    param_error_count += 1 # Count as error if we intended to change
                        else:
                            param_not_found_log.add(acoustic_rating_param_name)
                            # Don't increment error count if value was empty/not intended for update? Assume intent if key exists.
                            param_error_count += 1

                    if type_updated_this_iteration:
                        updated_count += 1

                except Exception as e:
                    general_error_count += 1
                    # Use repr(e) for potentially more detailed error in IronPython
                    print("# Error processing WallType '{}': {}".format(type_name, repr(e)))

            # --- Summary Output ---
            print("--- Wall Type Update Summary ---")
            print("# Wall Types Found and Processed: {}".format(types_processed_count))
            print("# Wall Types Successfully Updated (at least one parameter): {}".format(updated_count))
            print("# Wall Types in Data Not Found in Project: {}".format(not_found_count))
            print("# Errors related to Function parameter: {}".format(function_error_count))
            print("# Errors related to other parameters ('{}', '{}'): {}".format(fire_rating_param_name, acoustic_rating_param_name, param_error_count))
            print("# General Processing Errors (per type): {}".format(general_error_count))
            if param_not_found_log:
                print("# Parameters Not Found on some types: {}".format(", ".join(sorted(list(param_not_found_log)))))
            if param_read_only_log:
                print("# Read-Only Parameters encountered (prevented update): {}".format(", ".join(sorted(list(param_read_only_log)))))
else:
    print("# Script terminated due to error initializing WallFunction map.")