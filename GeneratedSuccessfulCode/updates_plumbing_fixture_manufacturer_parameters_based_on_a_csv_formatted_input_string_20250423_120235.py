# Purpose: This script updates plumbing fixture manufacturer parameters based on a CSV-formatted input string.

﻿# Mandatory Imports
import clr
import System # Required for str() conversion, exceptions
from System import StringComparison # For case-insensitive comparison if needed, though prompt implies exact match

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

# --- Input Data ---
# Raw multi-line string containing the data (header included)
input_data_string = """Tag,Mfr
WC-01,Kohler
LAV-01,American Standard
SHWR-01,Kohler"""

# --- Configuration ---
# Define the condition value that allows overwriting
# Explicitly check for None, empty string, and this specific value
overwrite_if_value = "Default Manufacturer"
tag_parameter_bip = BuiltInParameter.ALL_MODEL_MARK # Assumes 'Tag' corresponds to the 'Mark' parameter
manufacturer_parameter_bip = BuiltInParameter.ALL_MODEL_MANUFACTURER # Manufacturer parameter

# --- Data Processing ---
data_to_set = {}
lines = input_data_string.strip().split('\n')

if not lines or len(lines) < 2:
    print("# Error: Input data string is empty or missing data rows.")
else:
    # Process Header (optional, but good practice)
    header_line = lines[0].strip()
    header = [h.strip() for h in header_line.split(',')]
    if not header or len(header) != 2 or header[0].lower() != 'tag' or header[1].lower() != 'mfr':
        print("# Warning: Input header format mismatch. Expected 'Tag,Mfr'. Found: '{}'. Proceeding assuming column order.".format(header_line))
        # You might choose to abort here depending on strictness requirements

    # Process Data Rows
    num_columns = 2 # Expecting Tag, Mfr
    for i, line in enumerate(lines[1:]): # Start from 1 to skip header
        line = line.strip()
        if not line: continue # Skip empty lines
        values = [v.strip() for v in line.split(',')]
        if len(values) == num_columns:
            tag_value = values[0]
            mfr_value = values[1]
            if not tag_value:
                print("# Warning: Skipping row {} - Tag value is empty.".format(i + 2))
                continue
            if tag_value in data_to_set:
                 print("# Warning: Duplicate Tag '{}' found in input data. Row {} will overwrite previous data for this tag.".format(tag_value, i + 2))
            data_to_set[tag_value] = mfr_value
        else:
            print("# Warning: Skipping row {} - Incorrect number of columns (expected {}, found {}). Line: '{}'".format(i + 2, num_columns, len(values), line))

# --- Find and Update Elements ---
if not data_to_set:
    print("# No valid data parsed from input string. Aborting element update.")
else:
    print("# Parsed {} data entries. Starting element update...".format(len(data_to_set)))
    updated_count = 0
    skipped_count = 0
    not_found_tags = list(data_to_set.keys()) # Keep track of tags we need to find
    processed_elements = set() # Track element IDs to avoid processing duplicates

    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()

    # Explicitly check if collector is empty before iterating
    try:
        first_element = collector.FirstElement()
        is_empty = (first_element is None)
    except Exception as e:
        print("# Error checking collector: {}".format(e))
        is_empty = True # Assume empty on error

    if is_empty:
         print("# No Plumbing Fixture elements found in the model.")
    else:
        for element in collector:
            # Ensure it's an instance (though collector should handle this)
            if not isinstance(element, FamilyInstance):
                continue

            # Avoid processing the same element multiple times if collector somehow returns duplicates
            if element.Id in processed_elements:
                continue

            element_tag = None
            try:
                # Get the 'Mark' parameter (Tag)
                mark_param = element.get_Parameter(tag_parameter_bip)
                if mark_param and mark_param.HasValue:
                    element_tag = mark_param.AsString()

                # Check if this element's tag is in our data dictionary
                if element_tag and element_tag in data_to_set:
                    processed_elements.add(element.Id) # Mark as processed
                    if element_tag in not_found_tags:
                        not_found_tags.remove(element_tag) # Mark tag as found

                    print("\n# Processing Element: Tag='{}', ID={}".format(element_tag, element.Id))
                    new_mfr_value = data_to_set[element_tag]

                    # Get the Manufacturer parameter
                    mfr_param = element.get_Parameter(manufacturer_parameter_bip)

                    if mfr_param is None:
                        print("  - Skipping: Element does not have the Manufacturer parameter ({}).".format(manufacturer_parameter_bip))
                        skipped_count += 1
                        continue

                    if mfr_param.IsReadOnly:
                        print("  - Skipping: Manufacturer parameter is read-only.")
                        skipped_count += 1
                        continue

                    if mfr_param.StorageType != StorageType.String:
                        print("  - Skipping: Manufacturer parameter is not a String type (Actual: {}).".format(mfr_param.StorageType))
                        skipped_count += 1
                        continue

                    # Check the current value against the condition
                    current_mfr_value = mfr_param.AsString()
                    # Check if current value is None, empty string, or the specific value
                    if current_mfr_value is None or current_mfr_value.strip() == "" or current_mfr_value == overwrite_if_value:
                        try:
                            set_result = mfr_param.Set(new_mfr_value)
                            if set_result:
                                print("  - Success: Set Manufacturer to '{}' (Previous was '{}').".format(new_mfr_value, current_mfr_value if current_mfr_value is not None else "<None/Blank>"))
                                updated_count += 1
                            else:
                                print("  - Failed: Could not set Manufacturer parameter. Set method returned false.")
                                skipped_count += 1
                        except System.Exception as set_ex:
                            print("  - Failed: Error setting Manufacturer parameter: {}".format(set_ex))
                            skipped_count += 1
                    else:
                        print("  - Skipping: Current Manufacturer ('{}') does not meet condition (blank, empty, or '{}').".format(current_mfr_value, overwrite_if_value))
                        skipped_count += 1

            except System.Exception as e:
                print("# Error processing element ID {}: {}".format(element.Id if element else "Unknown", e))


    # --- Final Report ---
    print("\n# --- Update Summary ---")
    print("# Elements updated: {}".format(updated_count))
    print("# Elements skipped (condition not met, read-only, wrong type, error, etc.): {}".format(skipped_count))
    print("# Total data entries in input: {}".format(len(data_to_set)))

    if not_found_tags:
        print("# The following Tags from the input data were NOT found on any Plumbing Fixture element:")
        for tag in sorted(not_found_tags):
            print("  - {}".format(tag))
    else:
         if len(data_to_set) > 0 : # Only print all found if there was data to process
             print("# All Tags from the input data were found and processed or skipped based on condition.")

    if updated_count == 0 and skipped_count == 0 and len(data_to_set) > 0 and not is_empty:
         print("# Warning: No elements were processed. Check if 'Mark' parameters match the 'Tag' values in your input data and if plumbing fixtures exist.")
    elif is_empty and len(data_to_set) > 0:
         print("# Warning: No plumbing fixture elements exist in the model to update.")

# --- Script Finished ---