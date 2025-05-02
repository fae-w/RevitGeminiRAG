# Purpose: This script extracts view information from Revit sheets and outputs it to a CSV format.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    View,
    ElementId
)

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append("Sheet Number,Sheet Name,View Name,View ID")

# Collect all ViewSheets
collector_sheets = FilteredElementCollector(doc).OfClass(ViewSheet)

for sheet in collector_sheets:
    if not sheet or not sheet.IsValidObject:
        continue

    try:
        sheet_number = sheet.SheetNumber
        sheet_name = sheet.Name
        if not sheet_number:
            sheet_number = "<No Number>"
        if not sheet_name:
            sheet_name = "<No Name>"

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
            # Ensure it's a valid View, not a template itself, and has no view template assigned
            if (view and view.IsValidObject and
                    isinstance(view, View) and
                    not view.IsTemplate and
                    view.ViewTemplateId == ElementId.InvalidElementId):

                try:
                    view_name = view.Name
                    view_id_int = view.Id.IntegerValue

                    # Basic CSV quoting for fields that might contain commas or quotes
                    safe_sheet_number = '"{0}"'.format(sheet_number.replace('"', '""'))
                    safe_sheet_name = '"{0}"'.format(sheet_name.replace('"', '""'))
                    safe_view_name = '"{0}"'.format(view_name.replace('"', '""'))

                    csv_lines.append("{0},{1},{2},{3}".format(safe_sheet_number, safe_sheet_name, safe_view_name, view_id_int))
                except Exception as e_view:
                    # Silently skip if view details cannot be retrieved
                    # print("Error getting view details: {}".format(e_view)) # Debug
                    pass

    except Exception as e_sheet:
        # Silently skip if sheet processing fails
        # print("Error processing sheet {}: {}".format(sheet.Id, e_sheet)) # Debug
        pass

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::views_without_templates_on_sheets.csv")
    print(file_content)
else:
    # Use print for user feedback if no data found, although EXPORT marker takes precedence if data exists
    print("# No views found on sheets without a View Template assigned.")