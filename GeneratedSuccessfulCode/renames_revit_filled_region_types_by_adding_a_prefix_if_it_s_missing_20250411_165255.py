# Purpose: This script renames Revit Filled Region Types by adding a prefix if it's missing.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FilledRegionType,
    Element # Base class
)
import System # For Exception handling

# --- Configuration ---
prefix = "FR_"

# --- Initialization ---
renamed_count = 0
skipped_count = 0
error_count = 0

# --- Step 1: Collect FilledRegionType elements ---
# FilledRegionType elements are types, so we collect them directly using OfClass
collector = FilteredElementCollector(doc).OfClass(FilledRegionType)
filled_region_types = list(collector) # Convert iterator to list

# --- Step 2: Iterate and Rename FilledRegionType elements ---
for fr_type in filled_region_types:
    original_name = "" # Initialize for error context
    try:
        # FilledRegionType inherits Name property from ElementType
        original_name = fr_type.Name

        # Check if the name already starts with the desired prefix (case-sensitive)
        if not original_name.startswith(prefix):
            # Construct the new name
            new_name = prefix + original_name

            try:
                # Attempt to rename the FilledRegionType
                fr_type.Name = new_name
                renamed_count += 1
                # print("# Renamed FilledRegionType '{{}}' to '{{}}'".format(original_name, new_name)) # Debug comment
            except System.ArgumentException as arg_ex:
                # Handle potential errors like duplicate names
                error_count += 1
                print("# Error renaming FilledRegionType '{{}}' (ID: {{}}): {{}}. New name '{{}}' might already exist.".format(original_name, fr_type.Id, arg_ex.Message, new_name))
            except Exception as e_rename:
                # Handle other potential errors during renaming
                error_count += 1
                print("# Unexpected error renaming FilledRegionType '{{}}' (ID: {{}}): {{}}".format(original_name, fr_type.Id, e_rename))
        else:
            # Name already starts with the prefix, skip renaming
            skipped_count += 1
            # print("# Skipping FilledRegionType '{{}}' as it already starts with '{{}}'".format(original_name, prefix)) # Debug comment

    except Exception as e_outer:
        # Handle potential errors accessing properties like Name
        error_count += 1
        # Attempt to get ID even if name access failed
        try:
            element_id = fr_type.Id
        except:
            element_id = "Unknown ID"
        print("# Error processing FilledRegionType (ID: {{}}), original name may be '{{}}': {{}}".format(element_id, original_name, e_outer))

# Optional: Print summary to RevitPythonShell output (comment out if not desired)
# print("--- Filled Region Type Renaming Summary ---")
# print("Successfully renamed: {{{{}}}}".format(renamed_count))
# print("Skipped (already prefixed): {{{{}}}}".format(skipped_count))
# print("Errors encountered: {{{{}}}}".format(error_count))
# print("Total Filled Region Types processed: {{{{}}}}".format(len(filled_region_types)))