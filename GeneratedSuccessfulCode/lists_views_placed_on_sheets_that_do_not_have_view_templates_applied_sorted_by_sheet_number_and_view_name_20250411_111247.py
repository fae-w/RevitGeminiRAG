# Purpose: This script lists views placed on sheets that do not have view templates applied, sorted by sheet number and view name.

# Purpose: This script lists all views placed on sheets without applied view templates, sorted by sheet number and view name.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    View,
    ElementId
)
from System.Collections.Generic import List
import System # For sorting

# List to store tuples of (Sheet Number, View Name) for sorting
results = List[System.Tuple[str, str]]()

# Collect all ViewSheets
collector_sheets = FilteredElementCollector(doc).OfClass(ViewSheet)

for sheet in collector_sheets:
    if not sheet or not sheet.IsValidObject:
        continue

    try:
        sheet_number = sheet.SheetNumber
        if not sheet_number: # Skip sheets without a number if necessary
             sheet_number = "<No Number>" # Or handle as needed

        # Get all viewports on the sheet
        viewport_ids = sheet.GetAllViewports()

        for vp_id in viewport_ids:
            if vp_id == ElementId.InvalidElementId:
                continue

            viewport = doc.GetElement(vp_id)
            if not viewport or not viewport.IsValidObject or not isinstance(viewport, Viewport):
                continue

            view_id = viewport.ViewId
            if view_id == ElementId.InvalidElementId:
                continue

            view = doc.GetElement(view_id)
            if not view or not view.IsValidObject or not isinstance(view, View) or view.IsTemplate:
                continue

            # Check if a View Template is applied
            if view.ViewTemplateId == ElementId.InvalidElementId:
                try:
                    view_name = view.Name
                    # Add tuple for sorting
                    results.Add(System.Tuple[str, str](sheet_number, view_name))
                except Exception as e_view:
                    # print("# Warning: Could not get name for View ID {} on Sheet {}. Error: {}".format(view_id, sheet_number, e_view)) # Escaped warning
                    pass # Skip this view if name cannot be retrieved

    except Exception as e_sheet:
        # print("# Warning: Could not process Sheet ID {}. Error: {}".format(sheet.Id, e_sheet)) # Escaped warning
        pass # Continue with the next sheet


# Sort the results based on Sheet Number, then View Name
# Convert List[Tuple] to Python list for sorting
py_results = list(results)
py_results.sort(key=lambda x: (x.Item1, x.Item2)) # Sort by SheetNumber (Item1), then ViewName (Item2)

# Print the sorted results
if py_results:
    # print("# Views on Sheets without a View Template applied:") # Escaped info print
    for result_tuple in py_results:
        print("{0} / {1}".format(result_tuple.Item1, result_tuple.Item2)) # Escaped format
else:
    print("# No views found on sheets without a View Template applied.")