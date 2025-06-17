# Purpose: This script renames Revit legend views by adding a specified prefix.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewType,
    Element # Base class for elements
)
import System # For Exception handling, particularly ArgumentException

# --- Configuration ---
prefix = "LEG_"

# --- Initialization ---
renamed_count = 0
skipped_count = 0
error_count = 0

# --- Step 1: Collect Legend Views ---
# Assumption: The user meant to rename Legend *Views*, as Legend *Components*
# within views do not have a directly settable 'Name' property in the same way.
collector = FilteredElementCollector(doc).OfClass(View)

# Filter for Legend views that are not templates
legend_views = [v for v in collector if v.ViewType == ViewType.Legend and not v.IsTemplate]

# --- Step 2: Iterate and Rename Legend Views ---
for view in legend_views:
    original_name = "" # Initialize for error handling context
    try:
        original_name = view.Name

        # Check if the name already starts with the desired prefix (case-sensitive)
        if not original_name.startswith(prefix):
            # Construct the new name
            new_name = prefix + original_name

            try:
                # Attempt to rename the view
                view.Name = new_name
                renamed_count += 1
                # print("# Renamed view '{{}}' to '{{}}'".format(original_name, new_name)) # Debug comment
            except System.ArgumentException as arg_ex:
                # Handle potential errors like duplicate names
                error_count += 1
                print("# Error renaming Legend View '{{}}' (ID: {{}}): {{}}. New name '{{}}' might already exist.".format(original_name, view.Id, arg_ex.Message, new_name))
            except Exception as e_rename:
                # Handle other potential errors during renaming
                error_count += 1
                print("# Unexpected error renaming Legend View '{{}}' (ID: {{}}): {{}}".format(original_name, view.Id, e_rename))
        else:
            # Name already starts with the prefix, skip renaming
            skipped_count += 1
            # print("# Skipping Legend View '{{}}' as it already starts with '{{}}'".format(original_name, prefix)) # Debug comment

    except Exception as e_outer:
        # Handle potential errors accessing view properties like Name
        error_count += 1
        print("# Error processing Legend View (ID: {{}}), original name may be unknown: {{}}".format(view.Id, e_outer))

# Optional: Print summary to RevitPythonShell output (comment out if not desired)
# print("--- Legend View Renaming Summary ---")
# print("Successfully renamed: {{}}".format(renamed_count))
# print("Skipped (already prefixed): {{}}".format(skipped_count))
# print("Errors encountered: {{}}".format(error_count))
# print("Total Legend Views processed: {{}}".format(len(legend_views)))