# Purpose: This script updates the 'Manufacturer' parameter for Revit window types if it is empty.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String operations and Exception handling
from System import String, Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementType,
    FamilySymbol, # Window types are typically FamilySymbols
    Parameter,
    StorageType,
    BuiltInParameter
)

# --- Configuration ---
new_manufacturer_value = "Default Manufacturer"
target_parameter_bip = BuiltInParameter.ALL_MODEL_MANUFACTURER # 'Manufacturer' built-in parameter

# --- Initialization ---
updated_count = 0
skipped_no_param = 0
skipped_read_only = 0
skipped_already_set = 0
skipped_wrong_type = 0
error_count = 0
processed_count = 0

# --- Step 1: Collect Window Types ---
# Collect ElementTypes belonging to the OST_Windows category
try:
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsElementType()
    window_types = list(collector)
    processed_count = len(window_types)

    # --- Step 2 & 3: Iterate and Update ---
    for wt_element in window_types:
        # Ensure it's a FamilySymbol or at least ElementType, although collector should handle this
        if not isinstance(wt_element, ElementType):
            skipped_wrong_type += 1
            continue

        current_name = Element.Name.GetValue(wt_element) # For logging errors

        try:
            # Get the Manufacturer parameter using BuiltInParameter
            manufacturer_param = wt_element.get_Parameter(target_parameter_bip)

            if manufacturer_param is None:
                skipped_no_param += 1
                # print("# Info: Window Type ID {{}} ('{{}}') does not have the Manufacturer parameter. Skipping.".format(wt_element.Id, current_name)) # Debug
                continue

            if manufacturer_param.IsReadOnly:
                skipped_read_only += 1
                # print("# Info: Manufacturer parameter for Window Type ID {{}} ('{{}}') is read-only. Skipping.".format(wt_element.Id, current_name)) # Debug
                continue

            # Verify storage type is String
            if manufacturer_param.StorageType != StorageType.String:
                skipped_wrong_type += 1
                # print("# Info: Manufacturer parameter for Window Type ID {{}} ('{{}}') is not a String type ({{}}). Skipping.".format(wt_element.Id, current_name, manufacturer_param.StorageType)) # Debug
                continue

            # Get the current value
            current_value = manufacturer_param.AsString()

            # Check if the current value is null, empty, or whitespace
            if String.IsNullOrWhiteSpace(current_value):
                # Set the new value
                set_result = manufacturer_param.Set(new_manufacturer_value)
                if set_result:
                    updated_count += 1
                    # print("# Updated Manufacturer for Window Type ID {{}} ('{{}}') to '{{}}'".format(wt_element.Id, current_name, new_manufacturer_value)) # Debug
                else:
                    # This might happen if the value is disallowed for some reason
                    error_count += 1
                    print("# Error: Failed to set Manufacturer for Window Type ID {{}} ('{{}}'). Parameter.Set returned False.".format(wt_element.Id, current_name))
            else:
                # The parameter already has a value
                skipped_already_set += 1
                # print("# Info: Window Type ID {{}} ('{{}}') already has Manufacturer value: '{{}}'. Skipping.".format(wt_element.Id, current_name, current_value)) # Debug

        except SystemException as param_ex:
            error_count += 1
            print("# Error processing Window Type ID {{}} ('{{}}'): {{}}".format(wt_element.Id, current_name, param_ex.Message))

except SystemException as col_ex:
    # Error during the collection phase
    print("# Error collecting Window Types: {{}}".format(col_ex.Message))
    error_count += 1

# --- Final Summary --- (Optional: uncomment if needed for debugging)
# print("# --- Window Type Manufacturer Update Summary ---")
# print("# Total Window Types processed: {{}}".format(processed_count))
# print("# Successfully Updated: {{}}".format(updated_count))
# print("# Skipped (No Manufacturer Param): {{}}".format(skipped_no_param))
# print("# Skipped (Param Read-Only): {{}}".format(skipped_read_only))
# print("# Skipped (Param Not String): {{}}".format(skipped_wrong_type)) # Includes non-ElementType check
# print("# Skipped (Already Has Value): {{}}".format(skipped_already_set))
# print("# Errors Encountered: {{}}".format(error_count))
# if error_count > 0:
#     print("# Review errors printed above for details.")