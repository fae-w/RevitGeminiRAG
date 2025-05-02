# Purpose: This script updates Revit door instance parameters based on data from a CSV file.

﻿# Ensure necessary assemblies are referenced
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Collections') # For List

# Import necessary namespaces and classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance, # Doors are often FamilyInstances
    Parameter,
    BuiltInParameter,
    StorageType,
    Element
)
from System.Collections.Generic import List
from System import String, Exception as SystemException

# --- Input Data (CSV Format) ---
csv_data = """Mark,FireRating,Comments,HardwareSet
D-101,60 min,Standard Duty,HS-01
D-102,90 min,Heavy Duty,HS-02
D-103,60 min,Standard Duty,HS-01"""

# --- Parse CSV Data ---
parsed_data = []
lines = csv_data.strip().split('\n')
if len(lines) > 1:
    header = [h.strip() for h in lines[0].split(',')]
    try:
        mark_index = header.index("Mark")
        # Corrected line: Removed extra curly braces causing the TypeError
        param_indices = {h: i for i, h in enumerate(header) if i != mark_index}

        for line in lines[1:]:
            values = [v.strip() for v in line.split(',')]
            if len(values) == len(header):
                mark_value = values[mark_index]
                if mark_value:
                    row_data = {"Mark": mark_value}
                    for param_name, index in param_indices.items():
                        row_data[param_name] = values[index]
                    parsed_data.append(row_data)
                else:
                    print("# Warning: Skipping row with empty Mark value: '{}'".format(line))
            else:
                print("# Warning: Skipping malformed CSV row: '{}'".format(line))
    except ValueError:
        print("# Error: 'Mark' column not found in CSV header.")
        parsed_data = []
else:
    print("# Error: CSV data seems empty or lacks header row.")

# --- Parameter Mapping (CSV Header -> Revit Parameter Identifier) ---
# Using a dictionary where value is a tuple:
# (Parameter Identifier, Expected StorageType, Lookup Name if Identifier is None or fallback needed)
# Use BuiltInParameter when possible for robustness.
parameter_map = {
    "FireRating": (BuiltInParameter.DOOR_FIRE_RATING, StorageType.String, "Fire Rating"), # Changed to DOOR_FIRE_RATING for specificity
    "Comments": (BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, StorageType.String, "Comments"),
    "HardwareSet": (None, StorageType.String, "Hardware Set") # Assuming custom parameter name
    # Add other mappings here if needed
}

# --- Collect Door Instances and Index by Mark ---
door_dict = {}
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()
doors = collector.ToElements()

for door in doors:
    # Ensure it's a FamilyInstance (most doors are) to access instance parameters easily
    if isinstance(door, FamilyInstance):
        mark_param = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if mark_param and mark_param.HasValue:
            mark_value = mark_param.AsString()
            if mark_value:
                if mark_value not in door_dict:
                    door_dict[mark_value] = []
                door_dict[mark_value].append(door)

# --- Counters for Summary ---
total_rows_in_csv = len(parsed_data)
rows_processed = 0
doors_updated_count = 0
updates_applied_count = 0
errors_count = 0
warnings_count = 0
skipped_mark_not_found = 0
skipped_param_not_found = 0
skipped_param_read_only = 0
skipped_param_wrong_type = 0

# --- Iterate through Parsed Data and Update Doors ---
if not parsed_data:
    print("# No valid data parsed from CSV.")
elif not door_dict:
    print("# No door instances found in the project.")
