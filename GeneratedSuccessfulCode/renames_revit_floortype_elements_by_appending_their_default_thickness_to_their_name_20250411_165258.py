# Purpose: This script renames Revit FloorType elements by appending their default thickness to their name.

﻿# Mandatory Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FloorType,
    BuiltInParameter,
    Element
)
# No clr needed for these types
# No System imports needed

# --- Script Core Logic ---

# Collect all FloorType elements
collector = FilteredElementCollector(doc).OfClass(FloorType)
floor_types = collector.ToElements() # Get the list of FloorType elements

renamed_count = 0
skipped_count = 0
error_count = 0

# Iterate through the collected floor types
for floor_type in floor_types:
    # Ensure it's actually a FloorType (robustness check)
    if not isinstance(floor_type, FloorType):
        continue

    try:
        # Get the current name of the floor type
        current_name = Element.Name.GetValue(floor_type)

        # Get the 'Default Thickness' parameter
        # BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM corresponds to "Default Thickness"
        thickness_param = floor_type.get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM)

        if thickness_param and thickness_param.HasValue:
            # Get thickness as a string formatted according to project units
            # AsValueString() typically provides a user-friendly representation
            thickness_str = thickness_param.AsValueString()

            # Proceed only if a valid thickness string was obtained
            if thickness_str and thickness_str.strip(): # Check not None or empty/whitespace
                # Sanitize the thickness string slightly (e.g., replace common problematic chars if needed, though often not necessary)
                # For simplicity, we'll use it directly here.
                clean_thickness_str = thickness_str.strip()

                # Define the suffix to append
                suffix_to_add = " - {}".format(clean_thickness_str)

                # Construct the potential new name
                new_name = "{}{}".format(current_name, suffix_to_add)

                # Check if renaming is necessary:
                # 1. Is the new name different from the current name?
                # 2. Does the current name already end with the exact suffix we plan to add? (Prevents duplicates)
                if current_name != new_name and not current_name.endswith(suffix_to_add):
                    try:
                        # Rename the floor type (Transaction is handled externally by the C# wrapper)
                        floor_type.Name = new_name
                        renamed_count += 1
                        # print("# Renamed '{}' to '{}'".format(current_name, new_name)) # Debug info
                    except Exception as rename_err:
                        # Handle potential errors during renaming (e.g., duplicate names, invalid characters)
                        error_count += 1
                        # print("# Error renaming FloorType '{}' (ID: {}) to '{}': {}".format(current_name, floor_type.Id, new_name, rename_err)) # Debug info
                else:
                    # Skipping because name is already correct or already has the suffix
                    skipped_count += 1
                    # print("# Skipping FloorType '{}' (ID: {}), name already correct or ends with suffix.".format(current_name, floor_type.Id)) # Debug info
            else:
                # Thickness parameter exists but couldn't get a valid string value
                skipped_count += 1
                # print("# Skipping FloorType '{}' (ID: {}), could not retrieve thickness as a valid string.".format(current_name, floor_type.Id)) # Debug info

        else:
            # Thickness parameter not found or has no value
            skipped_count += 1
            # print("# Skipping FloorType '{}' (ID: {}), 'Default Thickness' parameter not found or has no value.".format(current_name, floor_type.Id)) # Debug info

    except Exception as e:
        # Catch-all for errors processing a specific floor type
        error_count += 1
        try:
            # Try to get name for error message, otherwise use ID
            name_for_error = Element.Name.GetValue(floor_type)
        except:
            name_for_error = "ID: {}".format(floor_type.Id)
        # print("# Error processing FloorType '{}': {}".format(name_for_error, e)) # Debug info

# Optional: Print a summary to the console/output window (useful for debugging in RPS/pyRevit)
# print("--- Floor Type Renaming Summary ---")
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (already correct/no thickness/no value): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Floor Types processed: {}".format(len(floor_types)))