# Purpose: This script updates the 'Asset ID' parameter of furniture elements in Revit based on room number and mark, using data from an input string.

﻿import clr
# Ensure Architecture classes are loaded if needed
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Assembly might be missing or blocked. Original error: {{}}".format(e))

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    Parameter,
    BuiltInParameter,
    LocationPoint,
    XYZ
)
import System

# Input data string: RoomNumber,Mark,AssetID
input_data = """RoomNumber,Mark,AssetID
101,Desk-01,F-ASSET-001
101,Chair-01,F-ASSET-002
102,Table-01,F-ASSET-003"""

# --- Configuration ---
# Define the exact name of the Asset ID parameter on the furniture elements
# IMPORTANT: This must match the parameter name in your Revit project EXACTLY (case-sensitive).
asset_id_param_name = "Asset ID"

# --- Data Parsing ---
# Create a dictionary to store (RoomNumber, Mark) -> AssetID mapping
asset_lookup = {}
lines = input_data.strip().split('\n')
# Skip header line (lines[0])
for line in lines[1:]:
    parts = line.strip().split(',')
    if len(parts) == 3:
        room_number = parts[0].strip()
        mark = parts[1].strip()
        asset_id = parts[2].strip()
        if room_number and mark: # Ensure room number and mark are not empty
            asset_lookup[(room_number, mark)] = asset_id

# --- Furniture Collection and Update ---
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType()

updated_count = 0
skipped_no_match = 0
skipped_no_room_info = 0
skipped_no_mark = 0
skipped_no_asset_param = 0
error_count = 0

for inst in collector:
    if not isinstance(inst, FamilyInstance):
        continue

    current_room_number = None
    current_mark = None
    found_room = None

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
            skipped_no_mark += 1
            continue # Skip if no Mark parameter or no value

        # --- Get Room Information ---
        # Method 1: Use FamilyInstance.Room property
        if hasattr(inst, 'Room') and inst.Room is not None:
            found_room = inst.Room
        # Method 2: Use GetRoomAtPoint as fallback
        else:
            location = inst.Location
            if location and isinstance(location, LocationPoint):
                point = location.Point
                if point:
                    found_room = doc.GetRoomAtPoint(point)

        # --- Get Room Number from the found room ---
        if found_room and isinstance(found_room, Room):
            number_param = found_room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if number_param and number_param.HasValue:
                current_room_number = number_param.AsString()
                if current_room_number:
                    current_room_number = current_room_number.strip()
                else:
                     # Room exists but number is empty
                     skipped_no_room_info += 1
                     continue # Skip if room number is empty
            else:
                # Room exists but has no Number parameter or value
                skipped_no_room_info += 1
                continue # Skip if room number cannot be determined
        else:
            # Furniture not in a room or location is invalid
            skipped_no_room_info += 1
            continue # Skip if no room information

        # --- Lookup Asset ID and Update ---
        if current_room_number and current_mark:
            lookup_key = (current_room_number, current_mark)
            if lookup_key in asset_lookup:
                target_asset_id = asset_lookup[lookup_key]

                # --- Find and Update Asset ID Parameter ---
                asset_param = inst.LookupParameter(asset_id_param_name)
                if asset_param and not asset_param.IsReadOnly:
                    try:
                        # Use Set(string) for text-based parameters
                        asset_param.Set(target_asset_id)
                        updated_count += 1
                    except Exception as set_ex:
                        # print("# ERROR: Failed to set Asset ID for Element {{}} (Room: {{}}, Mark: {{}}): {{}}".format(inst.Id, current_room_number, current_mark, str(set_ex)))
                        error_count += 1
                else:
                    # Asset ID parameter not found or is read-only
                    skipped_no_asset_param += 1
                    # print("# INFO: '{{}}' parameter not found or read-only for Element {{}} (Room: {{}}, Mark: {{}})".format(asset_id_param_name, inst.Id, current_room_number, current_mark))
            else:
                # Room/Mark combination not found in the input data
                skipped_no_match += 1
        else:
            # This case should theoretically be caught by earlier continues, but included for robustness
            error_count += 1 # Treat as error if checks failed

    except Exception as e:
        error_count += 1
        try:
            # Try to log the specific element ID causing the error
            print("# ERROR: Failed to process Furniture Instance ID {{}}: {{}}".format(inst.Id.ToString(), str(e)))
        except:
            print("# ERROR: Failed to process a Furniture element: {{}}".format(str(e)))


# Optional: Print summary to console (will appear in RPS/pyRevit output)
# print("--- Furniture Asset ID Update Summary ---")
# print("Furniture instances updated: {{}}".format(updated_count))
# print("Skipped (Room/Mark not in input data): {{}}".format(skipped_no_match))
# print("Skipped (No Room Info/Number): {{}}".format(skipped_no_room_info))
# print("Skipped (No Mark): {{}}".format(skipped_no_mark))
# print("Skipped ('{{}}' param issue): {{}}".format(asset_id_param_name, skipped_no_asset_param))
# print("Errors encountered: {{}}".format(error_count))
# if not asset_lookup:
#    print("# Warning: Input data was empty or failed to parse.")