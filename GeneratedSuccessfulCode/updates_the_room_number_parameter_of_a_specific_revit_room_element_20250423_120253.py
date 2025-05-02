# Purpose: This script updates the 'Room Number' parameter of a specific Revit Room element.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import Element, ElementId, BuiltInParameter, Parameter
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


# --- Configuration ---
target_element_id_int = 54321
new_room_number_value = "G.01a"
# --- End Configuration ---

try:
    # Construct the ElementId
    target_element_id = ElementId(target_element_id_int)

    # Get the element from the document
    element = doc.GetElement(target_element_id)

    if element:
        # Check if the element is actually a Room
        if isinstance(element, Room):
            # Get the 'Room Number' parameter
            room_number_param = element.get_Parameter(BuiltInParameter.ROOM_NUMBER)

            # Check if the parameter exists and is not read-only
            if room_number_param and not room_number_param.IsReadOnly:
                # Set the new value for the 'Room Number' parameter
                room_number_param.Set(new_room_number_value)
                # print("# Successfully updated Room Number for element ID {}".format(target_element_id_int)) # Optional success message
            else:
                if not room_number_param:
                    print("# Error: 'Room Number' parameter not found for Room ID {}.".format(target_element_id_int))
                elif room_number_param.IsReadOnly:
                    print("# Error: 'Room Number' parameter is read-only for Room ID {}.".format(target_element_id_int))
        else:
            print("# Error: Element with ID {} is not a Room element. It is a {}.".format(target_element_id_int, element.GetType().Name))
    else:
        print("# Error: Element with ID {} not found in the document.".format(target_element_id_int))

except Exception as e:
    print("# Error: An unexpected error occurred processing element ID {}: {}".format(target_element_id_int, e))