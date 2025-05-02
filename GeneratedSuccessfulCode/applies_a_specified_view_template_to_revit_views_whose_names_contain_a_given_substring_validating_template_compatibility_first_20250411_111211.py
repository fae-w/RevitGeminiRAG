# Purpose: This script applies a specified view template to Revit views whose names contain a given substring, validating template compatibility first.

# Purpose: This script applies a specific view template to Revit views based on their name and compatibility.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Often useful, though maybe not strictly needed here
from Autodesk.Revit.DB import FilteredElementCollector, View, ElementId
from System.Collections.Generic import List # Example of needing .NET list, good practice

# --- Configuration ---
target_template_name = "Structural Framing Plan"
view_name_substring = "Framing Plan"

# --- Find the View Template ElementId ---
template_id = ElementId.InvalidElementId
collector_templates = FilteredElementCollector(doc).OfClass(View)
# Use a more robust loop to find the template
template_view = None
for v in collector_templates:
    # Check if it's a view template and its name matches
    if v.IsTemplate and v.Name == target_template_name:
        template_view = v
        template_id = v.Id
        break # Exit loop once found

# --- Check if the template was found ---
if template_id == ElementId.InvalidElementId or template_view is None:
    print("# Error: View template named '{}' not found.".format(target_template_name)) # Escaped format
else:
    # --- Find and modify target views ---
    collector_views = FilteredElementCollector(doc).OfClass(View)
    applied_count = 0
    skipped_invalid_type = 0
    skipped_error = 0
    skipped_already_applied = 0

    for view in collector_views:
        # Skip view templates themselves
        if view.IsTemplate:
            continue

        # Skip views already using the target template
        if view.ViewTemplateId == template_id:
            skipped_already_applied += 1
            continue

        try:
            view_name = view.Name
            # Check if the view name contains the target substring
            if view_name_substring in view_name:
                # Check if the found template is valid for this view type
                if view.IsValidViewTemplate(template_id):
                    # Apply the template by setting the ViewTemplateId property
                    view.ViewTemplateId = template_id
                    applied_count += 1
                    # print(f"# Applied template '{target_template_name}' to view: {view_name}") # Optional debug output
                else:
                    skipped_invalid_type += 1
                    # print(f"# Skipped view '{view_name}': Template '{target_template_name}' is not valid for this view type.") # Optional debug output
        except Exception as e:
            skipped_error += 1
            # print(f"# Error processing view {view.Id} ('{view.Name}'): {e}") # Optional debug output

    # Optional: Print summary message (commented out by default)
    # total_skipped = skipped_invalid_type + skipped_error + skipped_already_applied
    # print(f"# Processed views containing '{view_name_substring}': Applied template '{target_template_name}' to {applied_count} views. Skipped {total_skipped} views (Invalid Type: {skipped_invalid_type}, Already Applied: {skipped_already_applied}, Error: {skipped_error}).") # Escaped f-string