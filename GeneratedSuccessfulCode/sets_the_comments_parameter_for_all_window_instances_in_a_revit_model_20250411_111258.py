# Purpose: This script sets the 'Comments' parameter for all window instances in a Revit model.

# Purpose: This script sets the 'Comments' parameter of all window instances in the Revit model to a specified value.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter

# Define the value to set for the 'Comments' parameter
new_comment_value = "Checked by AI"

# Collect all window instances in the document
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()

# Iterate through the collected windows
for window in collector:
    try:
        # Get the 'Comments' parameter (ALL_MODEL_INSTANCE_COMMENTS is the typical built-in param)
        comments_param = window.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

        # Check if the parameter exists and is not read-only
        if comments_param and not comments_param.IsReadOnly:
            # Set the parameter value
            comments_param.Set(new_comment_value)
        # else: # Optional: Add debug/logging if needed
            # if not comments_param:
            #     print(f"# 'Comments' parameter not found for window ID: {window.Id}")
            # elif comments_param.IsReadOnly:
            #     print(f"# 'Comments' parameter is read-only for window ID: {window.Id}")
    except Exception as e:
        # print(f"# Error processing window ID {window.Id}: {e}")
        pass # Silently continue if an error occurs for a specific window

# No explicit output required, changes are made directly to the model elements