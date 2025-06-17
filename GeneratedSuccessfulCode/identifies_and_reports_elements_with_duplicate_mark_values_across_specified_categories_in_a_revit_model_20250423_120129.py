# Purpose: This script identifies and reports elements with duplicate Mark values across specified categories in a Revit model.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Element, ElementId,
    BuiltInParameter, Category
)
# Using Python standard dictionary and list is generally fine in IronPython

# Define categories to check
categories_to_check = [
    BuiltInCategory.OST_Doors,
    BuiltInCategory.OST_Windows,
    BuiltInCategory.OST_MechanicalEquipment
]

# Dictionary to store elements by Mark value: { mark_value: [ (ElementId, CategoryName), ... ] }
marks_dict = {}

# Collect elements and populate the dictionary
for category_bic in categories_to_check:
    # Ensure we are collecting instances, not types
    collector = FilteredElementCollector(doc).OfCategory(category_bic).WhereElementIsNotElementType()
    for element in collector:
        try:
            mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            # Check if the parameter exists, has a value, and the value is not None or empty string
            if mark_param and mark_param.HasValue:
                mark_value = mark_param.AsString()
                # Ensure mark_value is a valid, non-empty string before proceeding
                if mark_value and mark_value.strip(): # Check for null, empty or whitespace only string
                    element_id = element.Id
                    # Get category name safely
                    category_name = "Unknown Category"
                    element_category = element.Category
                    if element_category and hasattr(element_category, 'Name'):
                         category_name = element_category.Name

                    # Store the element info, keyed by its mark value
                    if mark_value not in marks_dict:
                        marks_dict[mark_value] = []
                    marks_dict[mark_value].append((element_id, category_name))
        except Exception as e:
            # Optional: Log errors for specific elements during debugging
            # print("# Error processing element {}: {}".format(element.Id, e))
            pass # Silently ignore elements causing errors during parameter access or processing

# Prepare CSV lines for export
csv_lines = []
# Add header row
csv_lines.append('"Mark Value","Category","Element IDs"')

# Flag to track if any duplicates were found and processed
processed_duplicates = False

# Find duplicate marks and format output rows
for mark, elements_info in marks_dict.items():
    # A mark is considered duplicate if it's associated with more than one element
    if len(elements_info) > 1:
        processed_duplicates = True
        # Group elements by category name for this specific duplicate Mark value
        # category_groups maps: { category_name: [ElementId, ...], ... }
        category_groups = {}
        for elem_id, cat_name in elements_info:
            if cat_name not in category_groups:
                category_groups[cat_name] = []
            category_groups[cat_name].append(elem_id)

        # Create a distinct row in the CSV for each category that uses this duplicate mark
        for cat_name, id_list in category_groups.items():
            # Join the Element IDs for this category into a comma-separated string
            ids_str = ", ".join([eid.ToString() for eid in id_list])

            # Escape double quotes within strings for CSV safety and enclose fields in quotes
            safe_mark = '"' + mark.replace('"', '""') + '"'
            safe_cat = '"' + cat_name.replace('"', '""') + '"'
            safe_ids = '"' + ids_str.replace('"', '""') + '"'

            # Append the formatted row to our list of CSV lines
            csv_lines.append(','.join([safe_mark, safe_cat, safe_ids]))

# Check if any duplicate marks were actually found and added to the list
# (csv_lines will have more than 1 item if duplicates were found: header + data)
if len(csv_lines) > 1:
    # Format the final output string for export
    file_content = "\n".join(csv_lines)
    # Print the export header and the data
    print("EXPORT::EXCEL::duplicate_marks_report.xlsx")
    print(file_content)
else:
    # Print a message if no duplicates were found across the specified categories
    print("# No duplicate Mark values found in Doors, Windows, or Mechanical Equipment categories.")