# Purpose: This script extracts Revision Cloud IDs and their corresponding Revision sequence numbers from a Revit project.

# Purpose: This script extracts Revision Cloud IDs and their corresponding Revision sequence numbers in a Revit project and formats the data for export.

﻿# -*- coding: utf-8 -*-
# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevisionCloud,
    Revision,
    ElementId
)

# List to hold output lines for the export file
output_lines = []
output_lines.append("Revision Cloud Element ID | Revision Sequence Number")
output_lines.append("--------------------------------------------------")

# Collect all Revision Cloud elements in the document
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RevisionClouds).WhereElementIsNotElementType()

revision_clouds_found = False
# Iterate through the collected revision clouds
for cloud in collector:
    if isinstance(cloud, RevisionCloud):
        try:
            # Get the ID of the Revision associated with this cloud
            revision_id = cloud.RevisionId

            # Check if the Revision ID is valid
            if revision_id != ElementId.InvalidElementId:
                # Get the Revision element from its ID
                revision = doc.GetElement(revision_id)

                # Verify that the retrieved element is indeed a Revision
                if isinstance(revision, Revision):
                    # Get the sequence number of the Revision
                    sequence_number = revision.SequenceNumber
                    cloud_id_str = cloud.Id.ToString()

                    # Add the information to the output list
                    output_lines.append("{0} | {1}".format(cloud_id_str, sequence_number))
                    revision_clouds_found = True
                # else:
                    # # Optional: Handle cases where the ID points to something other than a Revision (unlikely)
                    # print("# Warning: Element {0} associated with RevisionCloud {1} is not a Revision.".format(revision_id, cloud.Id)) # Escaped
                    pass
            # else:
                # # Optional: Handle cases where a cloud might not have a revision assigned (shouldn't happen for valid clouds)
                # print("# Warning: RevisionCloud {0} has an invalid RevisionId.".format(cloud.Id)) # Escaped
                pass
        except Exception as e:
            # Log or print error for specific cloud processing failure
            # print("# Error processing RevisionCloud {0}: {1}".format(cloud.Id, e)) # Escaped
            pass # Continue with the next cloud

# Check if any revision clouds were found and processed
if revision_clouds_found:
    # Format the final output string for export
    file_content = "\n".join(output_lines)
    # Print the export header and data
    print("EXPORT::TXT::revision_cloud_sequences.txt")
    print(file_content)
else:
    # Print a message if no revision clouds were found
    print("# No Revision Clouds found in the project.")