# Purpose: This script creates a window schedule filtered by level and places it on a new sheet.

# Purpose: This script creates a window schedule filtered by level, places it on a new sheet, and handles potential errors during the process.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    Level,
    ViewSchedule,
    ScheduleField,
    ScheduleFieldId,
    SchedulableField,
    ScheduleFilter,
    ScheduleFilterType,
    ScheduleSortGroupField,
    ScheduleSortOrder,
    ViewSheet,
    ScheduleSheetInstance,
    XYZ,
    BuiltInParameter
)

# --- Configuration ---
TARGET_LEVEL_NAME = "Level 2"
SCHEDULE_NAME = "Window Schedule - Level 2"
SHEET_NUMBER = "A201" # Default start number
SHEET_NAME = "Window Schedule"
# --- End Configuration ---

# 1. Find the target Level ElementId
target_level_id = ElementId.InvalidElementId
level_collector = FilteredElementCollector(doc).OfClass(Level)
for level in level_collector:
    if level.Name == TARGET_LEVEL_NAME:
        target_level_id = level.Id
        break

if target_level_id == ElementId.InvalidElementId:
    print("# Error: Level named '{}' not found in the document.".format(TARGET_LEVEL_NAME))
else:
    # 2. Define Category ID for Windows
    category_id = ElementId(BuiltInCategory.OST_Windows)

    # 3. Create the Schedule View
    try:
        schedule = ViewSchedule.CreateSchedule(doc, category_id)
        schedule.Name = SCHEDULE_NAME
        # print("# Created Schedule: {}".format(SCHEDULE_NAME)) # Escaped
    except Exception as create_ex:
        print("# Error creating schedule: {}".format(create_ex))
        schedule = None

    if schedule:
        sched_def = schedule.Definition

        # 4. Find Schedulable Fields (Type Mark, Width, Height, Sill Height, Level)
        param_ids_to_find = {
            "Type Mark": BuiltInParameter.ALL_MODEL_TYPE_MARK,
            "Width": BuiltInParameter.WINDOW_WIDTH,
            "Height": BuiltInParameter.WINDOW_HEIGHT,
            "Sill Height": BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM,
            "Level": BuiltInParameter.SCHEDULE_LEVEL_PARAM
        }

        found_field_ids = {}
        level_field_id = ScheduleFieldId.InvalidScheduleFieldId

        schedulable_fields = sched_def.GetSchedulableFields()
        for sf in schedulable_fields:
            param_id = sf.ParameterId
            # Find fields based on BuiltInParameter ID
            for name, bip_id in param_ids_to_find.items():
                if param_id == ElementId(bip_id):
                    found_field_ids[name] = sf.FieldId
                    if name == "Level":
                        level_field_id = sf.FieldId
                    # print("# Found schedulable field: {} (ID: {})".format(name, sf.FieldId)) # Escaped
                    break # Move to next schedulable field once matched

        # 5. Add Fields to Schedule Definition
        fields_added = True
        # Define the order we want the fields to appear
        field_order = ["Type Mark", "Width", "Height", "Sill Height"]
        for field_name in field_order:
            if field_name in found_field_ids:
                try:
                    sched_def.AddField(found_field_ids[field_name])
                    # print("# Added field to schedule: {}".format(field_name)) # Escaped
                except Exception as add_field_ex:
                    print("# Warning: Could not add field '{}' to schedule. Error: {}".format(field_name, add_field_ex))
                    fields_added = False
            else:
                print("# Warning: Schedulable field '{}' not found for Windows category.".format(field_name))
                fields_added = False

        # Check if Level field was found for filtering
        if level_field_id == ScheduleFieldId.InvalidScheduleFieldId:
             print("# Error: Could not find the 'Level' field to apply the filter.")
             fields_added = False # Prevent further steps if filtering isn't possible

        if fields_added:
            # 6. Add Filter to Schedule Definition (by Level 2 ID)
            try:
                level_filter = ScheduleFilter(level_field_id, ScheduleFilterType.Equal, target_level_id)
                sched_def.AddFilter(level_filter)
                # print("# Added filter for Level: {}".format(TARGET_LEVEL_NAME)) # Escaped
            except Exception as filter_ex:
                print("# Error adding schedule filter: {}".format(filter_ex))
                schedule = None # Invalidate schedule if filter fails

    if schedule: # Proceed only if schedule created and fields/filter added successfully
        # 7. Find a Title Block Type
        title_block_type_id = ElementId.InvalidElementId
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
        first_title_block_type = collector.FirstElement()

        if first_title_block_type:
            title_block_type_id = first_title_block_type.Id
            # print("# Found title block type: {} (ID: {})".format(first_title_block_type.Name, title_block_type_id)) # Escaped
        else:
            print("# Error: No Title Block types found in the project. Cannot create sheet.")

        if title_block_type_id != ElementId.InvalidElementId:
            # 8. Create a new Sheet
            new_sheet = None
            try:
                new_sheet = ViewSheet.Create(doc, title_block_type_id)
                if new_sheet:
                    # Try to set a unique sheet number and name
                    temp_sheet_num = SHEET_NUMBER
                    temp_sheet_name = SHEET_NAME
                    counter = 1
                    max_attempts = 100 # Prevent infinite loop
                    existing_sheet_numbers = [s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()]

                    while temp_sheet_num in existing_sheet_numbers and counter < max_attempts:
                        counter += 1
                        # Example: A201 -> A202 etc. Modify logic if needed for different numbering schemes.
                        base_num_str = ''.join(filter(str.isdigit, SHEET_NUMBER))
                        prefix = SHEET_NUMBER.replace(base_num_str, '')
                        if base_num_str:
                             base_num = int(base_num_str)
                             temp_sheet_num = prefix + str(base_num + counter -1)
                        else: # Fallback if no number found
                             temp_sheet_num = SHEET_NUMBER + "_" + str(counter)


                    if counter < max_attempts:
                        try:
                            new_sheet.SheetNumber = temp_sheet_num
                            new_sheet.Name = temp_sheet_name
                            # print("# Created new sheet: {} - {} (ID: {})".format(temp_sheet_num, temp_sheet_name, new_sheet.Id)) # Escaped
                        except Exception as set_name_num_ex:
                            print("# Warning: Could not set sheet number/name. Error: {}".format(set_name_num_ex))
                    else:
                        print("# Warning: Could not find an unused sheet number starting from {} after {} attempts.".format(SHEET_NUMBER, max_attempts))
                else:
                    print("# Error: ViewSheet.Create returned None.")
            except Exception as sheet_ex:
                print("# Error creating sheet: {}".format(sheet_ex))

            if new_sheet and schedule:
                # 9. Place Schedule on Sheet
                try:
                    # Calculate a placement point (e.g., center of the sheet)
                    sheet_bb = new_sheet.get_BoundingBox(None) # Pass None for view to get sheet bounds
                    if sheet_bb and sheet_bb.Min and sheet_bb.Max:
                        center_point = (sheet_bb.Min + sheet_bb.Max) / 2.0
                        # Adjust Z slightly if needed, though usually 0 is fine for sheet placement
                        placement_point = XYZ(center_point.X, center_point.Y, 0)
                    else:
                        placement_point = XYZ(1, 1, 0) # Fallback placement
                        print("# Warning: Could not get sheet bounding box. Placing schedule at default location.")

                    # Create the schedule instance on the sheet
                    schedule_instance = ScheduleSheetInstance.Create(doc, new_sheet.Id, schedule.Id, placement_point)
                    if schedule_instance:
                        # print("# Successfully placed schedule '{}' on sheet '{}'.".format(schedule.Name, new_sheet.SheetNumber)) # Escaped
                        pass # Success
                    else:
                        print("# Error: ScheduleSheetInstance.Create returned None.")
                except Exception as place_ex:
                    print("# Error placing schedule on sheet: {}".format(place_ex))

# Final check if Level 2 was not found initially
# (The 'else' block for the initial level check takes care of this path)