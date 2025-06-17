# Purpose: This script lists all worksets in a workshared Revit project.

# Purpose: This script lists all available worksets in a Revit project if worksharing is enabled.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredWorksetCollector, Workset

# Check if the document is workshared
if doc.IsWorkshared:
    # List to hold text lines for the output
    output_lines = []
    output_lines.append("Available Worksets:")
    output_lines.append("===================")

    # Collect all worksets using FilteredWorksetCollector
    collector = FilteredWorksetCollector(doc)
    # No specific filter needed, as we want all kinds of worksets

    workset_found = False
    # Iterate through the collected worksets
    for workset in collector:
        if isinstance(workset, Workset):
            try:
                workset_name = workset.Name
                output_lines.append(workset_name)
                workset_found = True
            except Exception as e:
                # print(f"# Debug: Error processing workset {workset.Id}: {e}") # Escaped
                pass # Skip worksets that cause errors

    # Check if we gathered any data
    if workset_found:
        # Format the final output for export
        file_content = "\n".join(output_lines)
        print("EXPORT::TXT::workset_list.txt") # <-- The marker line
        print(file_content)                    # <-- The data content string
    else:
        # This case might occur if worksharing is enabled but no worksets exist (unlikely)
        print("# No worksets found in the project, although worksharing is enabled.")

else:
    print("# Worksharing is not enabled in this project. No worksets to list.")