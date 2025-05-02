# Purpose: This script renames specific Revit 3D views based on a defined naming pattern.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    View3D, # Specifically for checking if it's a 3D view
    ElementId # Good practice
)
import System # For Exception handling
import re # For regular expressions

# --- Configuration ---
# Regular expression to find views named exactly "3D View {n}" where n is one or more digits.
# Assumes the actual view names are like "3D View {1}", "3D View {12}" etc.
# ^ asserts position at start of the string.
# \$ asserts position at the end of the string.
# \{ and \} match literal braces.
# (\d+) matches one or more digits and captures them in group 1.
pattern = re.compile(r"^3D View \{(\d+)\}$")

# --- Initialization ---
renamed_count = 0
processed_3d_view_count = 0
skipped_no_match_count = 0
error_count = 0
errors = []

# --- Step 1: Collect all Views ---
collector = FilteredElementCollector(doc).OfClass(View)

# --- Step 2: Iterate and Rename Matching 3D Views ---
for view in collector:
    # Only process actual View3D elements
    if isinstance(view, View3D):
        processed_3d_view_count += 1
        original_name = "Unknown" # Default for error messages
        try:
            original_name = view.Name

            # --- Step 3: Check if the name matches the pattern ---
            match = pattern.match(original_name)

            if match:
                # --- Step 4: Extract the number and construct the new name ---
                number_str = match.group(1) # Get the captured digits
                new_name = "User 3D - {0}".format(number_str) # Format the new name # Escaped braces

                # --- Step 5: Check if renaming is necessary (should always be if matched) ---
                if new_name != original_name:
                    # print("# Attempting rename: Original='{0}', New='{1}'".format(original_name, new_name)) # Debug # Escaped braces
                    try:
                        # --- Step 6: Attempt to rename the view ---
                        view.Name = new_name
                        renamed_count += 1
                        # print("# Renamed view '{0}' to '{1}' (ID: {2})".format(original_name, new_name, view.Id)) # Debug # Escaped braces
                    except System.ArgumentException as arg_ex:
                        # Handle potential errors like duplicate names
                        error_count += 1
                        errors.append("# Error renaming view '{0}' (ID: {1}) to '{2}': {3}. New name might already exist.".format(original_name, view.Id, new_name, arg_ex.Message)) # Escaped braces
                    except Exception as e:
                        # Handle other potential errors during renaming
                        error_count += 1
                        errors.append("# Error renaming view '{0}' (ID: {1}) to '{2}': {3}".format(original_name, view.Id, new_name, e)) # Escaped braces
                else:
                     # This case shouldn't happen with this specific pattern and replacement, but included for completeness
                     skipped_no_match_count += 1 # Count as skipped if somehow the name didn't change
            else:
                # The view name does not match the required pattern
                skipped_no_match_count += 1
                # print("# Skipping view '{0}' (ID: {1}): Name does not match pattern.".format(original_name, view.Id)) # Debug # Escaped braces

        except Exception as outer_ex:
            # Handle unexpected errors during processing of a specific view
            error_count += 1
            errors.append("# Unexpected error processing view '{0}' (ID: {1}): {2}".format(original_name, view.Id, outer_ex)) # Escaped braces
    # else: # Optional: Track non-3D views skipped
        # print("# Skipping element {0} - Not a 3D View".format(view.Id)) # Debug # Escaped braces


# --- Optional: Print summary and errors (comment out if not desired) ---
# print("\n# --- View Renaming Summary ---")
# print("# Total 3D Views processed: {0}".format(processed_3d_view_count)) # Escaped braces
# print("# Successfully renamed: {0}".format(renamed_count)) # Escaped braces
# print("# Skipped (name did not match pattern): {0}".format(skipped_no_match_count)) # Escaped braces
# print("# Errors encountered: {0}".format(error_count)) # Escaped braces
# if errors:
#   print("# --- Errors ---")
#   for err in errors:
#       print(err)