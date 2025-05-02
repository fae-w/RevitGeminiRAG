# Purpose: This script updates electrical equipment parameters in Revit based on data from an input string.

﻿# Mandatory Imports
import clr
import System # Required for str() conversion, exceptions
from System import StringSplitOptions

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    BuiltInParameter,
    Parameter,
    StorageType,
    Element
)
# Attempt to import Electrical namespace, but handle gracefully if not available
ElectricalEquipment = None
try:
    clr.AddReference('RevitAPI') # Ensure base API is referenced
    clr.AddReference('RevitAPIElectrical') # Specific assembly for electrical types if needed
    from Autodesk.Revit.DB.Electrical import ElectricalEquipment
except System.IO.FileNotFoundException:
    print("# Warning: RevitAPIElectrical assembly not found. Will rely on BuiltInCategory.OST_ElectricalEquipment.")
except Exception as e:
    print("# Warning: Could not load Electrical types. Error: {}".format(e))
    # Continue script, assuming OST_ElectricalEquipment filter is sufficient

# --- Input Data ---
# Raw multi-line string containing the data (header included)
input_data_string = """Tag,Manufacturer,ModelNumber,Voltage
LP-01,Square D,NQOD-1,120/208V
LP-02,Square D,NQOD-2,120/208V
TX-01,Siemens,XL-1,480-120/208V"""

# --- Configuration: Parameter Mapping ---
# Maps the header names from the input string to Revit Parameter details
# 'target_type': The expected StorageType of the parameter.
# 'bip': The preferred BuiltInParameter enum value (optional).
# 'search_names': Fallback names to search for if BIP fails or isn't provided (optional).
parameter_mapping = {
    "Manufacturer": {
        'target_type': StorageType.String,
        'bip': BuiltInParameter.ALL_MODEL_MANUFACTURER,
        'search_names': ['Manufacturer']
    },
    "ModelNumber": {
        'target_type': StorageType.String,
        'bip': BuiltInParameter.ALL_MODEL_MODEL,
        'search_names': ['Model', 'Model Number'] # Added 'Model' as common alternative
    },
    "Voltage": {
        'target_type': StorageType.String, # Value like '120/208V' suggests string
        'bip': None, # No reliable BIP for string-based voltage representation
        'search_names': ['Voltage', 'Panel Voltage', 'Electrical Data', 'Nominal Voltage'] # Common names for voltage string
    }
    # 'Tag' is used for lookup, not setting directly in the loop below
}

# --- Data Processing ---
data_to_set = {}
header = []
lines = input_data_string.strip().split('\n')

if not lines:
    print("# Error: Input data string is empty.")
else:
    # Process Header
    header_line = lines[0].strip()
    header = [h.strip() for h in header_line.split(',')]
    if not header or header[0].lower() != 'tag':
        print("# Error: Input data must have a header row starting with 'Tag'. Found: '{}'".format(header_line))
        header = [] # Invalidate header

    # Process Data Rows
    if header:
        num_columns = len(header)
        for i, line in enumerate(lines[1:]):
            line = line.strip()
            if not line: continue # Skip empty lines
            values = [v.strip() for v in line.split(',')]
            if len(values) == num_columns:
                tag_value = values[0]
                if not tag_value:
                    print("# Warning: Skipping row {} - Tag value is empty.".format(i + 2))
                    continue
                row_data = {}
                for j in range(1, num_columns): # Start from 1 to skip Tag
                    param_header = header[j]
                    if param_header in parameter_mapping:
                        row_data[param_header] = values[j]
                    else:
                        print("# Warning: Skipping column '{}' in row {} - Header name not found in parameter_mapping.".format(param_header, i + 2))
                if tag_value in data_to_set:
                     print("# Warning: Duplicate Tag '{}' found in input data. Row {} will overwrite previous data for this tag.".format(tag_value, i + 2))
                data_to_set[tag_value] = row_data
            else:
                print("# Warning: Skipping row {} - Incorrect number of columns (expected {}, found {}). Line: '{}'".format(i + 2, num_columns, len(values), line))

# --- Find and Update Elements ---
if not data_to_set:
    print("# No valid data parsed from input string. Aborting element update.")
