# Purpose: This script generates a report listing views using a specified view template in a Revit project.

# Purpose: This script generates a report of all views using a specified view template in a Revit project.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, View, ElementId

# Define the target template name
target_template_name = "Default Floor Plan"

# Find the ElementId of the target view template
target_template_id = ElementId.InvalidElementId
collector_templates = FilteredElementCollector(doc).OfClass(View)
template_found = False
for v_template in collector_templates:
    if v_template.IsTemplate and v_template.Name == target_template_name:
        target_template_id = v_template.Id
        template_found = True
        break

# Check if the template was found
if not template_found:
    print("# Error: View template named '{}' not found.".format(target_template_name))
else:
    # List to hold the names of views using the template
    view_names = []

    # Collect all View elements in the document
    collector_views = FilteredElementCollector(doc).OfClass(View)

    # Iterate through views to find those using the specified template
    for view in collector_views:
        # Skip view templates themselves
        if view.IsTemplate:
            continue

        # Check if the view uses the target template
        if view.ViewTemplateId == target_template_id:
            try:
                view_names.append(view.Name)
            except Exception as e:
                # Handle potential errors getting view name, though unlikely for standard views
                print("# Error getting name for View ID: {} - {}".format(view.Id, e))
                view_names.append("Error: View ID {}".format(view.Id))

    # Prepare the report for export
    if view_names:
        report_lines = []
        report_lines.append("Views using template: '{}'".format(target_template_name))
        report_lines.append("=======================================")
        report_lines.extend(sorted(view_names)) # Sort the view names alphabetically

        # Format the final output string for export
        file_content = "\n".join(report_lines)
        safe_filename = "views_using_{}_template.txt".format(target_template_name.lower().replace(' ', '_').replace('-', '_'))
        print("EXPORT::TXT::{}".format(safe_filename)) # <-- The marker line
        print(file_content)                           # <-- The data content string
    else:
        print("# No views found using the template '{}'.".format(target_template_name))