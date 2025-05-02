# Purpose: This script extracts Revit project warnings and exports them to a CSV file.

﻿# -*- coding: utf-8 -*-
import clr
import System

# Import necessary classes from Revit API namespaces
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FailureMessage, ElementId

# List to hold CSV data rows
csv_lines = []

# Add header row
csv_lines.append('"Warning Description","Element IDs"')

# Helper function for CSV quoting and escaping
def escape_csv(value):
    """Escapes a value for safe inclusion in a CSV cell."""
    if value is None:
        return '""'
    # Ensure value is a string before replacing quotes
    str_value = System.Convert.ToString(value)
    # Replace double quotes with two double quotes and enclose in double quotes
    return '"' + str_value.replace('"', '""') + '"'

# Get all warnings in the document
try:
    warnings = doc.GetWarnings()
except Exception as e:
    # print("# Error retrieving warnings from the document: {{}}".format(e)) # Optional Debug
    warnings = None # Ensure warnings is None or an empty list if retrieval fails

# Check if there are any warnings and the list is not None
if warnings and warnings.Count > 0:
    # Iterate through collected warnings
    for warning in warnings:
        if isinstance(warning, FailureMessage):
            try:
                # Get Warning Description
                description = warning.GetDescriptionText()
                if not description:
                    description = "(No description provided)"

                # Get Failing Element IDs
                failing_elements_ids_collection = warning.GetFailingElements()
                element_ids_str = ""
                if failing_elements_ids_collection and failing_elements_ids_collection.Count > 0:
                    # Create a list of ElementId strings
                    id_list = []
                    for eid in failing_elements_ids_collection:
                         # Check if ElementId is valid before accessing IntegerValue
                         if eid and eid != ElementId.InvalidElementId:
                             id_list.append(str(eid.IntegerValue))
                         else:
                             id_list.append("Invalid")
                    # Join element IDs with a semicolon separator (safer for CSV)
                    element_ids_str = "; ".join(id_list)
                else:
                    # Indicate if no specific elements are associated
                    element_ids_str = "N/A"

                # Escape values for CSV
                safe_description = escape_csv(description)
                safe_element_ids = escape_csv(element_ids_str)

                # Append data row to the list
                csv_lines.append(','.join([safe_description, safe_element_ids]))

            except Exception as e:
                # Log error for specific warning processing if needed
                # print("# Error processing warning: {{}}".format(e)) # Optional Debug
                try:
                    # Try to get description even in error case for context
                    desc_error = warning.GetDescriptionText() if warning else "Unknown Warning"
                    csv_lines.append(','.join([escape_csv("ERROR processing: " + desc_error), escape_csv(str(e))]))
                except:
                    csv_lines.append(','.join([escape_csv("ERROR processing unknown warning"), escape_csv(str(e))]))
                # Continue with the next warning even if one fails
                pass

# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::project_warnings_report.csv")
    print(file_content)
else:
    # If no warnings were found or processed successfully, or if GetWarnings failed initially
    if warnings is None:
        print("# Failed to retrieve warnings from the project.")
    elif warnings.Count == 0:
        print("# No warnings found in the project.")
    else:
        print("# No warnings processed successfully, though some might exist.")