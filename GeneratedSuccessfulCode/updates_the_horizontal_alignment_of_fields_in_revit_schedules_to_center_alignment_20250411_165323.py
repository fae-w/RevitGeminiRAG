# Purpose: This script updates the horizontal alignment of fields in Revit schedules to center alignment.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSchedule,
    ScheduleDefinition,
    ScheduleField,
    ScheduleHorizontalAlignment
)
from System import ArgumentOutOfRangeException, Exception as SystemException

# --- Configuration ---
target_alignment = ScheduleHorizontalAlignment.Center

# --- Initialization ---
processed_schedule_count = 0
updated_field_count = 0
error_count = 0

# --- Step 1: Collect Schedules (Non-Templates) ---
collector = FilteredElementCollector(doc).OfClass(ViewSchedule)
# Filter out view templates
schedules = [s for s in collector if s and not s.IsTemplate]

# --- Step 2: Iterate and Process Schedules ---
for schedule in schedules:
    schedule_name = "Unknown"
    schedule_id_str = "Unknown"
    try:
        schedule_name = schedule.Name
        schedule_id_str = schedule.Id.ToString()
        processed_schedule_count += 1

        # Access the schedule definition
        schedule_def = schedule.Definition

        # Check if schedule_def is valid
        if schedule_def is None:
             # print("# Info: Schedule '{{0}}' (ID: {{1}}) has no Definition. Skipping.".format(schedule_name, schedule_id_str)) # Optional info
             continue # Skip to next schedule

        # Get the number of fields in the schedule definition
        field_count = schedule_def.GetFieldCount()

        # Iterate through each field (column) in the schedule definition
        for i in range(field_count):
            try:
                field = schedule_def.GetField(i)

                # Check if the field is valid and if its alignment needs updating
                if field is not None and field.HorizontalAlignment != target_alignment:
                    # Set the horizontal alignment
                    field.HorizontalAlignment = target_alignment
                    updated_field_count += 1
                    # print("# Updated field {{0}} in schedule '{{1}}'".format(i, schedule_name)) # Optional info

            except ArgumentOutOfRangeException:
                error_count += 1
                print("# Error: ArgumentOutOfRangeException accessing field index {{0}} for schedule '{{1}}' (ID: {{2}}).".format(i, schedule_name, schedule_id_str))
                # Continue to the next field if possible
            except SystemException as e_field:
                error_count += 1
                print("# Error processing field index {{0}} in schedule '{{1}}' (ID: {{2}}): {{3}}".format(i, schedule_name, schedule_id_str, e_field))

    except SystemException as e_schedule:
        error_count += 1
        # Try to get ID safely if the initial property access failed
        if schedule_id_str == "Unknown":
            try: schedule_id_str = schedule.Id.ToString()
            except: schedule_id_str = "[ID Unavailable]"
        print("# Error processing schedule '{{0}}' (ID: {{1}}): {{2}}".format(schedule_name, schedule_id_str, e_schedule))

# --- Optional: Print Summary (Comment out/remove for final script) ---
# print("--- Schedule Field Alignment Summary ---")
# print("Schedules checked: {}".format(processed_schedule_count))
# print("Fields updated to Center alignment: {}".format(updated_field_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Non-Template Schedules Found: {}".format(len(schedules)))
# --- End Optional Summary ---