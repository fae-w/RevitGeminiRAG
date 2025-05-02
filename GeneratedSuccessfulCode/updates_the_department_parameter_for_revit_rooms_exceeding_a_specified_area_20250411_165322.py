# Purpose: This script updates the 'Department' parameter for Revit rooms exceeding a specified area.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Parameter,
    BuiltInParameter,
    UnitUtils,
    ForgeTypeId # Required for Revit 2021+ UnitUtils.ConvertToInternalUnits
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
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Ensure RevitAPIArchitecture.dll is available. Error: {}".format(e))

# Define the area threshold in square meters
area_threshold_sq_meters = 50.0

# Define the value to set for the Department parameter
new_department_value = "Large Occupancy"

# Convert the area threshold to Revit's internal units (square feet)
area_threshold_internal = -1.0 # Initialize with an invalid value

# Try using UnitUtils.ConvertToInternalUnits (requires Revit 2021+ and ForgeTypeId)
try:
    # Use a common ForgeTypeId for Area. If this fails, the fallback will be used.
    # Replace with SpecTypeId.Area if using a very recent API version and wanting the most modern approach.
    area_spec_id = ForgeTypeId("autodesk.spec.aec:area-2.0.0")
    area_threshold_internal = UnitUtils.ConvertToInternalUnits(area_threshold_sq_meters, area_spec_id)
except AttributeError:
    # Fallback for older APIs or if ForgeTypeId/modern UnitUtils is not available
    # Use manual conversion factor: 1 square meter = 1 / (0.3048 * 0.3048) square feet
    sq_meters_to_sq_feet_factor = 1.0 / (0.3048 * 0.3048)
    area_threshold_internal = area_threshold_sq_meters * sq_meters_to_sq_feet_factor
    # print("# Warning: Using manual conversion factor for area. Assumes internal units are Square Feet.")
except Exception as e:
    # Catch other potential errors during unit conversion and fallback
    sq_meters_to_sq_feet_factor = 1.0 / (0.3048 * 0.3048)
    area_threshold_internal = area_threshold_sq_meters * sq_meters_to_sq_feet_factor
    # print("# Warning: Error during unit conversion using UnitUtils ({}). Falling back to manual conversion.".format(e))

# Verify conversion was successful (either method)
if area_threshold_internal < 0:
     raise ValueError("Fatal Error: Could not convert area threshold ({} sq m) to internal units.".format(area_threshold_sq_meters))

# Collect all Room elements in the project
# 'doc' is assumed to be pre-defined
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Filter for elements that are actual Room instances (safer than relying solely on collector)
# Also implicitly excludes unplaced Rooms as their Area will be 0.0
rooms_to_process = [el for el in collector if isinstance(el, Room)]

# Counter for modified rooms (optional, for potential logging)
modified_count = 0

# Iterate through the collected rooms
for room in rooms_to_process:
    try:
        # Get the room's area (Area property is in internal units - square feet)
        room_area_internal = room.Area

        # Check if the area is strictly greater than the threshold
        if room_area_internal > area_threshold_internal:
            # Find the 'Department' parameter using the BuiltInParameter enum
            department_param = room.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)

            # Check if the parameter exists on the room and is not read-only
            if department_param and not department_param.IsReadOnly:
                # Check if the current value is different from the target value
                current_value = department_param.AsString() # Use AsString for text parameters
                if current_value != new_department_value:
                    # Set the parameter value (Transaction is handled externally)
                    department_param.Set(new_department_value)
                    modified_count += 1
            # else:
                # Optional: Log if the parameter is missing or read-only for a qualifying room
                # room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString() if room.get_Parameter(BuiltInParameter.ROOM_NAME) else "Unnamed"
                # print("# INFO: Room ID {} (Name: '{}', Area: {:.2f} sq ft) meets area criteria but 'Department' parameter is missing or read-only.".format(room.Id, room_name, room_area_internal))
                # pass

    except Exception as e:
        # Log errors encountered while processing a specific room (optional)
        # import traceback
        # room_name_err = "Unknown"
        # try:
        #     room_name_err = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
        # except: pass
        # print("# ERROR processing Room ID {} (Name: '{}'): {}".format(room.Id, room_name_err, e))
        # print(traceback.format_exc())
        pass # Continue processing next room even if one fails

# Optional: Final summary message (commented out as per standard format)
# print("# Script finished. Set 'Department' to '{}' for {} rooms with area > {} sq m.".format(new_department_value, modified_count, area_threshold_sq_meters))