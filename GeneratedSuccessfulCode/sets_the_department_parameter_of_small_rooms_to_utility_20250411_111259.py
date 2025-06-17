# Purpose: This script sets the 'Department' parameter of small rooms to 'Utility'.

# Purpose: This script sets the "Department" parameter of rooms smaller than a specified area to "Utility".

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Parameter,
    BuiltInParameter,
    SpatialElement,
    UnitUtils,
    # DisplayUnitType # Not strictly needed for conversion if using direct factor
    ForgeTypeId # Required for Revit 2022+ UnitUtils.ConvertToInternalUnits
)
# Attempt to import Room without explicit AddReference for RevitAPIArchitecture
# Assuming the execution environment might pre-load it or handle it differently
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    # If the above fails, try adding the reference explicitly again,
    # perhaps the initial error was transient or environment-specific.
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Assembly might be missing or blocked. Original error: {}".format(e))


# Define the area threshold in square meters
area_threshold_sq_meters = 5.0

# Define the value to set for the Department parameter
new_department_value = "Utility"

# Get Revit's internal unit type for area
# Using DisplayUnitType.DUT_SQUARE_FEET assumes internal units are sq ft, which is common but not guaranteed.
# A more robust way for newer APIs (2021+) is to check doc.GetUnits().
# For compatibility, we'll stick to the direct conversion factor, assuming sq ft.
# If using Revit 2021+, use UnitUtils.ConvertToInternalUnits more robustly.
sq_meters_to_sq_feet_factor = 1 / (0.3048 * 0.3048) # More precise factor
area_threshold_internal = area_threshold_sq_meters * sq_meters_to_sq_feet_factor

# Alternative using UnitUtils (Requires Revit 2021+ and knowledge of Area unit spec)
# try:
#     area_spec = ForgeTypeId("autodesk.spec.aec:area-2.0.0") # Example Area Spec Id
#     area_threshold_internal = UnitUtils.ConvertToInternalUnits(area_threshold_sq_meters, area_spec)
# except AttributeError: # Handle cases where ForgeTypeId or newer UnitUtils methods aren't available
#     # Fallback to manual conversion
#     sq_meters_to_sq_feet_factor = 1 / (0.3048 * 0.3048)
#     area_threshold_internal = area_threshold_sq_meters * sq_meters_to_sq_feet_factor


# Collect all Room elements that are placed (have area > 0)
# 'doc' is assumed to be pre-defined
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Filter for placed rooms (Area > small tolerance)
# Note: Some environments might require iterating before filtering by parameter
placed_rooms = [el for el in collector if isinstance(el, Room) and el.Area > 1e-6]

# Counter for modified rooms (optional)
modified_count = 0

# Iterate through the placed rooms
for room in placed_rooms:
    try:
        room_area_internal = room.Area
        # Check if the area is below the threshold
        if room_area_internal < area_threshold_internal:
            # Find the 'Department' parameter
            department_param = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)

            # Check if the parameter exists and is not read-only
            if department_param and not department_param.IsReadOnly:
                # Check if the current value is different before setting
                current_value = department_param.AsString()
                if current_value != new_department_value:
                    # Set the parameter value
                    # Assuming a transaction is handled outside this script
                    department_param.Set(new_department_value)
                    modified_count += 1
            # else:
                # Optional: Log if parameter not found or read-only
                # print("# Parameter 'Department' not found or read-only for Room ID: {}".format(room.Id))
                # pass

    except Exception as e:
        # Log errors during processing individual rooms (optional)
        # import traceback
        # print("# Error processing Room ID {}: {}".format(room.Id, e))
        # print(traceback.format_exc())
        pass # Continue to the next room

# Optional: Print a summary message (commented out for clarity, use if needed)
# print("# Finished processing. Modified {} rooms.".format(modified_count))