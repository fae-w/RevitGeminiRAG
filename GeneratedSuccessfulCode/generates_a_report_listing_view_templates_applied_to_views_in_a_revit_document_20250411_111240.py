# Purpose: This script generates a report listing view templates applied to views in a Revit document.

# Purpose: This script generates a report of view templates applied to views in a Revit document.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, View, ElementId

# List to hold text lines for the report
text_lines = []
text_lines.append("View Templates Report")
text_lines.append("=====================")
text_lines.append("View Name | Applied Template Name")
text_lines.append("---------------------------------")

# Collect all View elements in the document
collector = FilteredElementCollector(doc).OfClass(View)

# Iterate through views
for view in collector:
    if isinstance(view, View) and not view.IsTemplate: # Exclude view templates themselves from the list
        try:
            view_name = view.Name
            template_name = "None" # Default if no template is applied

            # Get the ID of the applied view template
            template_id = view.ViewTemplateId

            # Check if a valid template ID exists
            if template_id is not None and template_id != ElementId.InvalidElementId:
                # Get the template element
                template_element = doc.GetElement(template_id)
                if template_element is not None and isinstance(template_element, View):
                    template_name = template_element.Name
                else:
                    template_name = "Invalid/Deleted Template ID" # Handle cases where ID exists but element doesn't

            # Format the line for the report
            text_lines.append(u"{} | {}".format(view_name, template_name)) # Use unicode format for safety

        except Exception as e:
            # Log errors for specific views if needed, but continue processing others
            # print(f"# Error processing view {view.Id}: {e}") # Escaped
            try:
                 text_lines.append(u"{} | Error processing view".format(view.Name)) # Escaped
            except:
                 text_lines.append(u"Error processing view ID: {}".format(view.Id)) # Escaped
            pass # Skip views that cause errors

# Check if we gathered any view data
if len(text_lines) > 4: # More than just the header lines
    # Format the final output string for export
    file_content = "\n".join(text_lines)
    print("EXPORT::TXT::view_templates_report.txt") # <-- The marker line
    print(file_content)                             # <-- The data content string
else:
    print("# No views found or processed in the document.")