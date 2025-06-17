# Purpose: This script renames Revit parameter filters by replacing a specified prefix.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ParameterFilterElement

# --- Configuration ---
old_prefix = "Filter-"
new_prefix = "VF_"
# --- End Configuration ---

renamed_count = 0
skipped_count = 0
error_count = 0

# Find all ParameterFilterElement instances in the document
collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)

# Iterate through the filters
for filter_element in collector:
    if not isinstance(filter_element, ParameterFilterElement):
        continue # Should not happen with OfClass filter, but good practice

    try:
        current_name = filter_element.Name
    except Exception as e:
        # print("# Error getting name for filter ID {}: {}".format(filter_element.Id.IntegerValue, e)) # Optional debug
        error_count += 1
        continue

    # Check if the current name starts with the old prefix
    if current_name and current_name.startswith(old_prefix):
        # Construct the new name
        new_name = new_prefix + current_name[len(old_prefix):]

        # Check if the new name is different from the old name
        if new_name == current_name:
            # print("# Filter '{}' already has the desired prefix structure.".format(current_name)) # Optional info
            continue

        # Check if the proposed new name is unique
        if ParameterFilterElement.IsNameUnique(doc, new_name):
            try:
                # Rename the filter (Transaction is handled externally)
                filter_element.Name = new_name
                renamed_count += 1
                # print("# Renamed '{}' to '{}'".format(current_name, new_name)) # Optional info
            except Exception as rename_e:
                # print("# Error renaming filter '{}' to '{}': {}".format(current_name, new_name, rename_e)) # Optional debug
                skipped_count += 1
                error_count += 1
        else:
            # print("# Skipped renaming '{}' to '{}': New name already exists.".format(current_name, new_name)) # Optional info
            skipped_count += 1

# Optional: Print a summary to the console/log
# print("# --- Filter Renaming Summary ---")
# print("# Renamed: {}".format(renamed_count))
# print("# Skipped (name conflict): {}".format(skipped_count))
# print("# Errors: {}".format(error_count))
# if renamed_count == 0 and skipped_count == 0 and error_count == 0:
#     print("# No filters found starting with '{}' or requiring rename.".format(old_prefix))