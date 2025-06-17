# Purpose: This script creates a 3D view cropped to a selected room's bounding box in Revit.

# Purpose: This script creates a new 3D view cropped to the bounding box of a selected room in Revit.

﻿# Import necessary .NET assemblies and classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewFamilyType,
    ViewFamily,
    View3D,
    BoundingBoxXYZ,
    ElementId,
    BuiltInCategory,
    BuiltInParameter
)
# Import Room specifically from the Architecture namespace
from Autodesk.Revit.DB.Architecture import Room
from System.Collections.Generic import List
import Autodesk.Revit.Exceptions as RevitExceptions

# --- Helper function to find a 3D ViewFamilyType ---
def find_first_3d_view_type(doc_param):
    """Finds the first available 3D ViewFamilyType."""
    collector = FilteredElementCollector(doc_param).OfClass(ViewFamilyType)
    for vft in collector:
        # Check if it's a ThreeDimensional view family using the ViewFamily enum
        if vft.ViewFamily == ViewFamily.ThreeDimensional:
            return vft.Id
    return ElementId.InvalidElementId

# --- Main Script ---
# Assume 'doc' and 'uidoc' are pre-defined and a Transaction is already open

# 1. Get Selected Element
selected_ids = uidoc.Selection.GetElementIds()
selected_room = None
error_message = None

# Validate selection: must be exactly one element, and it must be a Room.
if not selected_ids or selected_ids.Count == 0:
    error_message = "# Error: No element selected. Please select exactly one Room."
elif selected_ids.Count > 1:
    error_message = "# Error: More than one element selected. Please select exactly one Room."
else:
    selected_element = doc.GetElement(selected_ids[0])
    # Check if the selected element is actually a Room instance
    if isinstance(selected_element, Room):
        selected_room = selected_element
    else:
        # Provide feedback if the selected element is not a Room
        error_message = "# Error: Selected element (ID: {}) is not a Room. Element Type: {}".format(selected_element.Id.ToString(), selected_element.GetType().Name) # Use format for IronPython 2.7

if error_message:
    print(error_message)
# Proceed only if a valid Room was identified
elif selected_room:
    # 2. Get Room Bounding Box
    # Passing None as argument gets the model-aligned bounding box
    room_bbox = selected_room.get_BoundingBox(None)

    if room_bbox is None:
        print("# Error: Could not retrieve bounding box for the selected Room (ID: {}). The room might not be placed or might lack geometry.".format(selected_room.Id.ToString())) # Use format
    else:
        # 3. Find a suitable 3D View Type ID
        view_type_id = find_first_3d_view_type(doc)

        if view_type_id == ElementId.InvalidElementId:
            print("# Error: No suitable 3D ViewFamilyType found in the project. Cannot create 3D view.")
        else:
            try:
                # 4. Create a New Isometric 3D View
                # The transaction management is handled externally by the C# wrapper
                new_view = View3D.CreateIsometric(doc, view_type_id)

                if new_view is None:
                     print("# Error: Failed to create the isometric 3D view using ViewFamilyType ID {}.".format(view_type_id.ToString())) # Use format
                else:
                    # 5. Apply the Room's Bounding Box as a Section Box
                    # Check if the BoundingBox is valid before setting
                    if room_bbox.Min and room_bbox.Max and not room_bbox.Min.IsAlmostEqualTo(room_bbox.Max):
                         new_view.IsSectionBoxActive = True
                         new_view.SetSectionBox(room_bbox)
                    else:
                        print("# Warning: Room bounding box is invalid or zero-sized. Cannot apply section box. Room ID: {}".format(selected_room.Id.ToString())) # Use format


                    # 6. Refine View Name (Optional but helpful)
                    new_view_name = "3D View Cropped to Room" # Default name
                    try:
                        room_name_param = selected_room.get_Parameter(BuiltInParameter.ROOM_NAME)
                        room_number_param = selected_room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                        room_name = room_name_param.AsString() if room_name_param else "Unnamed"
                        room_number = room_number_param.AsString() if room_number_param else "NoNumber"
                        # Construct a more descriptive name
                        new_view_name = "3D - Room {} ({})".format(room_number, room_name) # Use format
                        new_view.Name = new_view_name
                    except RevitExceptions.ArgumentException as name_arg_ex:
                         # Handle cases where the name might be invalid or duplicate if CreateIsometric didn't handle it
                         print("# Warning: Could not set desired view name '{}'. It might be invalid or already in use. Using default name. Error: {}".format(new_view_name, str(name_arg_ex))) # Use format
                         # Keep the default name assigned by Revit if renaming fails
                    except Exception as name_ex:
                        print("# Warning: An error occurred while trying to rename the new view. Using default name. Error: {}".format(str(name_ex))) # Use format


                    # Optional: Make the new view the active view
                    try:
                        uidoc.ActiveView = new_view
                    except Exception as active_view_ex:
                         # This might fail if the script is run in a context where changing active view is not allowed
                         print("# Warning: Could not set the newly created view as active. Error: {}".format(str(active_view_ex))) # Use format

                    # Confirmation message (optional)
                    # print("# Successfully created 3D view '{}' and applied section box from Room ID {}.".format(new_view.Name, selected_room.Id.ToString())) # Use format

            except RevitExceptions.InvalidOperationException as inv_op_ex:
                 print("# Error: An InvalidOperationException occurred during view creation or modification. This might happen if the view type is incompatible or view creation is disallowed in the current context. API Message: {}".format(inv_op_ex.Message)) # Use format
            except Exception as e:
                # Catch any other unexpected errors during the process
                print("# Error during view creation or modification: {}".format(str(e))) # Use format

# else: # This case is implicitly handled by the initial error message print
#     pass # No valid room selected, message already printed