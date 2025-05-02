# Purpose: This script selects doors in Revit whose width is less than a specified value.

# Purpose: This script selects doors in Revit with a width less than a specified threshold.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections') # Required for List<T>
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, BuiltInParameter, Parameter
)
from System.Collections.Generic import List

# Define the width threshold in millimeters
max_width_mm = 750.0
# Revit's internal units are typically decimal feet. Convert mm to feet.
mm_to_feet_conversion = 1.0 / 304.8 # 1 foot = 304.8 mm
max_width_internal = max_width_mm * mm_to_feet_conversion # Approximately 2.46 feet

# List to store IDs of doors to select
doors_to_select_ids = []

# Create a collector for door instances in the document
collector = FilteredElementCollector(doc)
door_collector = collector.OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

# Iterate through collected doors
for door in door_collector:
    try:
        # Attempt to get the 'Width' parameter using the BuiltInParameter
        width_param = door.get_Parameter(BuiltInParameter.DOOR_WIDTH)

        # If BuiltInParameter didn't work, try looking up by name "Width"
        if not width_param or not width_param.HasValue:
             width_param = door.LookupParameter("Width") # Common parameter name

        # Check if the parameter was found and has a value
        if width_param and width_param.HasValue:
            # Get the width value (which is in internal units - feet)
            door_width_internal = width_param.AsDouble()

            # Check if the width is less than the threshold
            if door_width_internal < max_width_internal:
                doors_to_select_ids.append(door.Id)
                
        # else:
            # Optional: Handle cases where width parameter is not found or has no value
            # print("# Debug: Width parameter not found or has no value for Door ID: {}".format(door.Id))
            # pass

    except Exception as e:
        # Silently skip doors where parameter access causes an error
        # Optional: print debug message
        # print("# Debug: Error processing Door ID {}: {}".format(door.Id, e))
        pass

# If any matching doors were found, proceed to select them
if doors_to_select_ids:
    # Convert the Python list of ElementIds to a .NET List<ElementId>
    selection_list = List[ElementId](doors_to_select_ids)

    # Set the selection in the Revit UI
    try:
        uidoc.Selection.SetElementIds(selection_list)
        # Optional: Print confirmation message
        # print("# Selected {} doors with Width less than {}mm.".format(len(doors_to_select_ids), max_width_mm))
    except Exception as sel_ex:
        print("# Error setting selection: {}".format(sel_ex))
# else:
    # Optional: print message if no doors met criteria
    # print("# No doors found with Width less than {}mm.".format(max_width_mm))