# Purpose: This script updates the 'Comments' parameter of a specified Revit element.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import Element, ElementId, BuiltInParameter, Parameter

# --- Configuration ---
target_element_id_int = 12345
new_comment_value = "Approved by PM"
# --- End Configuration ---

try:
    # Construct the ElementId
    target_element_id = ElementId(target_element_id_int)

    # Get the element from the document
    element = doc.GetElement(target_element_id)

    if element:
        # Get the 'Comments' parameter (ALL_MODEL_INSTANCE_COMMENTS is common)
        # Use LookupParameter for robustness if BuiltInParameter isn't found or applicable
        comments_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

        # Fallback to lookup by name if BuiltInParameter fails or doesn't exist for the element type
        if not comments_param:
            comments_param = element.LookupParameter("Comments")

        # Check if the parameter exists and is not read-only
        if comments_param and not comments_param.IsReadOnly:
            # Set the new value for the 'Comments' parameter
            comments_param.Set(new_comment_value)
            # print(f"# Successfully updated Comments for element ID {target_element_id_int}") # Optional success message
        else:
            if not comments_param:
                print("# Error: 'Comments' parameter not found for element ID {}.".format(target_element_id_int))
            elif comments_param.IsReadOnly:
                print("# Error: 'Comments' parameter is read-only for element ID {}.".format(target_element_id_int))
    else:
        print("# Error: Element with ID {} not found in the document.".format(target_element_id_int))

except Exception as e:
    print("# Error: An unexpected error occurred processing element ID {}: {}".format(target_element_id_int, e))