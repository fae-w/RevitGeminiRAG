# Purpose: This script deletes unused view filters from the Revit model.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Core') # Required for HashSet

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    View,
    ElementId
)
from System.Collections.Generic import HashSet, List # Use List for deletion API

# 1. Collect all ParameterFilterElement IDs into a HashSet for efficient lookup
all_filter_ids = HashSet[ElementId]()
collector_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
for filter_elem in collector_filters:
    all_filter_ids.Add(filter_elem.Id)

# 2. Collect all filter IDs currently applied to any View or View Template
used_filter_ids = HashSet[ElementId]()
collector_views = FilteredElementCollector(doc).OfClass(View)

for view in collector_views:
    try:
        # View.GetFilters() retrieves filters applied directly or via a view template.
        # This covers both standard views and view templates themselves.
        view_applied_filters = view.GetFilters()
        if view_applied_filters and view_applied_filters.Count > 0:
            for filter_id in view_applied_filters:
                # Ensure the ID is valid and actually exists in our set of all filters
                if filter_id != ElementId.InvalidElementId and all_filter_ids.Contains(filter_id):
                    used_filter_ids.Add(filter_id)
    except Exception as e:
        # Ignore views where filters cannot be retrieved (e.g., certain view types might throw exceptions)
        # print("# Info: Could not get filters for view '{0}' (ID: {1}, Type: {2}). Error: {3}".format(view.Name, view.Id, view.ViewType, e)) # Optional debug info
        pass # Continue to the next view

# 3. Determine which filters are unused by finding the difference
# Create a list to hold the IDs of filters to be deleted
unused_filter_ids_list = List[ElementId]()
for filter_id in all_filter_ids:
    if not used_filter_ids.Contains(filter_id):
        unused_filter_ids_list.Add(filter_id)

# 4. Delete the unused filters
# The deletion is performed within the external C# transaction context
deleted_count = 0
if unused_filter_ids_list.Count > 0:
    try:
        # Attempt to delete the collected unused filter IDs
        deleted_ids_result = doc.Delete(unused_filter_ids_list)
        deleted_count = deleted_ids_result.Count
        # print("# Successfully deleted {0} unused view filters.".format(deleted_count)) # Optional confirmation message
    except Exception as e:
        # Report any errors during deletion
        print("# Error occurred during deletion of unused filters: {0}".format(e))
# else:
    # print("# No unused view filters found to delete.") # Optional confirmation message