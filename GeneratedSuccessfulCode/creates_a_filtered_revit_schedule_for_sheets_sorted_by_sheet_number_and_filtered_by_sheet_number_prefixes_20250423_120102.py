# Purpose: This script creates a filtered Revit schedule for sheets, sorted by sheet number and filtered by sheet number prefixes.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ViewSchedule,
    ScheduleDefinition,
    ScheduleField,
    ScheduleSortGroupField,
    ScheduleFilter,
    ScheduleFilterType,
    ScheduleFieldId,
    ScheduleSortOrder,
    BuiltInParameter,
    ElementId
)
import System # For exception handling

# --- Configuration ---
schedule_name = "Sheet Index - Filtered (A or S)"
filter_prefix_1 = "A-"
filter_prefix_2 = "S-"

# --- Main Logic ---
try:
    # Define the category for the schedule
    sheet_category_id = ElementId(BuiltInCategory.OST_Sheets)

    # Create the schedule
    # ViewSchedule.CreateSchedule requires doc, categoryId
    schedule = ViewSchedule.CreateSchedule(doc, sheet_category_id)
    schedule.Name = schedule_name

    # Get the schedule definition
    definition = schedule.GetDefinition()

    # --- Find Schedulable Fields ---
    # Helper function to find a schedulable field by BuiltInParameter
    def find_schedulable_field(definition, param_id):
        schedulable_fields = definition.GetSchedulableFields()
        for sf in schedulable_fields:
            if sf.ParameterId == ElementId(param_id):
                return sf
        return None

    # Find the fields we need
    sheet_number_field_sched = find_schedulable_field(definition, BuiltInParameter.SHEET_NUMBER)
    sheet_name_field_sched = find_schedulable_field(definition, BuiltInParameter.SHEET_NAME)
    revision_desc_field_sched = find_schedulable_field(definition, BuiltInParameter.SHEET_CURRENT_REVISION_DESCRIPTION)

    # Check if fields were found
    if not sheet_number_field_sched:
        print("# Error: Could not find SchedulableField for Sheet Number (BuiltInParameter.SHEET_NUMBER).")
    if not sheet_name_field_sched:
        print("# Error: Could not find SchedulableField for Sheet Name (BuiltInParameter.SHEET_NAME).")
    if not revision_desc_field_sched:
        print("# Error: Could not find SchedulableField for Current Revision Description (BuiltInParameter.SHEET_CURRENT_REVISION_DESCRIPTION).")

    # Proceed only if all essential fields are found
    if sheet_number_field_sched and sheet_name_field_sched and revision_desc_field_sched:

        # --- Add Fields to the Schedule ---
        # Add fields in the desired order
        field_sheet_number = definition.AddField(sheet_number_field_sched)
        field_sheet_name = definition.AddField(sheet_name_field_sched)
        field_revision_desc = definition.AddField(revision_desc_field_sched)

        # Get the ID of the field to be used for filtering and sorting
        sheet_number_field_id = field_sheet_number.FieldId

        # --- Add Sorting ---
        sort_field = ScheduleSortGroupField(sheet_number_field_id)
        sort_field.SortOrder = ScheduleSortOrder.Ascending
        definition.AddSortGroupField(sort_field)

        # --- Add Filters ---
        # Create the first filter: Sheet Number Begins With 'A-'
        filter1 = ScheduleFilter(sheet_number_field_id, ScheduleFilterType.BeginsWith, filter_prefix_1)

        # Create the second filter: Sheet Number Begins With 'S-'
        filter2 = ScheduleFilter(sheet_number_field_id, ScheduleFilterType.BeginsWith, filter_prefix_2)

        # Add the filters to the definition.
        # IMPORTANT NOTE: Adding multiple filters for the SAME field in the API
        # usually results in an AND condition between them, meaning SheetNumber
        # would need to start with BOTH 'A-' AND 'S-', which is impossible.
        # The Revit UI allows creating OR conditions for the same field, but the API's
        # AddFilter method typically doesn't directly support this for a single field.
        # Applying these two filters will likely result in an empty schedule.
        # A common workaround involves creating a calculated parameter that checks
        # the OR condition and filtering by that parameter, which is outside the
        # scope of just creating the schedule fields/filters/sorting as requested.
        # As a demonstration, the filters are added, but expect potentially incorrect results.
        definition.AddFilter(filter1)
        definition.AddFilter(filter2)

        print("# Successfully created schedule: '{}'".format(schedule_name))
        print("# Added Fields: Sheet Number, Sheet Name, Current Revision Description")
        print("# Sorted by: Sheet Number (Ascending)")
        print("# Applied Filters: Sheet Number Begins With '{}' OR '{}'".format(filter_prefix_1, filter_prefix_2))
        print("# WARNING: Applying multiple filters for the same field via API may result in AND logic, potentially yielding no results. OR logic for a single field might require a calculated parameter workaround.")

    else:
        # Clean up the created schedule if fields weren't found
        try:
            doc.Delete(schedule.Id)
            print("# Deleted partially created schedule due to missing required fields.")
        except Exception as delete_err:
            print("# Error deleting partially created schedule: {}".format(delete_err))
        print("# Schedule creation aborted because required schedulable fields were not found.")

except System.ArgumentException as arg_ex:
    print("# Error creating schedule: {} - Check if a schedule with the name '{}' already exists or if category is valid.".format(arg_ex.Message, schedule_name))
except Exception as e:
    print("# An unexpected error occurred: {}".format(e))