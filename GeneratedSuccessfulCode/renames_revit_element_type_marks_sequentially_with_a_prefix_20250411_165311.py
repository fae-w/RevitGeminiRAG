# Purpose: This script renames Revit element type marks sequentially with a prefix.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementType, # Explicitly import ElementType although collector yields Element
    ElementId,
    Parameter
)

# --- Configuration ---
# Define the category to process
TARGET_CATEGORY = BuiltInCategory.OST_Windows
# Define the parameter to modify
TARGET_PARAMETER = BuiltInParameter.ALL_MODEL_TYPE_MARK
# Define the prefix for the new Type Mark
NEW_PREFIX = "W-"
# Define the number of digits for zero-padding (e.g., 2 for 01, 3 for 001)
PADDING_DIGITS = 2

# --- Initialization ---
renamed_count = 0
skipped_count = 0
error_count = 0
counter = 1 # Start numbering from 1

# --- Script Core Logic ---
try:
    # Collect all element types of the specified category
    collector = FilteredElementCollector(doc).OfCategory(TARGET_CATEGORY).WhereElementIsElementType()
    element_types = list(collector) # Convert iterator to list for sorting

    if not element_types:
        print("# Info: No element types found for category '{}'.".format(TARGET_CATEGORY))
    else:
        # Sort element types to ensure consistent numbering (optional, sorting by Name might be more intuitive for users)
        # Sorting by Name:
        try:
            element_types.sort(key=lambda et: et.Name)
        except AttributeError: # Handle potential cases where Name might not be directly available (unlikely for types)
             print("# Warning: Could not sort element types by name, proceeding without sorting.")


        # Iterate through the sorted element types
        for elem_type in element_types:
            # Ensure it's actually an ElementType (though the filter should guarantee this)
            if not isinstance(elem_type, ElementType):
                 skipped_count += 1
                 # print("# Skipping element ID {}: Not an ElementType.".format(elem_type.Id)) # Debug
                 continue

            try:
                # Get the 'Type Mark' parameter
                type_mark_param = elem_type.get_Parameter(TARGET_PARAMETER)

                if type_mark_param is None:
                    skipped_count += 1
                    # print("# Info: Type '{}' (ID: {}) does not have parameter '{}'. Skipping.".format(elem_type.Name, elem_type.Id, TARGET_PARAMETER)) # Debug
                    continue

                if type_mark_param.IsReadOnly:
                    skipped_count += 1
                    # print("# Info: Parameter '{}' for Type '{}' (ID: {}) is read-only. Skipping.".format(TARGET_PARAMETER, elem_type.Name, elem_type.Id)) # Debug
                    continue

                # Construct the new sequential Type Mark value
                # Format string like "W-{:02d}" or "W-{:03d}" based on PADDING_DIGITS
                format_string = NEW_PREFIX + "{:0" + str(PADDING_DIGITS) + "d}"
                new_type_mark = format_string.format(counter)

                # Set the new value for the Type Mark parameter
                # The Set method requires a string for Text parameters like Type Mark
                set_result = type_mark_param.Set(new_type_mark)

                if set_result:
                    renamed_count += 1
                    counter += 1 # Increment counter only on successful rename
                    # print("# Renamed Type Mark for '{}' (ID: {}) to '{}'".format(elem_type.Name, elem_type.Id, new_type_mark)) # Debug
                else:
                    error_count += 1
                    # print("# Error: Failed to set Type Mark for '{}' (ID: {}) to '{}'. Parameter.Set returned False.".format(elem_type.Name, elem_type.Id, new_type_mark)) # Debug

            except SystemException as param_ex:
                error_count += 1
                type_name = "Unknown"
                type_id_str = "Unknown"
                try:
                    type_name = elem_type.Name
                    type_id_str = elem_type.Id.ToString()
                except: pass # Ignore errors getting name/id for error message itself
                print("# Error processing Type '{}' (ID: {}): {}".format(type_name, type_id_str, param_ex.Message))

        # --- Final Summary --- (Optional: uncomment if needed, keep commented for standard operation)
        # print("# --- Type Mark Renaming Summary ---")
        # print("# Category Processed: {}".format(TARGET_CATEGORY))
        # print("# Total Types Found: {}".format(len(element_types)))
        # print("# Successfully Renamed: {}".format(renamed_count))
        # print("# Skipped (No param/Read-only/Not Type): {}".format(skipped_count))
        # print("# Errors Encountered: {}".format(error_count))
        # if error_count > 0:
        #     print("# Review errors printed above for details.")

except SystemException as general_ex:
    print("# Error during element collection or processing: {}".format(general_ex.Message))