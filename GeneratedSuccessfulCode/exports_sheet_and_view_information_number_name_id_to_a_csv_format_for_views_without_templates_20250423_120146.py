# Purpose: This script exports sheet and view information (number, name, ID) to a CSV format for views without templates.

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
            # Ensure it's a valid View, not a template, and has no template assigned
            if (view and view.IsValidObject and
                    isinstance(view, View) and
                    not view.IsTemplate and
                    view.ViewTemplateId == ElementId.InvalidElementId):

                try:
                    view_name = view.Name
                    view_id_int = view.Id.IntegerValue

                    # Basic CSV quoting for fields that might contain commas
                    safe_sheet_number = '"{}"'.format(sheet_number.replace('"', '""')) if ',' in sheet_number else sheet_number
                    safe_sheet_name = '"{}"'.format(sheet_name.replace('"', '""')) if ',' in sheet_name else sheet_name
                    safe_view_name = '"{}"'.format(view_name.replace('"', '""')) if ',' in view_name else view_name

                    csv_lines.append("{},{},{},{}".format(safe_sheet_number, safe_sheet_name, safe_view_name, view_id_int))
                except Exception as e_view:
                    # Silently skip if view details cannot be retrieved
                    pass

    except Exception as e_sheet:
        # Silently skip if sheet processing fails
        pass

# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::views_without_templates_on_sheets.csv")
    print(file_content)
else:
    print("# No views found on sheets without a View Template applied.")