# Purpose: This script exports Revit elements created by a specified user in a workshared model to a CSV format.

﻿# -*- coding: utf-8 -*-
import clr
import System

# Add references to Revit API assemblies
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Not strictly needed, but good practice

# Import necessary classes from Revit API namespaces
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Element,
    ElementType,
    ElementId,
    Category,
    WorksharingUtils,
    WorksharingTooltipInfo
)
# Import .NET types
from System import String

# --- User Configuration ---
# Specify the username to filter by (case-insensitive)
target_username = "jsmith"
# --- End User Configuration ---

# List to hold CSV data rows for Excel export
csv_lines = []

# Add header row
# NOTE: The Revit API does not provide a reliable 'Date Created' property for elements,
# nor does it allow filtering by creation within the 'current project session'.
# This script will export elements CREATED BY the specified user in a workshared model,
# but cannot include the creation date or session filter.
csv_lines.append('"Element ID","Category Name","Created By (Worksharing)"')

# Helper function for CSV quoting and escaping
def escape_csv(value):
    """Escapes a value for safe inclusion in a CSV cell."""
    if value is None:
        return '""'
    str_value = System.Convert.ToString(value)
    return '"' + str_value.replace('"', '""') + '"'

# Check if the model is workshared, as 'Created By' is a worksharing feature
is_workshared = doc.IsWorkshared
elements_found = 0

if is_workshared:
    # Collect all model elements (excluding element types and view-specific elements)
    # Using WhereElementIsNotElementType() and WhereElementIsViewIndependent() is a common
    # way to approximate "model elements".
    collector = FilteredElementCollector(doc).WhereElementIsNotElementType().WhereElementIsViewIndependent()

    # Iterate through collected elements
    for element in collector:
        element_id_str = "N/A"
        category_name = "N/A"
        created_by = "N/A"

        try:
            # Get Element ID
            element_id_str = element.Id.ToString()

            # Get Category Name
            cat = element.Category
            if cat is not None and cat.Name:
                category_name = cat.Name
            elif cat is not None:
                category_name = "Unnamed Category"

            # Get 'Created By' from Worksharing Tooltip Info
            try:
                tooltip_info = WorksharingUtils.GetWorksharingTooltipInfo(doc, element.Id)
                if tooltip_info is not None:
                    creator = tooltip_info.CreatedBy
                    if not String.IsNullOrEmpty(creator):
                        # Check if the creator matches the target username (case-insensitive)
                        if System.String.Equals(creator, target_username, System.StringComparison.OrdinalIgnoreCase):
                            # Escape values for CSV
                            safe_id = escape_csv(element_id_str)
                            safe_cat_name = escape_csv(category_name)
                            safe_created_by = escape_csv(creator) # Store the actual creator found

                            # Append data row to the list
                            csv_lines.append(','.join([safe_id, safe_cat_name, safe_created_by]))
                            elements_found += 1
                    else:
                         # If creator is empty, we don't match target_username, but record it if needed
                         # created_by = "(not specified)"
                         pass # Don't add if creator is empty and doesn't match
                # else: tooltip_info is None, created_by remains "N/A", no match possible

            except Exception as ws_ex:
                # Handle potential errors retrieving worksharing info
                created_by = "Error getting WS info"
                # Optionally add an error row if needed for debugging
                # csv_lines.append(','.join([escape_csv(element_id_str), escape_csv("ERROR"), escape_csv("WS Info Error: " + str(ws_ex))]))


        except Exception as e:
            # Log errors for specific elements if needed during development
            # print("# Error processing element ID {{0}}: {{1}}".format(element_id_str, e))
            try:
                 error_id_str = element.Id.ToString()
            except:
                 error_id_str = "Unknown ID"
            # Add an error row to the CSV for context
            csv_lines.append(','.join([escape_csv(error_id_str), escape_csv("ERROR processing element"), escape_csv(str(e))]))

else:
    # If the model is not workshared, print a message and don't export data
    print("# Error: Model is not workshared. Cannot retrieve 'Created By' information.")
    # Ensure csv_lines only contains the header if we exit here
    csv_lines = [csv_lines[0]] # Keep only header

# Check if we gathered any valid data rows (more than just the header)
if elements_found > 0:
    # Format the final output for export to Excel (using CSV data)
    file_content = "\n".join(csv_lines)
    # Suggest a filename
    filename_suggestion = "elements_created_by_{0}.xlsx".format(target_username.replace(" ", "_").replace("\\", "_").replace("/", "_")) # Sanitize username for filename
    # Add project name prefix if possible
    try:
        if doc.Title and not String.IsNullOrWhiteSpace(doc.Title):
             proj_name = doc.Title.replace(' ', '_').replace('.rvt', '')
             # Further sanitize project name for typical file systems
             proj_name = "".join(c for c in proj_name if c.isalnum() or c in ('_', '-')).rstrip()
             filename_suggestion = proj_name + "_" + filename_suggestion
    except:
        pass # Ignore errors getting document title

    print("EXPORT::EXCEL::" + filename_suggestion)
    print(file_content)
elif is_workshared:
    # If workshared but no elements by the user were found
    print("# No model elements found created by user '{0}'.".format(target_username))
# No explicit 'else' needed here if the model wasn't workshared, as the error message was printed earlier.

# Reminder Comment (ignored by execution wrapper):
# - This script exports elements based on the 'Created By' worksharing property.
# - It CANNOT filter by creation date or the current Revit session due to API limitations.
# - It requires the model to be workshared.
# - It approximates "model elements" by excluding element types and view-specific elements.
# - Username comparison is case-insensitive.