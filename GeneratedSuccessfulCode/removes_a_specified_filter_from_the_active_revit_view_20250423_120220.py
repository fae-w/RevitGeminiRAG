# Purpose: This script removes a specified filter from the active Revit view.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ElementId, View, ParameterFilterElement, FilteredElementCollector

# Define the name of the filter to remove
filter_name_to_remove = "Temporary Site Elements"

# Get the active view
active_view = doc.ActiveView

if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View):
     print("# Error: Active document is not a view or view is not active.")
else:
    # Find the filter element by name
    filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    found_filter_id = None
    found_filter_name = None # To confirm the match

    for filter_element in filter_collector:
        if filter_element.Name == filter_name_to_remove:
            found_filter_id = filter_element.Id
            found_filter_name = filter_element.Name
            break # Found the filter, exit loop

    if found_filter_id:
        try:
            # Get the list of filters currently applied to the view
            applied_filter_ids = active_view.GetFilters()

            # Check if the found filter is actually applied to this view
            if found_filter_id in applied_filter_ids:
                # Remove the filter from the view
                active_view.RemoveFilter(found_filter_id)
                print("# Filter '{}' (ID: {}) removed successfully from view '{}'.".format(found_filter_name, found_filter_id.IntegerValue, active_view.Name))
            else:
                print("# Filter '{}' (ID: {}) exists in the project but is not applied to the active view '{}'.".format(found_filter_name, found_filter_id.IntegerValue, active_view.Name))

        except Exception as e:
            # Handle potential errors during removal or if the view doesn't support filters
            print("# Error removing filter '{}' from view '{}': {}".format(found_filter_name, active_view.Name, e))
            # print("# This view type might not support Visibility/Graphics Overrides or Filters.")

    else:
        print("# Error: Filter named '{}' not found in the project.".format(filter_name_to_remove))