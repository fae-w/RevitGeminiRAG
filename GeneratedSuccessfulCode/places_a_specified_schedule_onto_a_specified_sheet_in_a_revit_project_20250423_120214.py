# Purpose: This script places a specified schedule onto a specified sheet in a Revit project.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSchedule,
    ViewSheet,
    ScheduleSheetInstance,
    XYZ,
    ElementId
)
import System # Required for exception handling

# --- Configuration ---
target_schedule_name = "Door Schedule - L1 Blocks"
target_sheet_name = "Schedules Sheet"
# --- End Configuration ---

# 1. Find the target Schedule View
schedule_to_place = None
schedule_collector = FilteredElementCollector(doc).OfClass(ViewSchedule)
for schedule in schedule_collector:
    if schedule.Name == target_schedule_name:
        schedule_to_place = schedule
        break

# 2. Find the target Sheet View
sheet_to_place_on = None
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
for sheet in sheet_collector:
    if sheet.Name == target_sheet_name:
        sheet_to_place_on = sheet
        break

# 3. Check if both elements were found
if schedule_to_place is None:
    print("# Error: Schedule named '{{}}' not found.".format(target_schedule_name))
elif sheet_to_place_on is None:
    print("# Error: Sheet named '{{}}' not found.".format(target_sheet_name))
else:
    # 4. Determine Placement Point
    # Try to calculate a center point, otherwise use a default
    placement_point = XYZ(1, 1, 0) # Default fallback
    try:
        sheet_bb = sheet_to_place_on.get_BoundingBox(None) # Pass None for view to get sheet bounds
        if sheet_bb and sheet_bb.Min and sheet_bb.Max:
            center_point = (sheet_bb.Min + sheet_bb.Max) / 2.0
            placement_point = XYZ(center_point.X, center_point.Y, 0)
            # print("# Calculated placement point at sheet center: {{}}".format(placement_point)) # Escaped
        else:
             print("# Warning: Could not get sheet bounding box for '{{}}'. Using default placement point.".format(target_sheet_name))
    except Exception as bb_ex:
        print("# Warning: Error getting sheet bounding box: {{}}. Using default placement point.".format(bb_ex))

    # 5. Check if the schedule is already placed on the sheet
    existing_placement = None
    placed_schedule_collector = FilteredElementCollector(doc, sheet_to_place_on.Id).OfClass(ScheduleSheetInstance)
    for placed_instance in placed_schedule_collector:
        try:
            if placed_instance.ScheduleId == schedule_to_place.Id:
                existing_placement = placed_instance
                break
        except Exception as check_ex:
             print("# Warning: Error checking existing schedule instance: {{}}".format(check_ex)) # Escaped

    if existing_placement:
        print("# Info: Schedule '{{}}' is already placed on sheet '{{}}'.".format(target_schedule_name, target_sheet_name))
    else:
        # 6. Place the Schedule on the Sheet
        try:
            schedule_instance = ScheduleSheetInstance.Create(doc, sheet_to_place_on.Id, schedule_to_place.Id, placement_point)
            if schedule_instance:
                print("# Successfully placed schedule '{{}}' on sheet '{{}}'.".format(target_schedule_name, target_sheet_name))
            else:
                print("# Error: ScheduleSheetInstance.Create returned None for schedule '{{}}' on sheet '{{}}'.".format(target_schedule_name, target_sheet_name))
        except System.ArgumentException as arg_ex:
             print("# Error placing schedule: {{}}. This might happen if the schedule view isn't suitable for placement (e.g., already on another sheet, or a non-placeable type). Schedule: '{{}}', Sheet: '{{}}'.".format(arg_ex.Message, target_schedule_name, target_sheet_name))
        except Exception as place_ex:
            print("# Error placing schedule '{{}}' on sheet '{{}}': {{}}".format(target_schedule_name, target_sheet_name, place_ex))

# --- End Script ---