else:
    print("# Parsed {} data entries. Starting element update...".format(len(data_to_set)))
    updated_count = 0
    not_found_tags = list(data_to_set.keys()) # Keep track of tags we need to find
    processed_elements = set() # Track element IDs to avoid processing duplicates if collector finds them multiple times

    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ElectricalEquipment).WhereElementIsNotElementType()

    # Explicitly check if collector is empty before iterating
    try:
        first_element = collector.FirstElement()
        is_empty = (first_element is None)
    except Exception as e:
        print("# Error checking collector: {}".format(e))
        is_empty = True # Assume empty on error

    if is_empty:
         print("# No Electrical Equipment elements found in the model.")
    else:
        for element in collector:
            if not isinstance(element, FamilyInstance): # Ensure it's an instance
                continue

            # Avoid processing the same element multiple times if collector somehow returns duplicates
            if element.Id in processed_elements:
                continue

            element_tag = None
            try:
                # Get the 'Mark' parameter which corresponds to 'Tag'
                mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                if mark_param and mark_param.HasValue:
                    element_tag = mark_param.AsString()

                # Check if this element's tag is in our data dictionary
                if element_tag and element_tag in data_to_set:
                    processed_elements.add(element.Id) # Mark as processed
                    if element_tag in not_found_tags:
                        not_found_tags.remove(element_tag) # Mark tag as found

                    print("\n# Processing Element: Tag='{}', ID={}".format(element_tag, element.Id))
                    params_for_element = data_to_set[element_tag]
                    success_count_elem = 0
                    fail_count_elem = 0
                    skipped_count_elem = 0
                    notfound_count_elem = 0

                    for param_header, value_to_set in params_for_element.items():
                        param_config = parameter_mapping.get(param_header)
                        if not param_config: continue # Should not happen if parsing was correct

                        param_to_set = None
                        param_found_by = None

                        # 1. Try BuiltInParameter first
                        if param_config.get('bip') is not None and param_config['bip'] != BuiltInParameter.INVALID:
                            try:
                                param_to_set = element.get_Parameter(param_config['bip'])
                                if param_to_set:
                                    param_found_by = "BuiltInParameter ({})".format(param_config['bip'].ToString())
                            except System.Exception as e_bip:
                                # print("# Debug: Error checking BIP {} for '{}': {}".format(param_config['bip'], param_header, e_bip))
                                param_to_set = None

                        # 2. If not found by BIP, try searching by name(s)
                        if not param_to_set and param_config.get('search_names'):
                            for name in param_config['search_names']:
                                try:
                                    param_to_set = element.LookupParameter(name)
                                    if param_to_set:
                                        param_found_by = "Name ('{}')".format(name)
                                        break
                                except System.Exception as e_name:
                                    # print("# Debug: Error looking up parameter '{}' by name: {}".format(name, e_name))
                                    param_to_set = None

                        # 3. Process the found parameter
                        if param_to_set:
                            try:
                                if param_to_set.IsReadOnly:
                                    print("  - Skipping: Parameter '{}' (found by {}) is read-only.".format(param_header, param_found_by))
                                    skipped_count_elem += 1
                                    continue

                                if param_to_set.StorageType != param_config['target_type']:
                                    print("  - Skipping: Parameter '{}' (found by {}) has wrong type (Expected: {}, Actual: {}).".format(
                                        param_header, param_found_by, param_config['target_type'], param_to_set.StorageType))
                                    skipped_count_elem += 1
                                    continue

                                # Attempt to set the value (assuming string for all in this case)
                                set_result = False
                                try:
                                    if param_config['target_type'] == StorageType.String:
                                        set_result = param_to_set.Set(str(value_to_set)) # Ensure value is string
                                    # Add elif for other types if needed in future
                                    else:
                                         print("  - Skipping: Parameter '{}' has unhandled StorageType: {}.".format(param_header, param_to_set.StorageType))
                                         skipped_count_elem += 1
                                         continue

                                except System.Exception as set_ex:
                                    print("  - Failed: Error setting parameter '{}' (found by {}): {}".format(param_header, param_found_by, set_ex))
                                    fail_count_elem += 1
                                    set_result = False # Ensure failure

                                if set_result:
                                    print("  - Success: Set '{}' (found by {}) to '{}'.".format(param_header, param_found_by, value_to_set))
                                    success_count_elem += 1
                                elif fail_count_elem == 0 and skipped_count_elem == 0: # If set failed without exception
                                    print("  - Failed: Could not set parameter '{}' (found by {}). Set method returned false.".format(param_header, param_found_by))
                                    fail_count_elem += 1 # Count as failure

                            except System.Exception as process_ex:
                                print("  - Failed: Error processing parameter '{}' (found by {}): {}".format(param_header, param_found_by, process_ex))
                                fail_count_elem += 1
                        else:
                            print("  - Failed: Parameter '{}' not found on element.".format(param_header))
                            notfound_count_elem += 1

                    if success_count_elem > 0 or fail_count_elem > 0 or skipped_count_elem > 0 or notfound_count_elem > 0 :
                        updated_count += 1 # Count element as 'updated' if any parameter was touched/attempted

            except System.Exception as e:
                print("# Error processing element ID {}: {}".format(element.Id if element else "Unknown", e))


    # --- Final Report ---
    print("\n# --- Update Summary ---")
    print("# Elements processed/attempted: {}".format(updated_count))
    print("# Total data entries in input: {}".format(len(data_to_set)))

    if not_found_tags:
        print("# The following Tags from the input data were NOT found on any Electrical Equipment element:")
        for tag in sorted(not_found_tags):
            print("  - {}".format(tag))
    else:
        print("# All Tags from the input data were found and processed.")

    if updated_count == 0 and len(data_to_set) > 0 and len(not_found_tags) == len(data_to_set) and not is_empty:
         print("# Warning: No elements were updated. Check if 'Mark' parameters match the 'Tag' values in your input data.")
    elif is_empty and len(data_to_set) > 0:
         print("# Warning: No electrical equipment elements exist in the model to update.")


# --- Script Finished ---