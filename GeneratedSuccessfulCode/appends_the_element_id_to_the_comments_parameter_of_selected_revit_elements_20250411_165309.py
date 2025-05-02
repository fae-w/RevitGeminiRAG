# Purpose: This script appends the element ID to the 'Comments' parameter of selected Revit elements.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import Element, ElementId, BuiltInParameter, Parameter

# Get the current selection
selection = uidoc.Selection
selected_ids = selection.GetElementIds()

# Check if any elements are selected
if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected.")
else:
    # Iterate through the selected element IDs
    for element_id in selected_ids:
        try:
            # Get the element from the document
            element = doc.GetElement(element_id)

            if element:
                # Get the 'Comments' parameter (ALL_MODEL_INSTANCE_COMMENTS is common)
                # Use LookupParameter for robustness if BuiltInParameter isn't found or applicable
                comments_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

                # Fallback to lookup by name if BuiltInParameter fails or doesn't exist for the element type
                if not comments_param:
                    comments_param = element.LookupParameter("Comments")

                # Check if the parameter exists and is not read-only
                if comments_param and not comments_param.IsReadOnly:
                    # Get the current comment value
                    current_comment = comments_param.AsString()
                    if current_comment is None:
                        current_comment = ""

                    # Get the element ID as a string
                    element_id_str = str(element.Id.IntegerValue)

                    # Construct the new comment string
                    # Add a separator; adjust if needed (e.g., use "; " or just append)
                    separator = " - ID: "
                    # Avoid appending if ID is already present (simple check)
                    if not element_id_str in current_comment:
                         new_comment = current_comment + separator + element_id_str
                         # Set the new value for the 'Comments' parameter
                         comments_param.Set(new_comment.strip()) # Use strip() to remove leading/trailing whitespace if current_comment was empty
                    # else:
                        # print(f"# ID {element_id_str} seems already present in comments for Element {element_id}.") # Optional debug/info message

                # else: # Optional: Add debug/logging if needed
                    # if not comments_param:
                        # print(f"# 'Comments' parameter not found for element ID: {element_id}")
                    # elif comments_param.IsReadOnly:
                        # print(f"# 'Comments' parameter is read-only for element ID: {element_id}")
            # else:
                # print(f"# Element with ID {element_id} not found.") # Optional debug message

        except Exception as e:
            # print(f"# Error processing element ID {element_id}: {e}") # Optional detailed error message
            pass # Silently continue if an error occurs for a specific element

    # print(f"# Processed {selected_ids.Count} selected elements.") # Optional completion message