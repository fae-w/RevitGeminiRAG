# Purpose: This script retrieves and prints the names of filters applied to the active Revit view.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ElementId, View, ParameterFilterElement, FilteredElementCollector # ParameterFilterElement is needed to get filter details

# Get the active view
active_view = uidoc.ActiveView

if not active_view:
    print("# Error: No active view.")
elif not isinstance(active_view, View):
    print("# Error: Active document is not a view.")
else:
    try:
        # Get the ElementIds of the filters applied to the view
        filter_ids = active_view.GetFilters()

        if not filter_ids or filter_ids.Count == 0:
            print("# No view filters are applied to the active view.")
        else:
            # print("# Filters applied to view: {}".format(active_view.Name)) # Optional: Print view name
            found_filters = False
            for filter_id in filter_ids:
                if filter_id != ElementId.InvalidElementId:
                    filter_element = doc.GetElement(filter_id)
                    # Check if the retrieved element is actually a ParameterFilterElement
                    if filter_element and isinstance(filter_element, ParameterFilterElement):
                        try:
                            filter_name = filter_element.Name
                            print(filter_name)
                            found_filters = True
                        except Exception as e_name:
                            print("# Error getting name for Filter ID {}: {}".format(filter_id.IntegerValue, e_name))
                    # else: # Optional: Handle cases where the ID doesn't resolve to a ParameterFilterElement
                    #     print("# Warning: Element ID {} is not a ParameterFilterElement.".format(filter_id.IntegerValue))


            if not found_filters:
                 print("# No valid ParameterFilterElements found for the applied filter IDs.")

    except Exception as e:
        # Catch potential exceptions if the view type doesn't support filters
        print("# Error accessing filters for the active view: {}".format(e))
        # print("# This view type might not support Visibility/Graphics Overrides or Filters.")