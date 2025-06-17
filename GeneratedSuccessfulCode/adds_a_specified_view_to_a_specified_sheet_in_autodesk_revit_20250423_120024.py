# Purpose: This script adds a specified view to a specified sheet in Autodesk Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    View,
    Viewport,
    ElementId,
    XYZ,
    BuiltInParameter
)
import System # Required for exception handling

# --- Configuration ---
target_sheet_number = "A-301"
target_view_name = "East Elevation"

# --- Helper Functions ---
def find_sheet_by_number(doc_param, sheet_number):
    """Finds a ViewSheet by its Sheet Number."""
    sheets = FilteredElementCollector(doc_param).OfClass(ViewSheet).ToElements()
    for sheet in sheets:
        if sheet.SheetNumber == sheet_number:
            return sheet
    return None

def find_view_by_name(doc_param, view_name):
    """Finds a View by its Name."""
    views = FilteredElementCollector(doc_param).OfClass(View).WhereElementIsNotElementType().ToElements()
    for view in views:
        # Ensure it's not a ViewSheet itself or a template
        if not isinstance(view, ViewSheet) and not view.IsTemplate:
            if view.Name == view_name:
                return view
    return None

# --- Main Logic ---
target_sheet = find_sheet_by_number(doc, target_sheet_number)
target_view = find_view_by_name(doc, target_view_name)

if not target_sheet:
    print("# Error: Sheet with number '{}' not found.".format(target_sheet_number))
elif not target_view:
    print("# Error: View with name '{}' not found.".format(target_view_name))
else:
    # Check if the view can be added to the sheet
    can_add = False
    try:
        can_add = Viewport.CanAddViewToSheet(doc, target_sheet.Id, target_view.Id)
    except Exception as check_ex:
        print("# Error checking if view can be added to sheet: {}".format(check_ex))

    if not can_add:
        # Provide more specific feedback if possible
        viewports_on_sheet = FilteredElementCollector(doc, target_sheet.Id).OfClass(Viewport).ToElements()
        view_already_on_any_sheet = False
        existing_viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()
        for vp in existing_viewports:
            if vp.ViewId == target_view.Id:
                 sheet_id_of_vp = vp.SheetId
                 if sheet_id_of_vp != ElementId.InvalidElementId:
                     existing_sheet = doc.GetElement(sheet_id_of_vp)
                     existing_sheet_num = existing_sheet.SheetNumber if existing_sheet else "Unknown Sheet"
                     print("# Error: View '{}' is already placed on sheet '{}' (Sheet ID: {}). Cannot add.".format(target_view_name, existing_sheet_num, sheet_id_of_vp))
                     view_already_on_any_sheet = True
                     break
        if not view_already_on_any_sheet:
            print("# Error: View '{}' (ID: {}) cannot be added to sheet '{}' (ID: {}). Reason unknown or view type incompatible (e.g., schedules might have limitations).".format(target_view_name, target_view.Id, target_sheet_number, target_sheet.Id))

    else:
        try:
            # Calculate center point of the sheet outline
            sheet_outline = target_sheet.Outline # BoundingBoxUV
            center_u = (sheet_outline.Min.U + sheet_outline.Max.U) / 2.0
            center_v = (sheet_outline.Min.V + sheet_outline.Max.V) / 2.0
            center_point = XYZ(center_u, center_v, 0) # Z is 0 for sheet coordinates

            # Create the Viewport
            viewport = Viewport.Create(doc, target_sheet.Id, target_view.Id, center_point)

            if viewport:
                print("# Successfully added view '{}' (ID: {}) to sheet '{}' (ID: {}) at center.".format(target_view_name, target_view.Id, target_sheet_number, target_sheet.Id))
            else:
                print("# Error: Failed to create viewport for view '{}' on sheet '{}'.".format(target_view_name, target_sheet_number))

        except System.ArgumentException as arg_ex:
             print("# Error creating viewport (ArgumentException): {}. View ID: {}, Sheet ID: {}".format(arg_ex.Message, target_view.Id, target_sheet.Id))
        except Exception as create_ex:
            print("# Error creating viewport: {}".format(create_ex))