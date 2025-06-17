# Purpose: This script renames Revit schedules by adding a suffix if a specific field is absent.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for Exception handling
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSchedule,
    ScheduleDefinition,
    ScheduleField,
    BuiltInParameter,
    ElementId
)
from Autodesk.Revit.Exceptions import InvalidOperationException
import System # For Exception handling

# --- Configuration ---
SUFFIX_TO_ADD = "_NoTypeMark"
# Define the parameter we are looking for (Type Mark)
TARGET_PARAMETER_BIP = BuiltInParameter.ALL_MODEL_TYPE_MARK

# --- Initialization ---
renamed_count = 0
skipped_already_suffixed_count = 0
skipped_found_field_count = 0
error_count = 0
target_param_id = None # Initialize to None

# Get the ElementId for the target BuiltInParameter
try:
    # Attempt to create ElementId for the BuiltInParameter enum value
    # Direct casting to int is needed for ElementId constructor with BuiltInParameter
    target_param_id = ElementId(TARGET_PARAMETER_BIP)
except System.Exception as e_bip:
    print("# Error: Could not get ElementId for BuiltInParameter {0}. Stopping script. Error: {1}".format(TARGET_PARAMETER_BIP, e_bip))
    # If we can't get the target parameter ID, we cannot proceed.
    raise System.Exception("Failed to initialize target parameter ID.")

# Check if target_param_id was successfully obtained
if target_param_id is None or target_param_id == ElementId.InvalidElementId:
     print("# Error: Failed to obtain a valid ElementId for BuiltInParameter {0}. Stopping script.".format(TARGET_PARAMETER_BIP))
     raise System.Exception("Invalid target parameter ID obtained.")


# --- Step 1: Collect Schedules (Non-Templates) ---
collector = FilteredElementCollector(doc).OfClass(ViewSchedule)
# Filter out view templates, which are also ViewSchedules sometimes
schedules = [s for s in collector if s and not s.IsTemplate] # Added check for 's' being not None

# --- Step 2: Iterate and Process Schedules ---
for schedule in schedules:
    original_name = "Unknown"
    schedule_id_str = "Unknown"
    try:
        schedule_id_str = schedule.Id.ToString()
        original_name = schedule.Name

        # Access the schedule definition
        schedule_def = schedule.Definition

        # Flag to track if the target field is found
        found_target_field = False

        # Check if schedule_def is valid
        if schedule_def is None:
             print("# Warning: Schedule '{0}' (ID: {1}) has no Definition. Skipping.".format(original_name, schedule_id_str))
             continue # Skip to next schedule

        # Get the number of fields in the schedule definition
        field_count = schedule_def.GetFieldCount()

        # Iterate through each field in the schedule definition
        for i in range(field_count):
            try:
                field = schedule_def.GetField(i)
                # Check if the field's parameter ID matches the target parameter ID
                # Ensure field and ParameterId are not None before comparing
                if field is not None and field.ParameterId is not None and field.ParameterId == target_param_id:
                    found_target_field = True
                    break # Found the field, no need to check further fields

            except System.ArgumentOutOfRangeException:
                error_count += 1
                print("# Error: ArgumentOutOfRangeException accessing field index {0} for schedule '{1}' (ID: {2}).".format(i, original_name, schedule_id_str))
                break # Stop checking fields for this schedule
            except System.Exception as e_field:
                error_count += 1
                print("# Error: Failed accessing field at index {0} for schedule '{1}' (ID: {2}): {3}".format(i, original_name, schedule_id_str, e_field))
                # Continue checking other fields, but note the error

        # --- Step 3: Rename if Target Field Not Found ---
        if not found_target_field:
            # Check if the name already ends with the suffix
            if not original_name.endswith(SUFFIX_TO_ADD):
                new_name = original_name + SUFFIX_TO_ADD
                try:
                    # Attempt to rename the schedule
                    schedule.Name = new_name
                    renamed_count += 1
                    # print("# Renamed '{0}' to '{1}'".format(original_name, new_name)) # Debug
                except System.ArgumentException as arg_ex:
                    error_count += 1
                    print("# Error renaming schedule '{0}' (ID: {1}): {2}. New name '{3}' might already exist or be invalid.".format(original_name, schedule_id_str, arg_ex.Message, new_name))
                except System.Exception as e_rename:
                    error_count += 1
                    print("# Unexpected error renaming schedule '{0}' (ID: {1}): {2}".format(original_name, schedule_id_str, e_rename))
            else:
                skipped_already_suffixed_count += 1
                # print("# Skipping '{0}' (ID: {1}) as it already ends with '{2}'".format(original_name, schedule_id_str, SUFFIX_TO_ADD)) # Debug
        else:
            skipped_found_field_count += 1
            # print("# Skipping '{0}' (ID: {1}) as it contains the 'Type Mark' field.".format(original_name, schedule_id_str)) # Debug

    except System.NullReferenceException as nre:
        error_count += 1
        # Try to get ID safely for error message
        safe_id_nre = "[ID Unavailable]"
        try:
            safe_id_nre = schedule.Id.ToString()
        except: pass
        print("# Error: Null reference encountered while processing schedule (ID: {0}). Schedule might be invalid or corrupted. Details: {1}".format(safe_id_nre, nre))
    except InvalidOperationException as inv_op_ex:
         error_count += 1
         # Try to get ID/Name safely for error message
         safe_id_invop = "[ID Unavailable]"
         safe_name_invop = "[Name Unavailable]"
         try: safe_id_invop = schedule.Id.ToString()
         except: pass
         try: safe_name_invop = schedule.Name
         except: pass
         print("# Error: Invalid Operation while processing schedule '{0}' (ID: {1}): {2}".format(safe_name_invop, safe_id_invop, inv_op_ex.Message))
    except System.Exception as e_outer:
        # Handle other potential errors accessing schedule properties like Name or Definition
        error_count += 1
        # Try to get ID/Name again safely for the error message
        safe_id = "[ID Unavailable]"
        safe_name = "[Name Unavailable]"
        try:
            safe_id = schedule.Id.ToString()
        except:
            pass # Keep default if ID access fails

        # Use original_name if it was successfully assigned earlier in the 'try' block,
        # otherwise try to get the name safely.
        if original_name != "Unknown":
             safe_name = original_name
        else:
             try:
                 safe_name = schedule.Name
             except:
                 pass # Keep default '[Name Unavailable]' if Name access fails

        print("# Error processing schedule (ID: {0}, Current Name: '{1}'): {2}".format(safe_id, safe_name, e_outer))


# --- Optional: Print summary (Comment out/remove for final script) ---
# print("--- Schedule Renaming Summary ('{0}' suffix) ---".format(SUFFIX_TO_ADD))
# print("Successfully renamed: {0}".format(renamed_count))
# print("Skipped (already suffixed): {0}".format(skipped_already_suffixed_count))
# print("Skipped (contained 'Type Mark' field): {0}".format(skipped_found_field_count))
# print("Errors encountered: {0}".format(error_count))
# print("Total Non-Template Schedules Checked: {0}".format(len(schedules)))
# --- End Optional Summary ---