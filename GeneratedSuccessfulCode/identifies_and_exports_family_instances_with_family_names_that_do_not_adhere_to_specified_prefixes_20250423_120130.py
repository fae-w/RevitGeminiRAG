# Purpose: This script identifies and exports family instances with family names that do not adhere to specified prefixes.

﻿# -*- coding: utf-8 -*-
import clr
import System

# Import necessary classes from Revit API namespaces
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilyInstance,
    FamilySymbol,
    Family,
    ElementId,
    Element
)
from System import String # For checking null or empty strings

# Define the required prefixes
required_prefixes = ('ARC_', 'STR_', 'MEP_') # Case-sensitive

# List to hold CSV lines for Excel export
csv_lines = []
# Add header row - ensuring quotes for safety
csv_lines.append('"Element ID","Family Name","Type Name"')

# Helper function for CSV quoting and escaping
def escape_csv(value):
    """Escapes a value for safe inclusion in a CSV cell."""
    if value is None:
        return '""'
    # Ensure value is a string before replacing quotes
    str_value = System.Convert.ToString(value)
    # Replace double quotes with two double quotes and enclose in double quotes
    return '"' + str_value.replace('"', '""') + '"'

# Collect all FamilyInstance elements in the document
collector = FilteredElementCollector(doc).OfClass(FamilyInstance)

processed_count = 0
# Iterate through collected family instances
for inst in collector:
    if not isinstance(inst, FamilyInstance):
        continue # Should not happen with OfClass filter, but safety check

    family_name = "Unknown Family"
    type_name = "Unknown Type"
    family_name_compliant = True # Assume compliant initially

    try:
        # Get the FamilySymbol (Type) of the instance using GetTypeId
        symbol_id = inst.GetTypeId()
        if symbol_id is not None and symbol_id != ElementId.InvalidElementId:
            symbol = doc.GetElement(symbol_id)
            if symbol is not None and isinstance(symbol, FamilySymbol):
                type_name = symbol.Name # Get Type Name

                # Get the Family from the FamilySymbol
                family = symbol.Family
                if family is not None:
                    family_name = family.Name # Get Family Name

                    # Check if Family Name is valid and starts with one of the required prefixes
                    if not String.IsNullOrEmpty(family_name):
                        # Check if the name starts with ANY of the prefixes in the tuple
                        if not family_name.startswith(required_prefixes):
                            family_name_compliant = False
                    else:
                         # Consider empty/null family name as non-compliant
                         family_name = "(Empty Family Name)"
                         family_name_compliant = False
                else:
                    # Family object not found - treat as potentially non-compliant or error
                    family_name = "(Family Not Found)"
                    family_name_compliant = False # Treat error case as non-compliant for reporting
            else:
                 # Type element is not a FamilySymbol
                 type_name = "(Type is not FamilySymbol)"
                 family_name_compliant = False # Treat error case as non-compliant for reporting
        else:
             # Instance has no valid type ID
             type_name = "(Invalid Type ID)"
             family_name_compliant = False # Treat error case as non-compliant for reporting


        # If the family name is not compliant, add it to the list
        if not family_name_compliant:
            element_id_str = inst.Id.ToString()

            # Escape values for CSV/Excel
            safe_elem_id = escape_csv(element_id_str)
            safe_family_name = escape_csv(family_name)
            safe_type_name = escape_csv(type_name)

            # Append data row
            csv_lines.append(','.join([safe_elem_id, safe_family_name, safe_type_name]))
            processed_count += 1

    except Exception as e:
        # Optional: Log errors for specific elements during debugging
        # print("# Error processing element ID {{}}: {{}}".format(inst.Id.ToString(), e))
        try:
            # Attempt to add an error row to the export
            error_id = escape_csv(inst.Id.ToString())
            error_fam = escape_csv("ERROR processing")
            error_type = escape_csv(str(e))
            csv_lines.append(','.join([error_id, error_fam, error_type]))
        except:
            pass # Ignore errors during error logging

# Check if we gathered any non-compliant data (more than just the header)
if processed_count > 0:
    # Format the final output for export as Excel (using CSV data)
    file_content = "\n".join(csv_lines)
    filename_suggestion = "non_compliant_family_names.xlsx"
     # Add project name prefix if possible
    try:
        if doc.Title and not String.IsNullOrEmpty(doc.Title):
             proj_name_raw = doc.Title
             # Remove invalid characters for filenames
             invalid_chars = r'<>:"/\|?*'
             proj_name_clean = "".join(c for c in proj_name_raw if c not in invalid_chars)
             proj_name = proj_name_clean.replace(' ', '_').replace('.rvt', '')
             if proj_name: # Ensure proj_name is not empty after cleaning
                 filename_suggestion = proj_name + "_" + filename_suggestion
    except:
        pass # Ignore errors getting document title

    print("EXPORT::EXCEL::" + filename_suggestion)
    print(file_content)
else:
    # If only the header exists, print a message indicating no non-compliant families were found
    print("# No placed family instances found whose Family Name does not start with {}.".format(" or ".join(required_prefixes)))