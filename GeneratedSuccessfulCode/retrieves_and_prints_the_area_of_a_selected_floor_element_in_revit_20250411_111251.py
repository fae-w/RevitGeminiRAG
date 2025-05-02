# Purpose: This script retrieves and prints the area of a selected floor element in Revit.

# Purpose: This script retrieves and prints the area of a selected floor element in Revit.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import Floor, BuiltInCategory, ElementId, BuiltInParameter, Parameter

# Get the current selection
selection_ids = uidoc.Selection.GetElementIds()

# Check if exactly one element is selected
if not selection_ids or len(selection_ids) != 1:
    print("# Error: Please select exactly one floor element.")
else:
    selected_id = selection_ids[0]
    selected_element = doc.GetElement(selected_id)

    # Check if the selected element is a Floor
    if isinstance(selected_element, Floor):
        floor = selected_element
        try:
            # Get the area parameter using BuiltInParameter
            area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                # Area is typically in internal units (square feet)
                area_value_internal = area_param.AsDouble()
                # Format the area to two decimal places
                area_str = "{:.2f}".format(area_value_internal) # Escaped format specifier
                print("Selected Floor Area: {} square feet".format(area_str)) # Escaped format specifier
            else:
                print("# Error: Could not retrieve the area parameter for the selected floor.")
        except Exception as e:
            print("# Error accessing floor area: {}".format(e)) # Escaped format specifier
    else:
        print("# Error: The selected element is not a floor.")