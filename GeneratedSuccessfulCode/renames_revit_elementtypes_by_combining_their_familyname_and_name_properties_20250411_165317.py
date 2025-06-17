# Purpose: This script renames Revit ElementTypes by combining their FamilyName and Name properties.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementType,
    Element # Needed for Element.Name static methods
)

# --- Script Core Logic ---

# Collect all ElementType elements in the document
collector = FilteredElementCollector(doc).OfClass(ElementType)

renamed_count = 0
skipped_count = 0
error_count = 0
processed_count = 0

# Iterate through the collected element types
for element_type in collector:
    processed_count += 1
    # Defensive check, although collector should only return ElementTypes
    if not isinstance(element_type, ElementType):
        skipped_count += 1
        continue

    try:
        # Get the family name and the current type name
        # Some element types might not have a meaningful family name concept (e.g., ViewFamilyType)
        # but the property should still exist. Handle potential None or empty strings.
        family_name = element_type.FamilyName
        current_name = Element.Name.GetValue(element_type)

        # Ensure both names are valid strings before proceeding
        if not family_name or not isinstance(family_name, basestring) or not current_name or not isinstance(current_name, basestring):
            # print(f"# Skipping ElementType ID {element_type.Id}: Invalid FamilyName ('{family_name}') or Current Name ('{current_name}').") # Debug
            skipped_count += 1
            continue

        # Construct the potential new name, stripping whitespace just in case
        family_name_clean = family_name.strip()
        current_name_clean = current_name.strip()
        if not family_name_clean or not current_name_clean:
            skipped_count += 1
            continue # Skip if either part becomes empty after stripping

        new_name = "{}_{}".format(family_name_clean, current_name_clean)

        # Define the expected prefix for checking if already renamed
        expected_prefix = "{}_".format(family_name_clean)

        # Check if renaming is needed:
        # 1. New name is different from current name.
        # 2. Current name does not already start with the 'FamilyName_' prefix.
        #    (Case-sensitive check is standard for Revit names)
        if current_name != new_name and not current_name.startswith(expected_prefix):
            try:
                # Rename the element type (Transaction handled externally)
                element_type.Name = new_name
                renamed_count += 1
                # print(f"# Renamed Type ID {element_type.Id}: '{current_name}' to '{new_name}'") # Debug
            except Exception as rename_error:
                # Handle potential errors during renaming (e.g., duplicate names, invalid characters)
                error_count += 1
                # print(f"# Error renaming Type ID {element_type.Id} ('{current_name}' to '{new_name}'): {rename_error}") # Debug
        else:
            # Skipped because name didn't change or already has the prefix
            skipped_count += 1
            # if current_name == new_name:
            #    print(f"# Skipping Type ID {element_type.Id} ('{current_name}'): New name is the same.") # Debug
            # elif current_name.startswith(expected_prefix):
            #     print(f"# Skipping Type ID {element_type.Id} ('{current_name}'): Already appears to have prefix '{expected_prefix}'.") # Debug

    except Exception as e:
        # General error handling for processing a specific element type
        # e.g., accessing properties failed for some reason
        error_count += 1
        try:
            # Try to get the name for the error message
            name_for_error = Element.Name.GetValue(element_type) if element_type else "Unknown Element"
        except:
            name_for_error = "ID {}".format(element_type.Id) if element_type else "Unknown Element" # Fallback
        # print(f"# Error processing ElementType '{name_for_error}': {e}") # Debug

# Optional: Print summary (commented out by default as per instructions)
# print("--- ElementType Renaming Summary ---")
# print("Total ElementTypes processed: {}".format(processed_count))
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (no change/already prefixed/invalid names): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))