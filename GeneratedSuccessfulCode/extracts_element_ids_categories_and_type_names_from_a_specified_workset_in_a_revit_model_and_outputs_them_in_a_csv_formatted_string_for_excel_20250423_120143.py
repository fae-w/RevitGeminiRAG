# Purpose: This script extracts element IDs, categories, and type names from a specified workset in a Revit model and outputs them in a CSV-formatted string for Excel.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Workset,
    WorksetId,
    ElementWorksetFilter,
    Category,
    ElementType,
    ElementId,
    WorksetKind,
    FilteredWorksetCollector # Required for finding the workset
)
import System # For String.IsNullOrEmpty, Convert

# Check if the document is workshared
if not doc.IsWorkshared:
    print("# Error: Document is not workshared. Cannot query worksets.")
else:
    # Define the target workset name
    target_workset_name = 'SHELL_AND_CORE'
    target_workset_id = None
    target_workset = None

    # Find the target workset ID
    try:
        # Use FilteredWorksetCollector to find the workset by name
        workset_collector = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
        # Find first workset matching the name (case-sensitive)
        target_workset = next((ws for ws in workset_collector if ws.Name == target_workset_name), None)

        if target_workset:
            target_workset_id = target_workset.Id
        else:
            print("# Error: Workset '{{}}' not found.".format(target_workset_name))

    except Exception as e:
        print("# Error finding workset: {{}}".format(e))
        target_workset_id = None # Ensure it's None if error occurs

    # Proceed only if workset was found
    if target_workset_id is not None:
        # Prepare for export data collection
        csv_lines = []
        csv_lines.append('"Element ID","Category","Type Name"') # Header row

        # Helper function for CSV quoting and escaping
        def escape_csv(value):
            """Escapes a value for safe inclusion in a CSV cell."""
            if value is None:
                return '""'
            # Ensure value is a string before replacing quotes
            str_value = System.Convert.ToString(value)
            # Replace double quotes with two double quotes and enclose in double quotes
            return '"' + str_value.replace('"', '""') + '"'

        try:
            # Create element filter for the specific workset
            # False indicates elements directly assigned to this workset
            workset_filter = ElementWorksetFilter(target_workset_id, False)

            # Collect elements using the workset filter, excluding element types
            element_collector = FilteredElementCollector(doc).WherePasses(workset_filter).WhereElementIsNotElementType()

            # Iterate through collected elements and extract data
            for element in element_collector:
                elem_id_str = "N/A"
                category_name = "N/A"
                type_name = "N/A"

                try:
                    # Get Element ID
                    elem_id_str = element.Id.IntegerValue

                    # Get Category Name
                    cat = element.Category
                    if cat is not None and not System.String.IsNullOrEmpty(cat.Name):
                        category_name = cat.Name
                    elif cat is not None:
                        category_name = "(Unnamed Category)" # Handle empty name but existing category

                    # Get Type Name
                    type_id = element.GetTypeId()
                    if type_id is not None and type_id != ElementId.InvalidElementId:
                        elem_type = doc.GetElement(type_id)
                        if elem_type is not None and isinstance(elem_type, ElementType):
                            t_name = elem_type.Name
                            if not System.String.IsNullOrEmpty(t_name):
                                type_name = t_name
                            else:
                                # Fallback: Check family name if type name is empty
                                if hasattr(elem_type, 'FamilyName') and not System.String.IsNullOrEmpty(elem_type.FamilyName):
                                    type_name = elem_type.FamilyName + " (Family Name)"
                                else:
                                    type_name = "(Unnamed Type)"
                        elif elem_type is not None:
                            # If GetTypeId returns an element that isn't an ElementType
                             if hasattr(elem_type, 'Name') and not System.String.IsNullOrEmpty(elem_type.Name):
                                 type_name = elem_type.Name + " (Non-ElementType)"
                             else:
                                 type_name = "(Invalid Type Element)"
                        else:
                            type_name = "(Type Not Found)"
                    else:
                         # Handle elements without a type ID (like system families instances or specific categories)
                         # Sometimes the category name itself is the best descriptor here
                         if category_name != "N/A":
                             type_name = category_name + " Instance"
                         else:
                             type_name = "(System Family Instance / No Type ID)"


                    # Escape values for CSV and add row to list
                    safe_id = escape_csv(elem_id_str)
                    safe_cat = escape_csv(category_name)
                    safe_type = escape_csv(type_name)
                    csv_lines.append(','.join([safe_id, safe_cat, safe_type]))

                except Exception as el_ex:
                    # Log error for this specific element and add an error row
                    try:
                         err_id_str = element.Id.IntegerValue
                    except:
                         err_id_str = "Unknown ID"
                    csv_lines.append(','.join([escape_csv(err_id_str), escape_csv("ERROR"), escape_csv("Processing Error: " + str(el_ex))]))

            # Check if any data rows were added (more than just the header)
            if len(csv_lines) > 1:
                # Format the final output string
                file_content = "\n".join(csv_lines)

                # Suggest a filename, incorporating project name if possible
                filename_suggestion = "shell_and_core_elements.xlsx"
                try:
                    if doc.Title and not System.String.IsNullOrEmpty(doc.Title):
                        # Sanitize project title for filename
                        proj_name = "".join(c for c in doc.Title if c.isalnum() or c in (' ', '_', '-')).rstrip()
                        proj_name = proj_name.replace(' ', '_').replace('.rvt', '')
                        if proj_name: # Ensure not empty after sanitizing
                             filename_suggestion = proj_name + "_" + filename_suggestion
                except Exception:
                    pass # Ignore errors getting document title

                # Print the export marker and data
                print("EXPORT::EXCEL::" + filename_suggestion)
                print(file_content)
            else:
                # No elements found on the specified workset
                print("# No elements found assigned to workset '{{}}'.".format(target_workset_name))

        except Exception as coll_ex:
            print("# Error during element collection or processing: {{}}".format(coll_ex))

# If target_workset_id remained None (either not found or error finding), the appropriate message was already printed.