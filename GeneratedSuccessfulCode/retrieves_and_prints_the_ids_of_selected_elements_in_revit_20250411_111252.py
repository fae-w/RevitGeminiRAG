# Purpose: This script retrieves and prints the IDs of selected elements in Revit.

# Purpose: This script retrieves and prints the IDs of selected elements in Revit.

﻿# Import necessary classes
from Autodesk.Revit.DB import ElementId
# Selection class is accessed via uidoc.Selection, no direct import needed
# from Autodesk.Revit.UI import Selection # Optional explicit import
# ICollection<ElementId> is returned by GetElementIds(), iteration works directly

# Get the current selection object from the UIDocument
selection = uidoc.Selection

# Get the ElementIds of the currently selected elements
# This returns an ICollection<ElementId>
selected_ids = selection.GetElementIds()

# Check if any elements are selected
if selected_ids and selected_ids.Count > 0:
    # If elements are selected, print their IDs
    # If only one element is selected, this loop will run once.
    print("Selected Element ID(s):")
    for element_id in selected_ids:
        # Print the ElementId object representation
        print("- {}".format(element_id))
        # Alternatively, to print the integer value of the ID:
        # print("- {}".format(element_id.IntegerValue))

    # Example: If you specifically need the ID of the *first* selected element
    # first_selected_id = list(selected_ids)[0] # Convert to list to access by index
    # print("First selected Element ID: {}".format(first_selected_id))

else:
    # If no elements are selected, print a message
    print("No elements are currently selected.")