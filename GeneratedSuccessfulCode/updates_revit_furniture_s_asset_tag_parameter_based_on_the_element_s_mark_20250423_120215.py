# Purpose: This script updates Revit furniture's asset tag parameter based on the element's mark.

﻿import clr
# Ensure Architecture classes are loaded if needed (though not strictly required for this specific task)
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
    except Exception:
        # Pass silently if assembly is not found, as Room is not directly used
        pass

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    Parameter,
    BuiltInParameter
)
import System

# Input data string: Mark,AssetTag
# Rows with blank AssetTag will be skipped.
input_data = """Mark,AssetTag
CH-101,A001
CH-102,
TB-101,A003
Desk-01,A004
Chair-01,""" # Added more examples including a trailing blank

# --- Configuration ---
# Define the exact name of the Asset Tag parameter on the furniture elements
# IMPORTANT: This must match the parameter name in your Revit project EXACTLY (case-sensitive).
asset_tag_param_name = "Asset Tag"

# --- Data Parsing ---
# Create a dictionary to store Mark -> AssetTag mapping
asset_lookup = {}
lines = input_data.strip().split('\n')
# Skip header line (lines[0])
for line in lines[1:]:
    parts = line.strip().split(',', 1) # Split only on the first comma
    if len(parts) == 2:
        mark = parts[0].strip()
        asset_tag = parts[1].strip()
        # CRITICAL: Skip rows where AssetTag is blank
        if mark and asset_tag: # Ensure mark is not empty and asset_tag is not empty
            asset_lookup[mark] = asset_tag
        # Else: Implicitly skip the row if mark or asset_tag is blank

# --- Furniture Collection and Update ---
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType()

updated_count = 0
skipped_no_match = 0
skipped_no_mark = 0
skipped_no_asset_param = 0
error_count = 0

for inst in collector:
    if not isinstance(inst, FamilyInstance):
        continue

    current_mark = None

    try:
        # --- Get Furniture Mark ---
        mark_param = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if mark_param and mark_param.HasValue:
            current_mark = mark_param.AsString()
            if current_mark:
                current_mark = current_mark.strip()
            else:
                skipped_no_mark += 1
                continue # Skip if Mark is empty/None
        else:
            # Check instance property as a fallback if parameter not found
            if hasattr(inst, 'Mark') and inst.Mark:
                 current_mark = inst.Mark
                 if current_mark:
                     current_mark = current_mark.strip()
                 else:
                     skipped_no_mark += 1
                     continue
            else:
                 skipped_no_mark += 1
                 continue # Skip if no Mark parameter or property

        # --- Lookup Asset Tag and Update ---
        if current_mark in asset_lookup:
            target_asset_tag = asset_lookup[current_mark]

            # --- Find and Update Asset Tag Parameter ---
            asset_param = inst.LookupParameter(asset_tag_param_name)
            if asset_param and not asset_param.IsReadOnly:
                try:
                    # Use Set(string) for text-based parameters
                    asset_param.Set(target_asset_tag)
                    updated_count += 1
                except Exception as set_ex:
                    # print("# ERROR: Failed to set '{}' for Element {} (Mark: {}): {}".format(asset_tag_param_name, inst.Id, current_mark, str(set_ex)))
                    error_count += 1
            else:
                # Asset Tag parameter not found or is read-only
                skipped_no_asset_param += 1
                # print("# INFO: '{}' parameter not found or read-only for Element {} (Mark: {})".format(asset_tag_param_name, inst.Id, current_mark))
        else:
            # Mark not found in the input data (or was skipped due to blank AssetTag)
            skipped_no_match += 1

    except Exception as e:
        error_count += 1
        try:
            # Try to log the specific element ID causing the error
            print("# ERROR: Failed to process Furniture Instance ID {}: {}".format(inst.Id.ToString(), str(e)))
        except:
            print("# ERROR: Failed to process a Furniture element: {}".format(str(e)))


# Optional: Print summary to console (will appear in RPS/pyRevit output)
# print("--- Furniture Asset Tag Update Summary ---")
# print("Furniture instances updated: {}".format(updated_count))
# print("Skipped (Mark not in input data or AssetTag was blank): {}".format(skipped_no_match))
# print("Skipped (No Mark found on element): {}".format(skipped_no_mark))
# print("Skipped ('{}' param issue): {}".format(asset_tag_param_name, skipped_no_asset_param))
# print("Errors encountered: {}".format(error_count))
# if not asset_lookup:
#    print("# Warning: Input data was empty, failed to parse, or all AssetTags were blank.")