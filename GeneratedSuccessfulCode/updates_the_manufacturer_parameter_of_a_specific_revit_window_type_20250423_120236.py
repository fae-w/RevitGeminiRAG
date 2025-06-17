# Purpose: This script updates the manufacturer parameter of a specific Revit window type.

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
    BuiltInParameter,
    Element
)

# --- Configuration ---
target_type_name = "Fixed Window - 600x1200"
new_manufacturer_value = "Vision Glass Ltd."
target_parameter_bip = BuiltInParameter.ALL_MODEL_MANUFACTURER # 'Manufacturer' built-in parameter

# --- Initialization ---
found_type = None
update_successful = False
error_message = None

# --- Step 1: Collect and Find the specific Window Type ---
try:
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsElementType()
    window_types = list(collector)

    for wt_element in window_types:
        # Ensure it's an ElementType or derived class
        if not isinstance(wt_element, ElementType):
            continue

        # Check the name using the recommended property access
        element_name = Element.Name.GetValue(wt_element)
        if element_name == target_type_name:
            found_type = wt_element
            break # Found the type, no need to continue loop

    # --- Step 2: Update the parameter if the type was found ---
    if found_type:
        try:
            # Get the Manufacturer parameter using BuiltInParameter
            manufacturer_param = found_type.get_Parameter(target_parameter_bip)

            if manufacturer_param is None:
                error_message = "# Error: Window Type '{}' does not have the Manufacturer parameter.".format(target_type_name)
            elif manufacturer_param.IsReadOnly:
                error_message = "# Error: Manufacturer parameter for Window Type '{}' is read-only.".format(target_type_name)
            elif manufacturer_param.StorageType != StorageType.String:
                error_message = "# Error: Manufacturer parameter for Window Type '{}' is not a String type ({}).".format(target_type_name, manufacturer_param.StorageType)
            else:
                # Set the new value
                set_result = manufacturer_param.Set(new_manufacturer_value)
                if set_result:
                    update_successful = True
                    # print("# Successfully updated Manufacturer for '{}' to '{}'.".format(target_type_name, new_manufacturer_value)) # Optional success message
                else:
                    # This might happen if the value is disallowed for some reason
                    error_message = "# Error: Failed to set Manufacturer for Window Type '{}'. Parameter.Set returned False.".format(target_type_name)

        except SystemException as param_ex:
            error_message = "# Error accessing/setting parameter for Window Type '{}': {}".format(target_type_name, param_ex.Message)
    else:
        error_message = "# Error: Window Type with name '{}' not found in the document.".format(target_type_name)

except SystemException as col_ex:
    # Error during the collection phase
    error_message = "# Error collecting Window Types: {}".format(col_ex.Message)

# --- Final Feedback ---
if error_message:
    print(error_message)
# No explicit success message unless uncommented above, as per requirements.