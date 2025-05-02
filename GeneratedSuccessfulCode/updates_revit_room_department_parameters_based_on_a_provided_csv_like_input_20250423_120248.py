# Purpose: This script updates Revit room department parameters based on a provided CSV-like input.

﻿import clr
# Try importing Room from the standard location
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    # Fallback if RevitAPIArchitecture needs explicit loading
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        # Provide a more informative error if the import fails completely
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Assembly might be missing or blocked. Original error: {}".format(e))

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter

# Input data string: Number,Department
input_data = """Number,Department
301,Sales
302,Marketing
303,HR"""

# --- Data Parsing ---
# Create a dictionary to store Room Number -> Target Department mapping
room_department_update_map = {}
lines = input_data.strip().split('\n')
# Skip header line (lines[0])
for line in lines[1:]:
    parts = line.split(',', 1) # Split only on the first comma
    if len(parts) == 2:
        number = parts[0].strip()
        department = parts[1].strip()
        if number: # Ensure number is not empty
            room_department_update_map[number] = department

# --- Room Collection and Update ---
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

updated_count = 0
skipped_already_set = 0
skipped_not_found = 0
skipped_no_param = 0
error_count = 0

for room in collector:
    # Ensure it's a Room element and it's placed (has a location)
    if not isinstance(room, Room) or room.Location is None:
        continue

    try:
        # --- Get Room Number ---
        number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
        room_number = None
        if number_param and number_param.HasValue:
            room_number = number_param.AsString()
            if room_number:
                 room_number = room_number.strip() # Clean whitespace

        # --- Check if this room number is in our update map ---
        if room_number and room_number in room_department_update_map:
            target_department = room_department_update_map[room_number]

            # --- Get Department Parameter ---
            department_param = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)

            if department_param and not department_param.IsReadOnly:
                # --- Check if Current Department is Empty ---
                current_department = department_param.AsString()
                # An empty department parameter might return None or an empty string ""
                if current_department is None or current_department == "" or not current_department.strip():
                    # --- Update Parameter ---
                    department_param.Set(target_department)
                    updated_count += 1
                else:
                    # Department is already set, skip as per requirement
                    skipped_already_set += 1
            else:
                # Department parameter not found or read-only
                skipped_no_param += 1
                # print("# INFO: Department parameter not found or read-only for room number: {}".format(room_number))
        elif room_number:
             # Room number exists but is not in the input data map
             skipped_not_found +=1 # Count rooms processed but not targeted for update

    except Exception as e:
        error_count += 1
        try:
            # Try to log the specific room ID causing the error
            print("# ERROR: Failed to process Room ID {}: {}".format(room.Id.ToString(), str(e)))
        except:
            print("# ERROR: Failed to process a Room element: {}".format(str(e)))


# Optional: Print summary to console (will appear in RPS/pyRevit output)
# print("--- Room Department Update Summary (Conditional) ---")
# print("Rooms updated (was empty): {}".format(updated_count))
# print("Rooms skipped (department already set): {}".format(skipped_already_set))
# print("Rooms skipped (number not in input list): {}".format(skipped_not_found))
# print("Rooms skipped (Department param issue or unplaced): {}".format(skipped_no_param + (collector.GetElementCount() - updated_count - skipped_already_set - skipped_not_found - error_count))) # Approximation
# print("Errors encountered: {}".format(error_count))
# if not room_department_update_map:
#    print("# Warning: Input data was empty or failed to parse.")