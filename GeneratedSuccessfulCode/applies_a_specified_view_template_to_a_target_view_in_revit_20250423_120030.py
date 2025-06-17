# Purpose: This script applies a specified view template to a target view in Revit.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector, View, ElementId
)

# --- Configuration ---
target_view_name = 'R1'
template_view_name = 'Roof Plan Template'

# --- Helper Function to find a View by name ---
def find_view_by_name(doc_param, view_name):
    """Finds a View element by its exact name."""
    collector = FilteredElementCollector(doc_param).OfClass(View).WhereElementIsNotElementType()
    for v in collector:
        # Using Name property is generally reliable
        if v.Name == view_name:
            return v
    return None

# --- Helper Function to find a View Template by name ---
def find_view_template_by_name(doc_param, template_name):
    """Finds a View Template element by its exact name."""
    collector = FilteredElementCollector(doc_param).OfClass(View).WhereElementIsNotElementType()
    for v in collector:
        # Check if it's a template and the name matches
        if v.IsTemplate and v.Name == template_name:
            return v
    return None

# --- Main Logic ---

# 1. Find the target View
target_view = find_view_by_name(doc, target_view_name)

# 2. Find the View Template
template_view = find_view_template_by_name(doc, template_view_name)

# 3. Proceed only if both are found
if not target_view:
    print("# Error: View named '{}' not found.".format(target_view_name))
elif not template_view:
    print("# Error: View Template named '{}' not found.".format(template_view_name))
else:
    # 4. Validate if the template is suitable for the target view
    if not target_view.IsValidViewTemplate(template_view.Id):
        print("# Error: View Template '{}' (ID: {}) is not valid for View '{}' (ID: {}).".format(template_view_name, template_view.Id, target_view_name, target_view.Id))
    else:
        try:
            # 5. Apply the template
            target_view.ViewTemplateId = template_view.Id
            # print("# Successfully applied View Template '{}' to View '{}'.".format(template_view_name, target_view_name)) # Optional success message
        except Exception as e:
            print("# Error applying View Template '{}' to View '{}'. Error: {}".format(template_view_name, target_view_name, e))

# Example of how to handle the case where one or both were not found (already handled by the first two 'if' checks)
# if not target_view or not template_view:
#    print("# View creation aborted due to missing prerequisites.")