# Purpose: This script updates Revit equipment parameters based on CSV data matching equipment marks.

﻿# Ensure necessary assemblies are referenced
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')

# Import necessary namespaces and classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    Parameter,
    BuiltInParameter,
    StorageType,
    Element,
    ElementId, # Might be needed if iterating through Ids
    CategorySet,
    Category,
    ElementMulticategoryFilter # Added missing import
)
from System import String, Exception as SystemException

# --- Input Data (CSV Format) ---
csv_data = """Mark,Serial
AHU-01,SN123
AHU-02,SN456
AHU-99,SN789"""

# --- Parameters to Target ---
identifier_param_bip = BuiltInParameter.ALL_MODEL_MARK
target_param_name = "Serial Number" # Assuming this is the name of the parameter to update

# --- Parse CSV Data ---
parsed_data = {} # Dictionary { Mark: Serial }
csv_marks = set() # Set of all Marks found in the CSV
lines = csv_data.strip().split('\n')
header_found = False
if len(lines) > 0:
    # Simple header check - assumes first line is header if it contains "Mark" and "Serial" (case-insensitive)
    header_line = lines[0].lower()
    if "mark" in header_line and "serial" in header_line:
        header_found = True
        data_lines = lines[1:]
    else:
        # Assume no header if keywords not found
        print("# Warning: CSV header potentially missing or malformed. Assuming first line is data.")
        data_lines = lines

    for i, line in enumerate(data_lines):
        parts = [p.strip() for p in line.split(',')]
        if len(parts) == 2:
            mark_value = parts[0]
            serial_value = parts[1]
            if mark_value: # Ensure Mark is not empty
                if mark_value in parsed_data:
                    print("# Warning: Duplicate Mark '{}' found in CSV data (Row {}). Using the last value ('{}').".format(mark_value, i + (2 if header_found else 1), serial_value))
                parsed_data[mark_value] = serial_value
                csv_marks.add(mark_value)
            else:
                print("# Warning: Skipping CSV row {} due to empty Mark value.".format(i + (2 if header_found else 1)))
        else:
            print("# Warning: Skipping malformed CSV row {}: '{}'. Expected 2 columns.".format(i + (2 if header_found else 1), line))
else:
    print("# Error: CSV data is empty.")

# --- Collect Equipment Instances and Index by Mark ---
equipment_categories = CategorySet()
# Add common equipment categories
try:
    mech_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_MechanicalEquipment)
    elec_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_ElectricalEquipment)
    spec_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_SpecialityEquipment)
    # gen_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_GenericModel) # Optional

    if mech_cat and mech_cat.AllowsBoundParameters: equipment_categories.Insert(mech_cat)
    if elec_cat and elec_cat.AllowsBoundParameters: equipment_categories.Insert(elec_cat)
    if spec_cat and spec_cat.AllowsBoundParameters: equipment_categories.Insert(spec_cat)
    # if gen_cat and gen_cat.AllowsBoundParameters: equipment_categories.Insert(gen_cat) # Optional

except SystemException as cat_ex:
    print("# Error accessing categories: {}".format(cat_ex))

mark_to_element = {}
model_marks_found = set()
elements_processed = 0
all_equipment = [] # Initialize

# Use ElementMulticategoryFilter for efficiency if filtering by multiple categories
if not equipment_categories.IsEmpty:
    try:
        category_list = [] # ElementMulticategoryFilter requires a list of categories or BuiltInCategories
        for cat in equipment_categories:
            category_list.append(cat.Id)

        multi_cat_filter = ElementMulticategoryFilter(category_list)
        collector = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(multi_cat_filter)
        all_equipment = collector.ToElements()
        elements_processed = len(all_equipment)

        for element in all_equipment:
            # Check if it has the Mark parameter
            mark_param = element.get_Parameter(identifier_param_bip)
            if mark_param and mark_param.HasValue:
                mark_value = mark_param.AsString()
                if mark_value and mark_value.strip(): # Ensure mark is not null or whitespace
                    mark_value_clean = mark_value.strip()
                    model_marks_found.add(mark_value_clean)
                    if mark_value_clean in mark_to_element:
                        # Handle duplicate Marks found in the model
                        if isinstance(mark_to_element[mark_value_clean], list):
                            mark_to_element[mark_value_clean].append(element)
                        else: # Convert single element to list
                            mark_to_element[mark_value_clean] = [mark_to_element[mark_value_clean], element]
                        print("# Warning: Duplicate Mark '{}' found in model for Element IDs: {}".format(mark_value_clean, ", ".join([str(el.Id) for el in mark_to_element[mark_value_clean]])))
                    else:
                        mark_to_element[mark_value_clean] = element # Store single element initially
            # else: Element does not have a mark or it's empty

    except SystemException as filter_ex:
        print("# Error during element collection: {}".format(filter_ex))
        elements_processed = 0 # Reset count as collection failed

elif len(equipment_categories) == 0:
    print("# Warning: No valid equipment categories found or specified in the model.")
