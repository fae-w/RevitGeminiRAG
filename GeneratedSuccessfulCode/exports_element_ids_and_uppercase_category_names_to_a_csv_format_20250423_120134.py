# Purpose: This script exports element IDs and uppercase category names to a CSV format.

﻿# -*- coding: utf-8 -*-
import clr
import System

# Add references to Revit API assemblies
clr.AddReference('RevitAPI')

# Import necessary classes from Revit API namespaces
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Element,
    ElementId,
    Category,
    BuiltInCategory
)

# List to hold CSV data rows
csv_lines = []

# Add header row
csv_lines.append('"Element ID","Category Name (Uppercase)"')

# Helper function for CSV quoting and escaping
def escape_csv(value):
    """Escapes a value for safe inclusion in a CSV cell."""
    if value is None:
        return '""'
    # Ensure value is a string before replacing quotes
    str_value = System.Convert.ToString(value)
    # Replace double quotes with two double quotes and enclose in double quotes
    return '"' + str_value.replace('"', '""') + '"'

# Collect all elements in the document - ADDING THE REQUIRED FILTER
# Using WhereElementIsNotElementType() is common to get instances
collector = FilteredElementCollector(doc).WhereElementIsNotElementType()

# Iterate through collected elements
for element in collector:
    elem_id_int = -1 # Default invalid ID
    category_name_upper = "N/A" # Default category name

    try:
        # Get Element ID
        elem_id_int = element.Id.IntegerValue

        # Get Category
        category = element.Category

        if category is not None:
            # Get Category Name and convert to uppercase
            cat_name_raw = category.Name
            if cat_name_raw: # Check if name is not empty or None
                 category_name_upper = cat_name_raw.upper()
            else:
                 category_name_upper = "NO NAME" # Handle case where category exists but name is empty/None
        # else: category_name_upper remains "N/A"

        # Escape values for CSV
        safe_id = escape_csv(elem_id_int)
        safe_cat_name = escape_csv(category_name_upper)

        # Append data row to the list
        csv_lines.append(','.join([safe_id, safe_cat_name]))

    except Exception as e:
        # Optional: Log errors for debugging specific elements
        # print("# Error processing element ID {{}}: {{}}".format(elem_id_int if elem_id_int != -1 else 'Unknown', e))
        # Append error row if needed, or skip
        try:
            error_id = element.Id.IntegerValue
        except:
            error_id = "Unknown ID"
        # csv_lines.append(','.join([escape_csv(error_id), escape_csv("ERROR: " + str(e))]))
        pass # Silently skip elements that cause errors

# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::element_categories_uppercase.csv")
    print(file_content)
else:
    # If no elements were processed (or only the header exists)
    print("# No elements found or processed in the document.")