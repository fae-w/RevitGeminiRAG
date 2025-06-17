# Purpose: This script sets the 'Comments' parameter to 'Requires Review' for doors narrower than a specified width.

﻿# Purpose: This script sets the 'Comments' parameter to 'Requires Review' for all door instances
# whose width is less than a specified value (800mm).

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter
)

# Define the width threshold in millimeters
max_width_mm = 800.0
# Revit's internal units are typically decimal feet. Convert mm to feet.
mm_to_feet_conversion = 1.0 / 304.8 # 1 foot = 304.8 mm
max_width_internal = max_width_mm * mm_to_feet_conversion # Approximately 2.62 feet

# Define the value to set for the 'Comments' parameter
new_comment_value = "Requires Review"

# Collect all door instances in the document
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

# Iterate through the collected doors
for door in collector:
    door_width_internal = None
    try:
        # Attempt to get the 'Width' parameter using the BuiltInParameter
        width_param = door.get_Parameter(BuiltInParameter.DOOR_WIDTH)

        # If BuiltInParameter didn't work, try looking up by name "Width"
        if not width_param or not width_param.HasValue:
             width_param = door.LookupParameter("Width") # Common parameter name for door types might hold the width

        # Check if the parameter was found and has a value
        if width_param and width_param.HasValue:
            door_width_internal = width_param.AsDouble()

        # If width was found and is less than the threshold
        if door_width_internal is not None and door_width_internal < max_width_internal:
            try:
                # Get the 'Comments' parameter (ALL_MODEL_INSTANCE_COMMENTS is typical)
                comments_param = door.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

                # Check if the parameter exists and is not read-only
                if comments_param and not comments_param.IsReadOnly:
                    # Set the parameter value
                    comments_param.Set(new_comment_value)
                # else: # Optional: Add debug/logging if needed
                    # if not comments_param:
                    #     print(f"# 'Comments' parameter not found for door ID: {door.Id}")
                    # elif comments_param.IsReadOnly:
                    #     print(f"# 'Comments' parameter is read-only for door ID: {door.Id}")

            except Exception as e_comment:
                # print(f"# Error setting comments for door ID {door.Id}: {e_comment}")
                pass # Silently continue if setting comments fails for a specific door

    except Exception as e_width:
        # print(f"# Error processing door ID {door.Id} for width: {e_width}")
        pass # Silently continue if an error occurs getting width for a specific door

# No explicit output required, changes are made directly to the model elements.