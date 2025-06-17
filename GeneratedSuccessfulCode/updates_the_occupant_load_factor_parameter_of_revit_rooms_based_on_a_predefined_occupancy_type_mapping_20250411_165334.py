# Purpose: This script updates the 'Occupant Load Factor' parameter of Revit rooms based on a predefined occupancy type mapping.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    Parameter
)
# Import Room class
try:
    # RevitAPIArchitecture may already be loaded in some environments
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        # If loading Room fails, stop the script as it cannot proceed
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Error: {}".format(e))

# Define the conversion factor from square meters to square feet
SQM_TO_SQFT_FACTOR = 1.0 / (0.3048 * 0.3048) # Approx 10.7639

# --- Define Occupancy to Load Factor Mapping ---
# Map Occupancy Type (string) to Occupant Load Factor (sqm/person)
# Add or modify entries as needed for your project standards
occupancy_factor_map_sqm = {
    # Key: Value of 'Occupancy' parameter (case-sensitive)
    # Value: Occupant Load Factor in square meters per person
    "Office": 10.0,
    "Assembly": 1.4,
    "Corridor": 5.0,
    "Classroom": 1.9,
    "Residential": 18.6,
    "Storage": 27.9
    # Add other occupancy types relevant to your project
}

# Convert the map values to Revit's internal units (square feet per person)
occupancy_factor_map_internal = {
    occupancy_type: factor_sqm * SQM_TO_SQFT_FACTOR
    for occupancy_type, factor_sqm in occupancy_factor_map_sqm.items()
}

# Collect all Room elements in the project
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Filter for elements that are actual Room instances
rooms_to_process = [el for el in collector if isinstance(el, Room)]

updated_count = 0
skipped_no_occupancy_param = 0
skipped_no_olf_param = 0
skipped_unmapped_occupancy = 0
error_count = 0

# Iterate through the collected rooms
for room in rooms_to_process:
    try:
        # Get the 'Occupancy' parameter (BuiltInParameter.ROOM_OCCUPANCY)
        occupancy_param = room.get_Parameter(BuiltInParameter.ROOM_OCCUPANCY)

        if not occupancy_param or not occupancy_param.HasValue:
            # print("# INFO: Room ID {} skipped - 'Occupancy' parameter missing or empty.".format(room.Id))
            skipped_no_occupancy_param += 1
            continue

        occupancy_value = occupancy_param.AsString()
        if not occupancy_value: # Check for empty string after AsString()
            # print("# INFO: Room ID {} skipped - 'Occupancy' parameter value is empty.".format(room.Id))
            skipped_no_occupancy_param += 1
            continue

        # Check if the occupancy value exists in our mapping
        if occupancy_value in occupancy_factor_map_internal:
            target_olf_value = occupancy_factor_map_internal[occupancy_value]

            # Get the 'Occupant Load Factor' parameter (BuiltInParameter.ROOM_OCCUPANT_LOAD_FACTOR)
            olf_param = room.get_Parameter(BuiltInParameter.ROOM_OCCUPANT_LOAD_FACTOR)

            if olf_param and not olf_param.IsReadOnly:
                # Check if the current value needs updating (optional, avoids unnecessary sets)
                current_olf_value = olf_param.AsDouble()
                # Use a small tolerance for float comparison
                tolerance = 1e-6
                if abs(current_olf_value - target_olf_value) > tolerance:
                    # Set the Occupant Load Factor (Transaction handled externally)
                    olf_param.Set(target_olf_value)
                    updated_count += 1
                # else: # Already has the correct value
                    # pass
            else:
                # print("# INFO: Room ID {} skipped - 'Occupant Load Factor' parameter missing or read-only.".format(room.Id))
                skipped_no_olf_param += 1
        else:
            # print("# INFO: Room ID {} skipped - Occupancy type '{}' not found in mapping.".format(room.Id, occupancy_value))
            skipped_unmapped_occupancy += 1

    except Exception as e:
        # Log errors encountered while processing a specific room (optional)
        # print("# ERROR processing Room ID {}: {}".format(room.Id, e))
        error_count += 1

# Optional: Print summary (commented out as per standard format)
# print("--- Occupant Load Factor Update Summary ---")
# print("Rooms updated: {}".format(updated_count))
# print("Skipped (No/Empty Occupancy Param): {}".format(skipped_no_occupancy_param))
# print("Skipped (Unmapped Occupancy Type): {}".format(skipped_unmapped_occupancy))
# print("Skipped (No/Read-Only OLF Param): {}".format(skipped_no_olf_param))
# print("Errors encountered: {}".format(error_count))
# print("Total Rooms processed: {}".format(len(rooms_to_process)))