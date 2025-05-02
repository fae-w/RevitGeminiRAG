# Purpose: This script updates the department parameter of Revit rooms based on a predefined name mapping.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter
# Attempt to import Room class
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    # Fallback if RevitAPIArchitecture is not automatically referenced
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Assembly might be missing or blocked. Original error: {}".format(e))

# --- Room Name to Department Mapping ---
# This dictionary stores the target department for each specific room name.
# Room names in the model must match these keys exactly (case-sensitive, after stripping whitespace)
# to be updated.
room_department_mapping = {
    "Stair S1": "Vertical Circulation",
    "Stair S3": "Vertical Circulation",
    "Stair S2": "Vertical Circulation",
    "Elevator E1": "Vertical Circulation",
    "Elevator E2": "Vertical Circulation",
    "Café": "Front of House",
    "Café Kitchen": "Front of House",
    "Outdoor Covered Dining": "Front of House",
    "Pocket Park": "Front of House",
    "Commercial/Retail": "Front of House", # Note: Multiple entries for this name, last one usually wins in dict creation, but here the department is the same. Be mindful if departments differed.
    "Residential Lobby": "Front of House",
    "Utility": "MEP", # Note: Multiple entries for this name with different departments. This mapping will set 'MEP' for rooms named "Utility".
    "Corridor": "Circulation", # Note: Multiple entries for this name, department is the same.
    "Live/Work Unit": "Front of House", # Note: Multiple entries, department is the same.
    "Studio Unit": "Front of House", # Note: Multiple entries, department is the same.
    "Two Story Studio Unit": "Front of House", # Note: Multiple entries, department is the same.
    "Office Unit": "Front of House", # Note: Multiple entries, department is the same.
    "Green Roof": "Front of House", # Note: Multiple entries, department is the same.
    "Parking Garage": "MEP",
    "Machine RM": "MEP", # Note: Multiple entries, department is the same.
    "Storage": "MEP", # Note: Multiple entries for this name with different departments. This mapping will set 'MEP' for rooms named "Storage".
    "Live/Work Loft Unit": "Front of House",
    "Mezzanine Dining": "Front of House",
    "Bandstand": "Front of House",
    "Private Patio": "Front of House"
}

# --- Collect Rooms and Update Department Parameter ---
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

updated_count = 0
skipped_count = 0
error_count = 0

for room in collector:
    if not isinstance(room, Room):
        continue

    # Skip unplaced rooms as they might not have reliable parameters
    if room.Location is None:
        skipped_count += 1
        continue

    try:
        # --- Get Room Name ---
        room_name = None
        name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
        if name_param and name_param.HasValue:
            name_val = name_param.AsString()
            if name_val and name_val.strip(): # Check if not None and not empty/whitespace
                room_name = name_val.strip()

        # Fallback to Element.Name if parameter is missing or empty
        if not room_name and room.Name:
             name_val = room.Name
             if name_val and name_val.strip():
                  room_name = name_val.strip()

        # If no valid name found, skip this room
        if not room_name:
            skipped_count += 1
            continue

        # --- Check if this room name is in our mapping ---
        if room_name in room_department_mapping:
            target_department = room_department_mapping[room_name]

            # --- Get Department Parameter ---
            department_param = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)

            # --- Update Parameter if possible and necessary ---
            if department_param and not department_param.IsReadOnly:
                current_department = department_param.AsString()
                # Update only if the value is different
                if current_department != target_department:
                    department_param.Set(target_department)
                    updated_count += 1
                # else: # Room already has the correct department
                     # skipped_count += 1 # Optionally count rooms that already match
            else:
                # Parameter not found or read-only
                skipped_count += 1
                # print("# INFO: Department parameter not found or read-only for room: {}".format(room_name))

        else:
            # Room name not found in the mapping
            skipped_count += 1
            # print("# INFO: Room name '{}' (ID: {}) not found in mapping, skipping.".format(room_name, room.Id))

    except Exception as e:
        error_count += 1
        try:
            # Try to log the specific room ID causing the error
            print("# ERROR: Failed to process Room ID {}: {}".format(room.Id.ToString(), str(e)))
        except:
            print("# ERROR: Failed to process a Room element: {}".format(str(e)))


# Optional: Print summary to console (will appear in RPS/pyRevit output)
# print("--- Room Department Update Summary ---")
# print("Rooms updated: {}".format(updated_count))
# print("Rooms skipped (unplaced, no name, no mapping, already correct, or read-only param): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))