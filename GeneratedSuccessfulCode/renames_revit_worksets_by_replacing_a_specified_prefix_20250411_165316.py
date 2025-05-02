# Purpose: This script renames Revit worksets by replacing a specified prefix.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException
import System # For ArgumentException

from Autodesk.Revit.DB import (
    FilteredWorksetCollector,
    WorksetKind,
    WorksetTable,
    WorksetId,
    Workset # Though FilteredWorksetCollector should yield Workset objects
)

# --- Configuration ---
old_prefix = "Workset"
new_prefix = "WS_"

# --- Initialization ---
renamed_count = 0
skipped_count = 0
error_count = 0
processed_count = 0

# --- Check if worksharing is enabled ---
if not doc.IsWorkshared:
    print("# Info: Project is not workshared. No worksets to rename.")
else:
    try:
        # Get the WorksetTable - needed for the RenameWorkset static method
        # workset_table = doc.GetWorksetTable() # Not strictly needed if using static method

        # Collect only user-created worksets
        collector = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
        # Ensure we have Workset objects, although OfKind should guarantee this
        user_worksets = [ws for ws in collector if isinstance(ws, Workset)]
        processed_count = len(user_worksets)

        if not user_worksets:
             print("# Info: No user-created worksets found to process.")
        else:
            # print("# Found {} user worksets. Checking for renaming...".format(processed_count)) # Optional debug info

            for workset in user_worksets:
                current_name = "Unknown" # Default in case of error getting name
                workset_id_int = -1 # Default in case of error getting ID
                try:
                    current_name = workset.Name
                    workset_id = workset.Id # Get the WorksetId object
                    workset_id_int = workset_id.IntegerValue # Get integer value for logging

                    # Check if name is not null/empty and starts with the old prefix (case-sensitive)
                    if current_name and current_name.startswith(old_prefix):
                        # Construct the new name by replacing the prefix
                        rest_of_name = current_name[len(old_prefix):]
                        new_name = new_prefix + rest_of_name

                        # Only proceed if the name actually changes
                        if current_name != new_name:
                            try:
                                # Attempt to rename using the static method WorksetTable.RenameWorkset
                                WorksetTable.RenameWorkset(doc, workset_id, new_name)
                                renamed_count += 1
                                # print("# Renamed Workset '{}' to '{}' (ID: {})".format(current_name, new_name, workset_id_int)) # Debug
                            except System.ArgumentException as arg_ex:
                                error_count += 1
                                print("# Error renaming Workset '{}' (ID: {}): New name '{}' might already exist or be invalid. Details: {}".format(current_name, workset_id_int, new_name, arg_ex.Message))
                            except SystemException as rename_ex:
                                error_count += 1
                                print("# Error renaming Workset '{}' (ID: {}): {}".format(current_name, workset_id_int, rename_ex.Message))
                        else:
                            # This case might happen if old_prefix is empty or rest_of_name is empty leading to identical names
                            skipped_count += 1
                            # print("# Skipped Workset '{}' (ID: {}): New name is identical to old name.".format(current_name, workset_id_int)) # Debug
                    else:
                        # Name doesn't start with the prefix or is null/empty
                        skipped_count += 1
                        # print("# Skipped Workset '{}' (ID: {}): Does not start with '{}'.".format(current_name, workset_id_int, old_prefix)) # Debug

                except SystemException as proc_ex:
                    # Log error encountered while processing a specific workset (e.g., getting Name or Id)
                    error_count += 1
                    # Try to get ID again just for the error message, might fail again
                    try: workset_id_int = workset.Id.IntegerValue
                    except: pass
                    print("# Error processing Workset (Name: '{}', ID: {}): {}".format(current_name, workset_id_int, proc_ex.Message))

            # --- Final Summary --- (Optional: uncomment if needed, but keep commented per instructions)
            # print("# --- Workset Renaming Summary ---")
            # print("# Total user worksets checked: {}".format(processed_count))
            # print("# Successfully renamed: {}".format(renamed_count))
            # print("# Skipped (prefix mismatch or no change): {}".format(skipped_count))
            # print("# Errors encountered: {}".format(error_count))
            # if error_count > 0:
            #    print("# Review errors printed above for details.")

    except SystemException as general_ex:
        # Error accessing workset table or during collection phase
        print("# Error accessing workset information: {}".format(general_ex.Message))
        # No reliable counts available if collection failed.