# Purpose: This script adjusts the view range of a Revit Reflected Ceiling Plan (RCP) based on specified level names and offsets.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    BuiltInCategory,
    ViewPlan,
    PlanViewRange,
    PlanViewPlane,
    ElementId,
    ViewType
)
import System

# --- Configuration ---
target_view_name_part = "L4" # User specified 'L4' RCP view
target_view_type = ViewType.CeilingPlan
target_level_name_cut = "L5"
target_level_name_bottom = "L4"
target_level_name_view_depth = "L5"
cut_plane_offset_mm = -150.0 # 150mm below L5

# --- Helper Function ---
def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    collector = FilteredElementCollector(doc_param).OfClass(Level)
    for level in collector:
        if level.Name == level_name:
            return level
    print("# Error: Level named '{}' not found.".format(level_name))
    return None

def mm_to_feet(mm):
    """Converts millimeters to decimal feet."""
    return mm / 304.8

# --- Main Logic ---
active_view = doc.ActiveView

if not active_view:
    print("# Error: No active view found.")
else:
    # Verify active view is the intended one
    is_correct_name = target_view_name_part in active_view.Name
    is_correct_type = active_view.ViewType == target_view_type

    if not (is_correct_name and is_correct_type):
        print("# Error: Active view '{}' (Type: {}) is not the target '{}' RCP view.".format(
            active_view.Name, active_view.ViewType.ToString(), target_view_name_part))
    elif not isinstance(active_view, ViewPlan):
        print("# Error: Active view '{}' is not a Plan View (Floor Plan, RCP, etc.) and does not have a View Range.".format(active_view.Name))
    else:
        view_plan = active_view # Cast to ViewPlan
        print("# Target view found: '{}' (Type: {})".format(view_plan.Name, view_plan.ViewType.ToString()))

        # Find the required levels
        level_cut = find_level_by_name(doc, target_level_name_cut)
        level_bottom = find_level_by_name(doc, target_level_name_bottom)
        level_view_depth = find_level_by_name(doc, target_level_name_view_depth)

        if level_cut and level_bottom and level_view_depth:
            print("# Levels found: Cut='{}' (ID:{}), Bottom='{}' (ID:{}), ViewDepth='{}' (ID:{})".format(
                level_cut.Name, level_cut.Id.IntegerValue,
                level_bottom.Name, level_bottom.Id.IntegerValue,
                level_view_depth.Name, level_view_depth.Id.IntegerValue))

            try:
                # Get the current view range
                view_range = view_plan.GetViewRange()

                # Set Level IDs for each plane
                # For RCP, Top is typically associated with the level above the primary level
                # Assuming Top should also be associated with L5 like Cut and View Depth
                view_range.SetLevelId(PlanViewPlane.TopClipPlane, level_view_depth.Id) # Assuming L5 for Top as well
                view_range.SetLevelId(PlanViewPlane.CutPlane, level_cut.Id)
                view_range.SetLevelId(PlanViewPlane.BottomClipPlane, level_bottom.Id)
                view_range.SetLevelId(PlanViewPlane.ViewDepthPlane, level_view_depth.Id)

                # Set Offsets for each plane (convert mm to feet)
                cut_offset_feet = mm_to_feet(cut_plane_offset_mm)
                view_range.SetOffset(PlanViewPlane.TopClipPlane, 0.0) # Default offset for Top assumed 0
                view_range.SetOffset(PlanViewPlane.CutPlane, cut_offset_feet)
                view_range.SetOffset(PlanViewPlane.BottomClipPlane, 0.0) # Offset relative to Bottom level (L4)
                view_range.SetOffset(PlanViewPlane.ViewDepthPlane, 0.0) # Offset relative to View Depth level (L5)

                # Apply the modified view range
                view_plan.SetViewRange(view_range)

                print("# Successfully adjusted View Range for view '{}':".format(view_plan.Name))
                print("#   Top: Level '{}', Offset 0.0 ft".format(level_view_depth.Name))
                print("#   Cut: Level '{}', Offset {:.4f} ft ({} mm)".format(level_cut.Name, cut_offset_feet, cut_plane_offset_mm))
                print("#   Bottom: Level '{}', Offset 0.0 ft".format(level_bottom.Name))
                print("#   View Depth: Level '{}', Offset 0.0 ft".format(level_view_depth.Name))

            except System.Exception as e:
                print("# Error setting View Range for view '{}'. Exception: {}".format(view_plan.Name, str(e)))
        else:
            # Error messages already printed by find_level_by_name if levels weren't found
            print("# Cannot proceed without finding all required levels.")