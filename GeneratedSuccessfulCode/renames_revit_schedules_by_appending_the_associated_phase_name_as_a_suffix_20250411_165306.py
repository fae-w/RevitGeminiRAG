# Purpose: This script renames Revit schedules by appending the associated phase name as a suffix.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSchedule,
    Phase,
    ElementId,
    BuiltInParameter
)
import System # For Exception handling

# --- Initialization ---
renamed_count = 0
skipped_already_suffixed_count = 0
skipped_no_phase_param_count = 0
skipped_invalid_phase_ref_count = 0
error_count = 0

# --- Step 1: Collect Schedules (Non-Templates) ---
# Using OfClass(ViewSchedule) is efficient
collector = FilteredElementCollector(doc).OfClass(ViewSchedule)
# Filter out view templates, which are also ViewSchedules sometimes
schedules = [s for s in collector if not s.IsTemplate]

# --- Step 2: Iterate and Rename Schedules ---
for schedule in schedules:
    original_name = "" # Initialize for error handling context
    schedule_id_str = "Unknown" # Initialize for error handling context
    try:
        schedule_id_str = schedule.Id.ToString()
        original_name = schedule.Name

        # Get the SCHEDULE_PHASE parameter - this determines which phase the schedule reports on
        phase_param = schedule.get_Parameter(BuiltInParameter.SCHEDULE_PHASE)

        # Check if the schedule has a phase parameter and if it has a value set
        if phase_param and phase_param.HasValue:
            phase_id = phase_param.AsElementId()

            # Check if the phase ID is valid (not InvalidElementId, which often represents 'None')
            if phase_id != ElementId.InvalidElementId:
                phase_elem = doc.GetElement(phase_id)

                # Check if the retrieved element is actually a Phase element
                if phase_elem and isinstance(phase_elem, Phase):
                    phase_name = phase_elem.Name
                    # Ensure phase name is not empty or null before using it
                    if phase_name and len(phase_name.strip()) > 0:
                        # Construct the desired suffix (e.g., "_Phase 1")
                        suffix = "_{}".format(phase_name)

                        # Check if the name already ends with the correct suffix for its CURRENT phase
                        # This prevents adding the suffix multiple times if the script is rerun
                        if not original_name.endswith(suffix):
                            # Construct the new name by appending the suffix
                            new_name = original_name + suffix

                            try:
                                # Attempt to rename the schedule
                                schedule.Name = new_name
                                renamed_count += 1
                                # print("# Renamed '{}' to '{}'".format(original_name, new_name)) # Debug comment
                            except System.ArgumentException as arg_ex:
                                # Handle potential errors like duplicate names
                                error_count += 1
                                print("# Error renaming schedule '{}' (ID: {}): {}. New name '{}' might already exist.".format(original_name, schedule_id_str, arg_ex.Message, new_name))
                            except Exception as e_rename:
                                # Handle other potential errors during renaming
                                error_count += 1
                                print("# Unexpected error renaming schedule '{}' (ID: {}): {}".format(original_name, schedule_id_str, e_rename))
                        else:
                            # Name already ends with the correct suffix for its phase
                            skipped_already_suffixed_count += 1
                            # print("# Skipping '{}' (ID: {}) as it already has the correct phase suffix '{}'".format(original_name, schedule_id_str, suffix)) # Debug comment
                    else:
                        # Phase name is empty or invalid, cannot create suffix
                         skipped_invalid_phase_ref_count += 1
                         print("# Warning: Phase name for schedule '{}' (ID: {}) is empty or invalid. Skipping suffix addition.".format(original_name, schedule_id_str))

                else:
                    # Phase element ID points to nothing or not a Phase element (e.g., phase was deleted)
                    skipped_invalid_phase_ref_count += 1
                    print("# Warning: Could not find valid Phase element for schedule '{}' (ID: {}) with Phase ID: {}. Skipping suffix addition.".format(original_name, schedule_id_str, phase_id))
            else:
                # Phase ID is InvalidElementId (e.g., Phase "None" was selected in properties)
                skipped_invalid_phase_ref_count += 1
                print("# Warning: Schedule '{}' (ID: {}) has Phase set to 'None' (InvalidElementId). Skipping suffix addition.".format(original_name, schedule_id_str))
        else:
            # Schedule does not have a SCHEDULE_PHASE parameter or it has no value set
            # This is expected for certain schedule types like Key Schedules, Revision Schedules, View Lists, Sheet Lists.
            skipped_no_phase_param_count += 1
            # print("# Skipping '{}' (ID: {}) as it doesn't have a valid Phase parameter (Might be Key/Revision/List etc.).".format(original_name, schedule_id_str)) # Debug comment

    except Exception as e_outer:
        # Handle potential errors accessing schedule properties like Name or Parameter
        error_count += 1
        # Try to get ID again in case the error happened before it was assigned
        if schedule_id_str == "Unknown":
            try:
                schedule_id_str = schedule.Id.ToString()
            except:
                 schedule_id_str = "Unknown" # Keep it Unknown if ID access also fails

        print("# Error processing schedule (ID: {}), original name may be '{}': {}".format(schedule_id_str, original_name, e_outer))


# --- Optional: Print summary to RevitPythonShell output (comment out if not desired) ---
# total_processed = renamed_count + skipped_already_suffixed_count + skipped_no_phase_param_count + skipped_invalid_phase_ref_count + error_count
# print("--- Schedule Renaming Summary ---")
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (already suffixed correctly for current phase): {}".format(skipped_already_suffixed_count))
# print("Skipped (no applicable phase parameter found): {}".format(skipped_no_phase_param_count))
# print("Skipped (invalid phase reference or phase name): {}".format(skipped_invalid_phase_ref_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Schedules processed: {} (out of {} non-template schedules found)".format(total_processed, len(schedules)))
# --- End Optional Summary ---