else:
    print("# Starting door parameter update process...")
    for row_data in parsed_data:
        rows_processed += 1
        mark_to_find = row_data["Mark"]

        if mark_to_find in door_dict:
            target_doors = door_dict[mark_to_find]
            # print("# Found {} door(s) with Mark '{}'".format(len(target_doors), mark_to_find)) # Debug

            for door_instance in target_doors:
                door_updated_in_this_row = False # Flag if any param was set for this specific door element
                door_info = "Door Mark '{}', ID {}".format(mark_to_find, door_instance.Id)

                for csv_param_name, value_to_set in row_data.items():
                    if csv_param_name == "Mark":
                        continue # Skip the Mark column itself

                    if csv_param_name in parameter_map:
                        param_identifier, expected_type, lookup_name = parameter_map[csv_param_name]

                        param = None
                        try:
                            # 1. Try BuiltInParameter first if available
                            if param_identifier is not None and param_identifier != BuiltInParameter.INVALID:
                                param = door_instance.get_Parameter(param_identifier)

                            # 2. If BuiltInParameter didn't work or wasn't specified, try LookupParameter on instance
                            if not param and lookup_name:
                                param = door_instance.LookupParameter(lookup_name)

                            # 3. If still not found, maybe it's a type parameter? We only update INSTANCE parameters.
                            # So, we won't check the type here based on the request.

                            if param:
                                if param.IsReadOnly:
                                    # print("# Warning: Parameter '{}' ({}) is read-only. Skipping.".format(csv_param_name, door_info)) # Verbose
                                    warnings_count += 1
                                    skipped_param_read_only += 1
                                elif expected_type is not None and param.StorageType != expected_type:
                                    print("# Warning: Parameter '{}' ({}) has wrong storage type (Expected: {}, Actual: {}). Skipping.".format(csv_param_name, door_info, expected_type, param.StorageType))
                                    warnings_count += 1
                                    skipped_param_wrong_type += 1
                                else:
                                    # Attempt to set the value
                                    current_value_str = ""
                                    try:
                                        if param.StorageType == StorageType.String:
                                            current_value_str = param.AsString()
                                        elif param.StorageType == StorageType.Double:
                                             current_value_str = param.AsValueString() # Get value with units if applicable
                                        elif param.StorageType == StorageType.Integer:
                                             current_value_str = str(param.AsInteger())
                                        # Add other types if needed
                                    except Exception as read_ex: # Catch potential errors reading value
                                         current_value_str = "[Error reading current value: {}]".format(read_ex)


                                    # Only update if the value is different (compare as strings for simplicity here)
                                    if str(current_value_str) != str(value_to_set):
                                        try:
                                            set_result = False
                                            # Use specific Set methods based on expected type
                                            if param.StorageType == StorageType.String:
                                                set_result = param.Set(str(value_to_set))
                                            # Add elif for other types (Double, Integer, ElementId) if necessary
                                            # elif param.StorageType == StorageType.Double:
                                            #    set_result = param.Set(float(value_to_set)) # Watch out for units! Requires robust parsing.
                                            # elif param.StorageType == StorageType.Integer:
                                            #    set_result = param.Set(int(value_to_set)) # Requires robust parsing.

                                            if set_result:
                                                updates_applied_count += 1
                                                door_updated_in_this_row = True
                                                # print("# Success: Updated '{}' to '{}' for {}".format(csv_param_name, value_to_set, door_info)) # Verbose
                                            else:
                                                # Check if read-only again, might have changed or initial check failed
                                                if param.IsReadOnly:
                                                     # print("# Info: Parameter '{}' ({}) became read-only before update.".format(csv_param_name, door_info)) # Verbose
                                                     warnings_count += 1
                                                     skipped_param_read_only +=1
                                                else:
                                                     print("# Error: Failed to set parameter '{}' to '{}' for {} (Set method returned false).".format(csv_param_name, value_to_set, door_info))
                                                     errors_count += 1
                                        except SystemException as set_ex:
                                            print("# Error setting parameter '{}' for {}: {}".format(csv_param_name, door_info, set_ex.Message))
                                            errors_count += 1
                                    # else: # Value is already correct - uncomment for verbose logging
                                        # print("# Info: Parameter '{}' already set to '{}' for {}".format(csv_param_name, value_to_set, door_info))
                            else:
                                # Parameter not found on the instance
                                # print("# Warning: Instance parameter '{}' (Lookup: '{}') not found for {}. Skipping.".format(csv_param_name, lookup_name or 'N/A', door_info)) # Verbose
                                warnings_count += 1
                                skipped_param_not_found += 1

                        except SystemException as param_ex:
                            print("# Error processing parameter '{}' for {}: {}".format(csv_param_name, door_info, param_ex.Message))
                            errors_count += 1
                    else:
                        # CSV column name not found in parameter map
                        # print("# Warning: CSV column '{}' is not mapped to a Revit parameter. Skipping.".format(csv_param_name)) # Verbose
                        warnings_count += 1 # Count this as a general warning

                if door_updated_in_this_row:
                    doors_updated_count += 1 # Count unique doors that had at least one parameter updated

        else:
            # Mark from CSV not found in project doors
            # print("# Warning: Door with Mark '{}' specified in CSV row not found in the project. Skipping row.".format(mark_to_find)) # Verbose
            warnings_count += 1
            skipped_mark_not_found += 1

# --- Final Summary ---
# Calculate uncategorized warnings
uncategorized_warnings = warnings_count - skipped_mark_not_found - skipped_param_not_found - skipped_param_read_only - skipped_param_wrong_type
if uncategorized_warnings < 0: uncategorized_warnings = 0 # Avoid negative counts due to verbose flags

print("--- Door Parameter Update Summary ---")
print("Total Rows in CSV (excluding header): {}".format(total_rows_in_csv))
print("Rows Processed: {}".format(rows_processed))
print("Total Door Elements Found (Category OST_Doors, Instances): {}".format(len(doors)))
print("Unique Door Elements Updated: {}".format(doors_updated_count))
print("Total Parameter Updates Applied: {}".format(updates_applied_count))
print("--- Issues Encountered ---")
print("Skipped Rows (Mark Not Found in Project): {}".format(skipped_mark_not_found))
print("Skipped Updates (Parameter Not Found on Instance): {}".format(skipped_param_not_found))
print("Skipped Updates (Parameter Read-Only): {}".format(skipped_param_read_only))
print("Skipped Updates (Parameter Wrong Type): {}".format(skipped_param_wrong_type))
print("Other Warnings (e.g., unmapped CSV columns): {}".format(uncategorized_warnings))
print("Errors During Update: {}".format(errors_count))
print("--- Script Finished ---")