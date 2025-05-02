# Purpose: This script selects rooms lacking a valid Room Number parameter in Revit.

# Purpose: This script selects rooms that lack a valid Room Number parameter value in Revit.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Parameter # Explicitly import Parameter
)
# Import Architecture namespace specifically for Room
import Autodesk.Revit.DB.Architecture as Arch
from Autodesk.Revit.DB.Architecture import Room

from System.Collections.Generic import List

# List to hold the IDs of rooms without a number
rooms_without_number_ids = []

# Collect all Room elements
collector = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_Rooms)\
            .WhereElementIsNotElementType()

for element in collector:
    # Check if the element is a Room
    if isinstance(element, Room):
        room = element
        # Check if the room is placed (e.g., has a valid location or area)
        # Unplaced rooms often lack meaningful parameter values.
        # Checking Area is a common way to filter for placed rooms.
        is_placed = False
        try:
            if room.Area > 1e-6: # Using a small tolerance for floating point comparison
                 is_placed = True
        except Exception:
            # Some rooms might throw exceptions on accessing Area if not properly placed/initialized
            pass # Treat as not placed

        if is_placed:
            try:
                # Get the Room Number parameter using BuiltInParameter
                number_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)

                # Verify the parameter exists and check its value
                # A parameter exists if number_param is not None.
                # A parameter has *no value* if HasValue is False, or if AsString() returns None or an empty string.
                has_value = False
                if number_param is not None and number_param.HasValue:
                    param_value_str = number_param.AsString()
                    # Check if the string value is not None and not empty
                    if param_value_str is not None and param_value_str.strip() != "":
                        has_value = True

                # If the parameter doesn't have a valid, non-empty value, add the room ID
                if not has_value:
                    rooms_without_number_ids.append(room.Id)

            except Exception as e:
                # Log error processing a specific room if needed during debugging
                # print("# Error processing Room ID {0}: {1}".format(room.Id, e)) # Escaped format
                pass # Continue with the next room if an error occurs

# Prepare the list of ElementIds for selection
selection_list = List[ElementId](rooms_without_number_ids)

# Select the rooms in the UI
if selection_list.Count > 0:
    try:
        uidoc.Selection.SetElementIds(selection_list)
        # Optional: print("# Selected {0} rooms without a valid 'Room Number'.".format(selection_list.Count)) # Escaped format
    except Exception as sel_ex:
        print("# Error setting selection: {0}".format(sel_ex)) # Escaped format
else:
    # Optional: print("# All placed rooms have a valid value for the 'Room Number' parameter.")
    # Ensure selection is cleared if nothing matched
    uidoc.Selection.SetElementIds(List[ElementId]())