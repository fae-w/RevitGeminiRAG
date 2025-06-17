# Purpose: This script filters a Revit schedule based on a specified parameter value.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    ViewSchedule,
    ScheduleDefinition,
    ScheduleField,
    ScheduleFieldId,
    ScheduleFilter,
    ScheduleFilterType,
    BuiltInParameter,
    ElementId # Added ElementId import
)
# Import System explicitly if needed for Enum conversion (though not strictly required by the corrected logic below)
# import System

# --- Configuration ---
target_parameter_name = "Cost"
filter_value = 1000.0  # Use double for numeric comparison
filter_comparison_type = ScheduleFilterType.GreaterThan
# --- End Configuration ---

# Get the active view
active_view = uidoc.ActiveView

if not isinstance(active_view, ViewSchedule):
    print("# Error: Active view is not a schedule.")
else:
    schedule = active_view
    definition = schedule.Definition

    # Check if filtering is allowed on this schedule
    if not definition.CanFilter():
        print("# Error: Filtering is not enabled for this schedule type.")
    else:
        # Find the ScheduleField corresponding to the 'Cost' parameter
        cost_field_id = None
        cost_field = None
        found_field = False

        field_ids = definition.GetFieldOrder()
        for field_id in field_ids:
            field = definition.GetField(field_id)
            # Attempt to get field name
            field_name = ""
            try:
                # Use GetFieldName() for newer API versions or GetName() as fallback
                try:
                    field_name = field.GetFieldName() # Preferred method in newer APIs
                except AttributeError:
                    field_name = field.GetName() # Fallback for older APIs
            except Exception as e_name:
                # Optional: Log error getting field name if needed for debugging
                # print("# Debug: Could not get name for field ID {}: {}".format(field_id.IntegerValue, e_name))
                pass # Continue checking other fields

            if field_name == target_parameter_name:
                # Check if the field type is suitable for value-based filtering
                if definition.CanFilterByValue(field.ScheduleFieldId):
                    cost_field_id = field.ScheduleFieldId
                    cost_field = field
                    found_field = True
                    # print("# Debug: Found field '{}' with ID {}".format(target_parameter_name, cost_field_id)) # Optional Debug
                    break
                else:
                    print("# Error: Field '{{}}' found, but it cannot be used for value-based filtering in this schedule.".format(target_parameter_name))
                    found_field = True # Mark as found to prevent 'not found' message
                    break # Stop searching

        if not found_field:
            print("# Error: Field named '{{}}' not found in the schedule fields.".format(target_parameter_name))
        elif cost_field_id:
            # Create the filter
            try:
                # Constructor for double value: ScheduleFilter(ScheduleFieldId, ScheduleFilterType, double)
                new_filter = ScheduleFilter(cost_field_id, filter_comparison_type, filter_value)

                # Check current filter count before adding
                max_filters = definition.MaxNumberOfFilters # Use API property for max filters
                if definition.GetFilterCount() >= max_filters:
                    print("# Error: Cannot add filter. Schedule already has the maximum number of filters ({{}}).".format(max_filters))
                else:
                    # Clear existing filters targeting the same field to avoid conflicts (optional, adjust if needed)
                    # filters_to_remove = []
                    # for i in range(definition.GetFilterCount()):
                    #     existing_filter = definition.GetFilter(i)
                    #     if existing_filter.FieldId == cost_field_id:
                    #         filters_to_remove.append(i)
                    # # Remove in reverse order to maintain indices
                    # for index in sorted(filters_to_remove, reverse=True):
                    #     definition.RemoveFilter(index)
                    #     print("# Debug: Removed existing filter for field '{}'".format(target_parameter_name)) # Optional Debug

                    # Add the filter to the schedule definition
                    # IMPORTANT: This modification requires an external Transaction (assumed handled by C# wrapper).
                    definition.AddFilter(new_filter)
                    # print("# Filter '{{}} > {{}}' added to schedule '{{}}'.".format(target_parameter_name, filter_value, schedule.Name)) # Optional success message

            except Exception as e:
                print("# Error adding filter: {{}}".format(e))
                print("# Ensure the '{{}}' field is a numeric type compatible with the '>' comparison.".format(target_parameter_name))