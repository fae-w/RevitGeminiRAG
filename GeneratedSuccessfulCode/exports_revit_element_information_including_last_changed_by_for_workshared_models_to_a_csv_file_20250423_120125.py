# Purpose: This script exports Revit element information, including 'Last Changed By' for workshared models, to a CSV file.

﻿# -*- coding: utf-8 -*-
import clr
import System

# Add references to Revit API assemblies
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Not strictly needed for this task, but good practice if uidoc might be used elsewhere

# Import necessary classes from Revit API namespaces
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Element,
    ElementType,
    ElementId,
    Category,
    BuiltInCategory,
    WorksharingUtils,
    WorksharingTooltipInfo
)
# Import .NET date/time types
from System import DateTime, String

# List to hold CSV data rows
csv_lines = []

# Add header row
# Note: Filtering by "last modified today" is not directly supported by the standard Revit API
# for individual element modification times. The 'Last Changed By' reflects the user
# who last saved to central after modifying the element in a workshared model.
# This script will export all elements with the available 'Last Changed By' info.
csv_lines.append('"Element ID","Category Name","Type Name","Last Changed By (Worksharing)"')

# Helper function for CSV quoting and escaping
def escape_csv(value):
    """Escapes a value for safe inclusion in a CSV cell."""
    if value is None:
        return '""'
    # Ensure value is a string before replacing quotes
    str_value = System.Convert.ToString(value)
    # Replace double quotes with two double quotes and enclose in double quotes
    return '"' + str_value.replace('"', '""') + '"'

# Check if the model is workshared, as 'Last Changed By' is a worksharing feature
is_workshared = doc.IsWorkshared

# Collect all elements in the document (excluding element types for efficiency)
collector = FilteredElementCollector(doc).WhereElementIsNotElementType()

# Iterate through collected elements
for element in collector:
    elem_id_str = "N/A"
    category_name = "N/A"
    type_name = "N/A"
    last_changed_by = "N/A" # Default value

    try:
        # Get Element ID
        elem_id_str = element.Id.ToString()

        # Get Category Name
        cat = element.Category
        if cat is not None and cat.Name:
            category_name = cat.Name
        elif cat is not None:
             category_name = "Unnamed Category" # Handle cases where category exists but name is empty

        # Get Type Name
        type_id = element.GetTypeId()
        if type_id is not None and type_id != ElementId.InvalidElementId:
            elem_type = doc.GetElement(type_id)
            if elem_type is not None and isinstance(elem_type, ElementType):
                 # ElementType.Name might be editable, Parameter BuiltInParameter.SYMBOL_NAME_PARAM is often more reliable
                 # but ElementType.Name is usually sufficient and simpler.
                 t_name = elem_type.Name
                 if not String.IsNullOrEmpty(t_name):
                     type_name = t_name
                 else:
                     # Fallback: Check family name if type name is empty
                     if hasattr(elem_type, 'FamilyName') and not String.IsNullOrEmpty(elem_type.FamilyName):
                         type_name = elem_type.FamilyName + " (Family Name)"
                     else:
                         type_name = "Unnamed Type"
            elif elem_type is not None:
                 # If GetTypeId returns an element that isn't an ElementType, use its name if available
                 if hasattr(elem_type, 'Name') and not String.IsNullOrEmpty(elem_type.Name):
                      type_name = elem_type.Name + " (Non-ElementType)"
                 else:
                     type_name = "Invalid Type Element"

        # Get 'Last Changed By' from Worksharing Tooltip Info (if workshared)
        if is_workshared:
            try:
                tooltip_info = WorksharingUtils.GetWorksharingTooltipInfo(doc, element.Id)
                if tooltip_info is not None:
                    # The LastChangedBy property contains the username
                    lc_user = tooltip_info.LastChangedBy
                    if not String.IsNullOrEmpty(lc_user):
                        last_changed_by = lc_user
                    else:
                        last_changed_by = "(not specified)"
                # else: tooltip_info is None, last_changed_by remains "N/A"
            except Exception as ws_ex:
                # Handle potential errors retrieving worksharing info for specific elements
                last_changed_by = "Error getting WS info"
        else:
            last_changed_by = "(Not Workshared)" # Indicate model isn't workshared

        # Escape values for CSV
        safe_id = escape_csv(elem_id_str)
        safe_cat_name = escape_csv(category_name)
        safe_type_name = escape_csv(type_name)
        safe_last_changed = escape_csv(last_changed_by)

        # Append data row to the list
        csv_lines.append(','.join([safe_id, safe_cat_name, safe_type_name, safe_last_changed]))

    except Exception as e:
        # Optional: Log errors for debugging specific elements
        # print("# Error processing element ID {{{{}}}}: {{{{}}}}".format(elem_id_str, e))
        try:
             error_id_str = element.Id.ToString()
        except:
             error_id_str = "Unknown ID"
        csv_lines.append(','.join([escape_csv(error_id_str), escape_csv("ERROR"), escape_csv(str(e)), escape_csv("ERROR")]))

# Check if we gathered any data (more than just the header)
if len(csv_lines) > 1:
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    # Suggest a filename
    filename_suggestion = "element_modification_info.csv"
    # Add project name prefix if possible
    try:
        if doc.Title:
             proj_name = doc.Title.replace(' ', '_').replace('.rvt', '')
             filename_suggestion = proj_name + "_" + filename_suggestion
    except:
        pass # Ignore errors getting document title

    print("EXPORT::CSV::" + filename_suggestion)
    print(file_content)
else:
    # If no elements were processed (or only the header exists)
    print("# No elements found or processed in the document.")

# Reminder Comment (will be ignored by execution wrapper, but useful for humans)
# The Revit API does not provide a reliable way to filter elements based on the exact date/time
# they were last modified. The 'Last Changed By' field reflects worksharing history
# (user who last saved to central after changes) and does not include a timestamp accessible here.
# Therefore, this script exports data for all non-type elements.