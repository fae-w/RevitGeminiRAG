# Purpose: This script renames views placed on sheets in Revit by adding a specified suffix.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, View, ElementId, Element
import System # For Exception handling

# --- Configuration ---
suffix_to_add = " (On Sheet)"

# --- Initialization ---
all_placed_view_ids = set() # Using a set to store unique view IDs
processed_count = 0
renamed_count = 0
already_named_count = 0
skipped_not_view_count = 0
failed_count = 0
errors = []

# --- Step 1: Collect all ViewSheets ---
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
all_sheets = [sheet for sheet in sheet_collector if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet)]

if not all_sheets:
    print("# No ViewSheet elements found in the project.")
else:
    print("# Found {} sheets. Collecting views placed on them...".format(len(all_sheets)))

    # --- Step 2: Collect IDs of all views placed on any sheet ---
    for sheet in all_sheets:
        try:
            # GetAllPlacedViews returns ISet<ElementId> containing View Ids (excluding schedules)
            placed_view_ids_on_sheet = sheet.GetAllPlacedViews()
            if placed_view_ids_on_sheet:
                # Update the master set with IDs from this sheet
                # In IronPython, directly iterating over the ISet<ElementId> usually works
                for view_id in placed_view_ids_on_sheet:
                     all_placed_view_ids.add(view_id)
        except Exception as e:
            errors.append("# Error getting placed views for sheet '{}' (ID: {}): {}".format(sheet.Name, sheet.Id, e))
            print("# Warning: Could not process sheet '{}' (ID: {}). Error: {}".format(sheet.Name, sheet.Id, e))


    # --- Step 3: Iterate through unique view IDs and attempt rename ---
    total_unique_views = len(all_placed_view_ids)
    if total_unique_views == 0:
        print("# No views found placed on any sheets.")
    else:
        print("# Found {} unique views placed on sheets. Attempting to rename...".format(total_unique_views))

        for view_id in all_placed_view_ids:
            processed_count += 1
            view_element = None
            current_name = None

            try:
                view_element = doc.GetElement(view_id)

                # Check if the element is a valid View
                if not view_element or not isinstance(view_element, View):
                    # This might happen if an ID points to something unexpected, though GetAllPlacedViews should return Views.
                    skipped_not_view_count += 1
                    errors.append("# Skipped: Element ID {} is not a valid View.".format(view_id))
                    continue

                # Get current name
                try:
                    current_name = view_element.Name
                except Exception as name_ex:
                    failed_count += 1
                    errors.append("# Error getting name for View ID {}: {}".format(view_id, name_ex))
                    continue # Skip if we can't even get the name

                # Check if already has the suffix
                if current_name.endswith(suffix_to_add):
                    already_named_count += 1
                    continue # Skip, already named correctly

                # Construct new name
                new_name = current_name + suffix_to_add

                # Attempt rename
                try:
                    view_element.Name = new_name
                    renamed_count += 1
                    # print("# Renamed View '{}' to '{}'".format(current_name, new_name)) # Optional debug message
                except System.ArgumentException as arg_ex:
                    # Handle specific errors like duplicate names
                    failed_count += 1
                    error_msg = "# Rename Error: View '{}' (ID: {}) to '{}': {}. (Likely duplicate name)".format(current_name, view_id, new_name, arg_ex.Message)
                    errors.append(error_msg)
                    print(error_msg) # Print immediately
                except Exception as rename_ex:
                    failed_count += 1
                    error_msg = "# Rename Error: View '{}' (ID: {}) to '{}': {}".format(current_name, view_id, new_name, rename_ex)
                    errors.append(error_msg)
                    print(error_msg) # Print immediately

            except Exception as outer_ex:
                 # Catch errors during element retrieval or initial checks
                 failed_count += 1
                 error_msg = "# Unexpected Error processing View ID {}: {}".format(view_id, outer_ex)
                 errors.append(error_msg)
                 print(error_msg) # Print immediately


        # --- Final Summary ---
        print("\n# --- View Renaming Summary ---")
        print("# Total unique views found on sheets: {}".format(total_unique_views))
        print("# Views successfully renamed: {}".format(renamed_count))
        print("# Views already had the suffix '{}': {}".format(suffix_to_add, already_named_count))
        print("# Views skipped (Element ID was not a valid View): {}".format(skipped_not_view_count))
        print("# Views failed during rename attempt (e.g., duplicates, errors): {}".format(failed_count))

        # if errors:
        #     print("\n# --- Encountered Errors ---")
        #     for error in errors:
        #         print(error)