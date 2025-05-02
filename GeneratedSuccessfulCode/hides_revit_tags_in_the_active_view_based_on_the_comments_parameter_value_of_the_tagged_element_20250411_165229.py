# Purpose: This script hides Revit tags in the active view based on the 'Comments' parameter value of the tagged element.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Required for List<T>
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    View,
    IndependentTag,
    BuiltInParameter,
    CategoryType, # Although not directly used for filtering, good context
    Element # To access GetParameters or Parameter property
)

# Assume doc and uidoc are pre-defined

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view found or the active view is not suitable.")
else:
    # List to store the ElementIds of the tags to hide
    tags_to_hide_ids = List[ElementId]()

    # Parameter to check on the tagged element
    comments_param_id = BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
    target_comment_value = "Ignore" # Case-sensitive comparison

    # Collect all IndependentTag elements in the active view
    # Using OfClass is generally more reliable for specific types like IndependentTag
    tag_collector = FilteredElementCollector(doc, active_view.Id).OfClass(IndependentTag)

    for tag in tag_collector:
        if not isinstance(tag, IndependentTag):
            continue

        try:
            # Get the element tagged by this tag
            # Use GetTaggedLocalElement() as it handles cases within the main model
            tagged_element = tag.GetTaggedLocalElement()

            if tagged_element:
                # Get the 'Comments' parameter from the tagged element
                comments_param = tagged_element.get_Parameter(comments_param_id)

                # Check if the parameter exists and its value matches
                if comments_param and comments_param.HasValue:
                    param_value = comments_param.AsString() # Get value as string
                    if param_value == target_comment_value:
                        # Check if the tag itself can be hidden in this view
                        if tag.CanBeHidden(active_view):
                            tags_to_hide_ids.Add(tag.Id)
                        # else:
                        #     print("# Info: Tag ID {} cannot be hidden in this view.".format(tag.Id)) # Debug/Info
            # Handle cases where the tag might be associated with a linked element differently if needed
            # For this script, we only consider locally tagged elements.

        except Exception as e:
            # print("# Warning: Error processing tag ID {}: {}".format(tag.Id, e)) # Debug/Info
            pass # Continue with the next tag

    # Hide the collected tags if any were found
    if tags_to_hide_ids.Count > 0:
        try:
            # Transaction is handled externally by the C# wrapper
            active_view.HideElements(tags_to_hide_ids)
            # print("# Hid {} tags where tagged element's Comments parameter is '{}'.".format(tags_to_hide_ids.Count, target_comment_value)) # Debug/Info
        except Exception as hide_ex:
            print("# Error applying hide operation: {}".format(hide_ex))
    # else:
        # print("# No tags found matching the criteria to hide.") # Debug/Info
        # pass