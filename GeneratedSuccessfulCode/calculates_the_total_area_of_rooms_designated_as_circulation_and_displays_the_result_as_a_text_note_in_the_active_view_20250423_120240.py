# Purpose: This script calculates the total area of rooms designated as 'Circulation' and displays the result as a Text Note in the active view.

﻿# Purpose: Calculate the total area of rooms designated as 'Circulation'
#          and display the result as a Text Note in the active view.

import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for Dictionary/List if used, good practice

# Import necessary Revit DB classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    TextNote,
    TextNoteType,
    ElementTypeGroup,
    XYZ,
    View
)

# Import Room class specifically from Architecture namespace
try:
    from Autodesk.Revit.DB.Architecture import Room
except ImportError:
    try:
        clr.AddReference('RevitAPIArchitecture')
        from Autodesk.Revit.DB.Architecture import Room
    except Exception as e:
        raise ImportError("Could not load Room class from Autodesk.Revit.DB.Architecture. Error: {}".format(e))

# --- Configuration ---
target_department_value = "Circulation" # Case-sensitive

# --- Calculation ---
total_circulation_area = 0.0
room_count = 0
processed_room_count = 0

# Collect all Room elements
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

# Filter for actual Room instances and check parameters
for element in collector:
    # Ensure element is a valid Room object
    if isinstance(element, Room):
        processed_room_count += 1
        try:
            # Get the 'Department' parameter
            department_param = element.get_Parameter(BuiltInParameter.ROOM_DEPARTMENT)

            # Check if parameter exists and matches the target value
            if department_param and department_param.HasValue:
                department_value = department_param.AsString() # Use AsString for text comparison
                if department_value == target_department_value:
                    # Get the room's area (Area property is in internal units - square feet)
                    room_area_internal = element.Area
                    if room_area_internal > 0: # Only sum areas for placed rooms
                        total_circulation_area += room_area_internal
                        room_count += 1

        except Exception as e:
            # Optional: Log error processing a specific room
            # print("# ERROR processing Room ID {}: {}".format(element.Id, e))
            pass # Continue to next room

# --- Output to Text Note ---

# Format the result string
# Display area in square feet (internal units)
result_text = "Total Circulation Area: {:.2f} sq ft (from {} rooms)".format(total_circulation_area, room_count)
# Alternatively, could print to console:
# print(result_text)

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Cannot create text note. Requires an active, non-template view.")
    print("# Calculated result: {}".format(result_text)) # Print to console as fallback
else:
    # Determine Text Note Position (Center of Active View Crop Box or Origin)
    position = None
    try:
        if active_view.CropBoxActive and active_view.CropBoxVisible:
            crop_box = active_view.CropBox
            # Calculate center of the crop box
            center_x = (crop_box.Min.X + crop_box.Max.X) / 2.0
            center_y = (crop_box.Min.Y + crop_box.Max.Y) / 2.0
            center_z = crop_box.Min.Z # Use Z of the crop box Min
            position = XYZ(center_x, center_y, center_z)
        else:
            # Fallback: Use the view's origin
            position = active_view.Origin
            # print("# Warning: Crop box not active/visible. Placing text at view origin.")

        # If view origin is also problematic (e.g., None), pick an arbitrary point
        if position is None:
            position = XYZ(0, 0, 0)
            # print("# Warning: Could not determine view center. Placing text at (0,0,0).")

    except Exception as e:
        # Fallback if accessing crop box or origin fails
        print("# Error getting view center: {}. Placing text at (0,0,0).".format(e))
        position = XYZ(0, 0, 0) # Absolute fallback

    # Create Text Note
    if position:
        try:
            # Get default text note type ID
            default_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType)

            # If no default, find the first available TextNoteType
            if default_type_id == ElementId.InvalidElementId:
                # print("# Warning: No default TextNoteType set. Searching for any TextNoteType.")
                collector_types = FilteredElementCollector(doc).OfClass(TextNoteType)
                first_type = collector_types.FirstElement()
                if first_type:
                    default_type_id = first_type.Id
                    # print("# Found TextNoteType: {}".format(first_type.Name))
                else:
                    print("# Error: No TextNoteType found in the document. Cannot create text note.")
                    default_type_id = ElementId.InvalidElementId # Ensure it remains invalid

            if default_type_id != ElementId.InvalidElementId:
                 # Create an unwrapped text note.
                 TextNote.Create(doc, active_view.Id, position, result_text, default_type_id)
                 # print("# Text note created with circulation area summary.")
            else:
                 print("# Error: Could not find a valid TextNoteType ID to create the note.")
                 print("# Calculated result: {}".format(result_text)) # Print to console as fallback


        except Exception as e:
            print("# Error creating text note: {}".format(e))
            print("# Calculated result: {}".format(result_text)) # Print to console as fallback
    else:
        # This case should ideally not be reached due to fallback position logic
        print("# Error: Could not determine a position for the text note.")
        print("# Calculated result: {}".format(result_text)) # Print to console as fallback

# Final summary message (optional, uncomment if needed for console debugging)
# print("# Script finished. Processed {} rooms.".format(processed_room_count))
# print("# Found {} rooms with Department '{}'.".format(room_count, target_department_value))
# print("# Total Area: {:.2f} sq ft".format(total_circulation_area))