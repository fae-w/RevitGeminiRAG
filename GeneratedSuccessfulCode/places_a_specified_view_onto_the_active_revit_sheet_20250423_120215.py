# Purpose: This script places a specified view onto the active Revit sheet.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewSheet,
    Viewport,
    ElementId,
    XYZ,
    BoundingBoxUV,
    ViewPlacementOnSheetStatus,
    BuiltInCategory,
    BuiltInParameter
)

# --- Configuration ---
target_view_name = "L4 - Floor Plan"

# --- Helper Function ---
def find_view_by_name(doc_param, view_name):
    """Finds a View element by its exact name, excluding view templates."""
    views = FilteredElementCollector(doc_param).OfClass(View).ToElements()
    for v in views:
        if v.IsTemplate:
            continue # Skip view templates
        try:
            # Access Name property directly
            if v.Name == view_name:
                return v
        except Exception as e:
            print("# Warning: Error accessing view name for ID {}: {}".format(v.Id, e))
            continue
    print("# Error: View named '{}' not found or it is a template.".format(view_name))
    return None

# --- Main Logic ---
active_view = uidoc.ActiveView

if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, ViewSheet):
    print("# Error: The active view '{}' is not a sheet.".format(active_view.Name))
else:
    active_sheet = active_view
    sheet_id = active_sheet.Id
    print("# Active sheet found: '{}' (ID: {})".format(active_sheet.Name, sheet_id.IntegerValue))

    # Find the target view
    target_view = find_view_by_name(doc, target_view_name)

    if target_view:
        view_id = target_view.Id
        print("# Target view found: '{}' (ID: {})".format(target_view.Name, view_id.IntegerValue))

        # Check if the view can be added to the sheet
        if Viewport.CanAddViewToSheet(doc, sheet_id, view_id):
            print("# Check Passed: View '{}' can be added to sheet '{}'.".format(target_view_name, active_sheet.Name))

            # Check if the view is already placed (informational)
            placement_status = target_view.GetPlacementOnSheetStatus()
            if placement_status != ViewPlacementOnSheetStatus.NotPlaced:
                 print("# Warning: View '{}' is already placed on a sheet (Status: {}). Depending on view type, placement might replace or error.".format(target_view_name, placement_status))
                 # Depending on the view type and Revit version, Create might still work or throw an error.
                 # Some views can be placed multiple times, others only once. CanAddViewToSheet is the primary check.

            try:
                # Calculate a placement point (center of the sheet)
                # Note: BoundingBoxUV might be null if the sheet has no title block or geometry yet
                # Using a default point if outline is not available
                center_point = XYZ(0, 0, 0) # Default origin placement
                try:
                    outline = active_sheet.Outline
                    if outline and outline.Min and outline.Max:
                        center_u = (outline.Min.U + outline.Max.U) / 2.0
                        center_v = (outline.Min.V + outline.Max.V) / 2.0
                        center_point = XYZ(center_u, center_v, 0)
                        print("# Calculated center placement point: ({}, {})".format(center_u, center_v))
                    else:
                        print("# Warning: Could not get sheet outline. Placing view at default origin (0,0).")
                except Exception as calc_ex:
                     print("# Warning: Error calculating sheet center ({}). Placing view at default origin (0,0).".format(calc_ex))


                # Create the viewport
                new_viewport = Viewport.Create(doc, sheet_id, view_id, center_point)
                if new_viewport:
                    print("# Successfully placed view '{}' onto sheet '{}'.".format(target_view_name, active_sheet.Name))
                else:
                    # This case might be rare if CanAddViewToSheet passed, but good practice
                    print("# Error: Viewport.Create returned None, placement failed for unknown reason.")

            except Exception as create_ex:
                print("# Error placing view '{}' onto sheet '{}'. Exception: {}".format(target_view_name, active_sheet.Name, create_ex))

        else:
             print("# Error: View '{}' cannot be added to sheet '{}'. It might already be placed exclusively, or is an incompatible view type.".format(target_view_name, active_sheet.Name))
             # Additional check: what is the current placement status?
             placement_status = target_view.GetPlacementOnSheetStatus()
             print("# Current placement status of view '{}': {}".format(target_view_name, placement_status))

    # else: message already printed by find_view_by_name