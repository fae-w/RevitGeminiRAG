# Purpose: This script hides Revit viewports on sheets if their scale is larger than a specified threshold.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    View,
    ElementId,
    ViewType
)
from System.Collections.Generic import List
import System # For checking attributes like IsPerspective

# --- Configuration ---
# Scale threshold: Hide views with scale 1:N where N >= target_scale_denominator
target_scale_denominator = 200

# Dictionary to store viewports to hide per sheet
# Key: Sheet ElementId, Value: List of Viewport ElementIds
viewports_to_hide_on_sheets = {}
processed_viewports = 0

# --- Collect Sheets ---
collector_sheets = FilteredElementCollector(doc).OfClass(ViewSheet).WhereElementIsNotElementType()

# --- Iterate through Sheets and Viewports ---
for sheet in collector_sheets:
    if not sheet or not sheet.IsValidObject:
        continue

    sheet_id = sheet.Id
    sheet_number = sheet.SheetNumber # For potential debug messages
    viewports_on_this_sheet_to_hide = List[ElementId]()

    # Get all viewports placed on the current sheet
    try:
        viewport_ids = sheet.GetAllViewports()
    except Exception as e_vp_ids:
        # print("# Warning: Could not get viewports for Sheet {} (ID: {}). Error: {}".format(sheet_number, sheet_id, e_vp_ids)) # Escaped warning
        continue # Skip this sheet

    for vp_id in viewport_ids:
        processed_viewports += 1
        if vp_id == ElementId.InvalidElementId:
            continue

        try:
            viewport = doc.GetElement(vp_id)
            if not viewport or not isinstance(viewport, Viewport):
                continue

            view_id = viewport.ViewId
            if view_id == ElementId.InvalidElementId:
                continue

            view = doc.GetElement(view_id)
            if not view or not isinstance(view, View) or view.IsTemplate:
                continue

            # Check if the view type typically has a scale
            # Exclude view types that don't have a meaningful scale like schedules, legends, etc.
            # Perspective views also don't have a meaningful scale in this context.
            # Checking for CanBePrinted might also be a good filter, but type check is more explicit.
            if view.ViewType in [ViewType.Schedule, ViewType.ColumnSchedule, ViewType.PanelSchedule,
                                ViewType.Legend, ViewType.DrawingSheet, ViewType.ProjectBrowser,
                                ViewType.SystemBrowser, ViewType.Rendering, ViewType.CostReport,
                                ViewType.LoadsReport, ViewType.PressureLossReport] or \
               (hasattr(view, 'IsPerspective') and view.IsPerspective): # Check for perspective 3D views
                 continue

            # Get the scale denominator (N in 1:N)
            # View.Scale is 0 for some view types without scale, or 1 for custom scale.
            # Check if Scale property exists and is accessible
            if hasattr(view, 'Scale'):
                view_scale = view.Scale
                # We are interested in standard scales 1:N where N >= target_scale_denominator
                # Ensure view_scale is a positive integer representing the denominator
                if isinstance(view_scale, (int, long)) and view_scale > 0 and view_scale >= target_scale_denominator:
                     # Check if the viewport can be hidden (good practice)
                     # Element.CanBeHidden requires the view context (the sheet in this case)
                     try:
                         if viewport.CanBeHidden(sheet):
                             viewports_on_this_sheet_to_hide.Add(vp_id)
                         # else:
                             # print("# Info: Viewport ID {} (View: '{}') on Sheet {} cannot be hidden.".format(vp_id, view.Name, sheet_number)) # Escaped info
                     except Exception as check_hide_err:
                         # print("# Warning: Could not check if viewport ID {} can be hidden on Sheet {}. Error: {}. Adding anyway.".format(vp_id, sheet_number, check_hide_err)) # Escaped warning
                         viewports_on_this_sheet_to_hide.Add(vp_id) # Add anyway if check fails
            # else:
                 # print("# Info: View ID {} (Type: {}) does not have a 'Scale' property.".format(view_id, view.ViewType)) # Escaped info

        except Exception as e_vp:
            # Catch errors during viewport/view processing
            # print("# Warning: Could not process Viewport ID {} on Sheet {}. Error: {}".format(vp_id, sheet_number, e_vp)) # Escaped warning
            pass # Continue to the next viewport

    # Store the list of viewports to hide for this sheet if any were found
    if viewports_on_this_sheet_to_hide.Count > 0:
        viewports_to_hide_on_sheets[sheet_id] = viewports_on_this_sheet_to_hide

# --- Hide the Collected Viewports on their Respective Sheets ---
total_hidden_count = 0
sheets_affected_count = 0
for sheet_id, viewport_ids_to_hide in viewports_to_hide_on_sheets.items():
    if viewport_ids_to_hide.Count > 0:
        sheet_view = doc.GetElement(sheet_id)
        sheet_name = "<Unknown Sheet>"
        if sheet_view and isinstance(sheet_view, ViewSheet):
             try:
                sheet_name = sheet_view.SheetNumber + " - " + sheet_view.Name
             except:
                 pass # Keep default name if properties fail

             try:
                # Hide the viewport elements within the sheet view's context
                # This operation happens within the external transaction
                sheet_view.HideElements(viewport_ids_to_hide)
                count = viewport_ids_to_hide.Count
                total_hidden_count += count
                sheets_affected_count += 1
                # print("# Hid {} viewports on Sheet '{}'.".format(count, sheet_name)) # Escaped info
             except Exception as hide_err:
                # Check if the error message indicates elements cannot be hidden (e.g., already hidden)
                err_msg = str(hide_err)
                if "cannot be hidden" in err_msg or "already hidden" in err_msg:
                     # Potentially log a more specific warning or ignore if this is expected
                     # print("# Warning: Some viewports on Sheet '{}' could not be hidden (may be already hidden or restricted).".format(sheet_name)) # Escaped warning
                     pass # Treat as partial success or expected behaviour
                else:
                     print("# ERROR: Hiding viewports on Sheet '{}' failed: {}".format(sheet_name, hide_err)) # Escaped error
        # else:
             # print("# Warning: Could not retrieve Sheet element for ID {}.".format(sheet_id)) # Escaped warning

# --- Final Report ---
if total_hidden_count > 0:
    print("# Attempted to hide {} viewports with scale 1:{} or smaller across {} sheets.".format(total_hidden_count, target_scale_denominator, sheets_affected_count))
elif processed_viewports > 0:
     print("# No viewports found on sheets with scale 1:{} or smaller that could be hidden ({} viewports checked).".format(target_scale_denominator, processed_viewports))
else:
     print("# No viewports found on any sheets to process.")

# Clean up (optional)
# del collector_sheets
# del viewports_to_hide_on_sheets