else:
     print("# Warning: Could not create category set for filtering or set is empty.")


# --- Counters for Summary ---
updates_applied_count = 0
errors_count = 0
warnings_count = 0
target_param_not_found = 0
target_param_read_only = 0
target_param_wrong_type = 0

# --- Iterate through Parsed Data and Update Equipment ---
if not parsed_data:
    print("# No valid data parsed from CSV to process.")
elif not mark_to_element:
    print("# No equipment elements with 'Mark' values found in the specified categories or collection failed.")
else:
    print("# Starting equipment parameter update process...")
    for mark_to_find, serial_to_set in parsed_data.items():
        if mark_to_find in mark_to_element:
            target_elements = mark_to_element[mark_to_find]
            if not isinstance(target_elements, list): # Ensure it's always a list for iteration
                target_elements = [target_elements]

            for element_instance in target_elements:
                element_info = "Element Mark '{}', ID {}".format(mark_to_find, element_instance.Id)
                try:
                    # Find the target parameter ('Serial Number') by name
                    target_param = element_instance.LookupParameter(target_param_name)

                    if target_param:
                        if target_param.IsReadOnly:
                            print("# Warning: Parameter '{}' on {} is read-only. Skipping update.".format(target_param_name, element_info))
                            warnings_count += 1
                            target_param_read_only += 1
                        elif target_param.StorageType != StorageType.String:
                            print("# Warning: Parameter '{}' on {} is not a Text parameter (Type: {}). Skipping update.".format(target_param_name, element_info, target_param.StorageType))
                            warnings_count += 1
                            target_param_wrong_type += 1
                        else:
                            # Check current value before setting
                            current_value = target_param.AsString()
                            # Treat None or empty string from parameter as different from provided serial unless serial is also empty
                            needs_update = False
                            if current_value is None: # Parameter exists but has no value
                                needs_update = bool(serial_to_set) # Update if CSV value is not empty
                            elif current_value != serial_to_set:
                                needs_update = True

                            if needs_update:
                                try:
                                    # Transaction should be handled outside this script
                                    set_result = target_param.Set(serial_to_set)
                                    if set_result:
                                        updates_applied_count += 1
                                        # print("# Success: Updated '{}' to '{}' for {}".format(target_param_name, serial_to_set, element_info)) # Verbose
                                    else:
                                        # Check if read-only again, maybe it changed?
                                        if target_param.IsReadOnly:
                                            print("# Info: Parameter '{}' on {} became read-only before update could be applied.".format(target_param_name, element_info))
                                            warnings_count += 1
                                            target_param_read_only += 1
                                        else:
                                            print("# Error: Failed to set parameter '{}' to '{}' for {} (Set returned false).".format(target_param_name, serial_to_set, element_info))
                                            errors_count += 1
                                except SystemException as set_ex:
                                    print("# Error setting parameter '{}' for {}: {}".format(target_param_name, element_info, set_ex.Message))
                                    errors_count += 1
                            # else: # Value is already correct
                                # print("# Info: Parameter '{}' already set to '{}' for {}".format(target_param_name, serial_to_set, element_info)) # Verbose

                    else:
                        # Target parameter not found on this element
                        print("# Warning: Parameter '{}' not found on {}. Skipping update.".format(target_param_name, element_info))
                        warnings_count += 1
                        target_param_not_found += 1

                except SystemException as ex:
                    print("# Error processing {}: {}".format(element_info, ex.Message))
                    errors_count += 1
        # else: Mark from CSV not found in model (handled in reporting below)

# --- Report Marks from CSV Not Found in Model ---
marks_not_found_in_model = sorted(list(csv_marks - model_marks_found))
if marks_not_found_in_model:
    print("--- Marks from CSV Not Found in Model Equipment ---")
    for mark in marks_not_found_in_model:
        print(mark)
else:
    print("--- All Marks from CSV were found in model equipment (specified categories) ---")


# --- Final Summary ---
print("--- Update Summary ---")
print("CSV Rows Parsed (excluding header): {}".format(len(parsed_data)))
print("Equipment Elements Processed (in specified categories): {}".format(elements_processed))
print("Parameter Updates Applied: {}".format(updates_applied_count))
print("--- Issues Encountered ---")
print("Updates Skipped (Parameter '{}' Not Found): {}".format(target_param_name, target_param_not_found))
print("Updates Skipped (Parameter '{}' Read-Only): {}".format(target_param_name, target_param_read_only))
print("Updates Skipped (Parameter '{}' Not Text Type): {}".format(target_param_name, target_param_wrong_type))
# Calculate other warnings count accurately
other_warnings = warnings_count - target_param_not_found - target_param_read_only - target_param_wrong_type
print("Total Other Warnings (CSV parsing, duplicate model marks, etc.): {}".format(other_warnings))
print("Errors During Update: {}".format(errors_count))
print("CSV Marks Not Found in Model: {}".format(len(marks_not_found_in_model)))
print("--- Script Finished ---")