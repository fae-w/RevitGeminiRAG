# Purpose: This script calculates wall areas by type and creates a CSV formatted text note in the active Revit view.

# Purpose: This script calculates and displays the total area of walls per type in the active view as a text note, formatted as a CSV summary.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for Dictionary
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    WallType,
    ElementId,
    TextNote,
    TextNoteType,
    TextNoteOptions,
    XYZ,
    BuiltInParameter,
    ElementTypeGroup,
    View,
    BoundingBoxXYZ,
    HorizontalTextAlignment,
    VerticalTextAlignment
)
from System.Collections.Generic import Dictionary

# Get the active view
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
    # Consider exiting or providing a default behavior if needed
    # sys.exit() # Cannot exit here, let script finish gracefully

# --- Calculate Wall Areas per Type (Project-wide) ---
wall_type_areas = Dictionary[ElementId, float]()
total_area = 0.0

# Collect all walls in the project
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

for wall in collector:
    if isinstance(wall, Wall):
        try:
            # Use HOST_AREA_COMPUTED for area
            area_param = wall.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                area = area_param.AsDouble()
                if area > 0: # Only consider walls with positive area
                    wall_type_id = wall.GetTypeId()
                    if wall_type_id != ElementId.InvalidElementId:
                        if wall_type_areas.ContainsKey(wall_type_id):
                            wall_type_areas[wall_type_id] += area
                        else:
                            wall_type_areas[wall_type_id] = area
                        total_area += area
        except Exception as e:
            # print("# Skipping wall {{{{{{{{}}}}}}}} due to error getting area: {{{{{{{{}}}}}}}}".format(wall.Id, e)) # Optional debug
            pass

# --- Format CSV Content ---
csv_lines = []
csv_lines.append('"Wall Type Name","Total Area (sq ft)","Percentage"') # Header

if total_area > 0 and wall_type_areas.Count > 0:
    # Sort wall types by name for consistent output
    # Use a lambda to safely get the name, handling potential null elements
    sorted_type_ids = sorted(wall_type_areas.Keys, key=lambda type_id: (doc.GetElement(type_id).Name if doc.GetElement(type_id) else ""))

    for type_id in sorted_type_ids:
        try:
            wall_type = doc.GetElement(type_id)
            if wall_type:
                type_name = wall_type.Name
                area = wall_type_areas[type_id]
                percentage = (area / total_area) * 100.0

                # Escape quotes in name for CSV safety
                safe_name = '"' + type_name.replace('"', '""') + '"'
                # Format numbers to 2 decimal places
                area_str = "{:.2f}".format(area) # Escaped format specifier
                perc_str = "{:.2f}%".format(percentage) # Escaped format specifier

                csv_lines.append(','.join([safe_name, area_str, perc_str]))
        except Exception as e:
            # print("# Error processing wall type {{{{{{{{}}}}}}}} : {{{{{{{{}}}}}}}}".format(type_id, e)) # Optional debug
            pass
elif wall_type_areas.Count == 0:
     csv_lines.append("No walls with computable area found in the project.")
else: # total_area is 0 but there might be types? Unlikely but handle.
    csv_lines.append("No walls with positive area found in the project.")


csv_content = "\n".join(csv_lines)

# --- Determine Text Note Position (Center of Active View Crop Box or Origin) ---
position = None
try:
    if active_view.CropBoxActive and active_view.CropBoxVisible:
        crop_box = active_view.CropBox
         # Calculate center of the crop box
        center_x = (crop_box.Min.X + crop_box.Max.X) / 2.0
        center_y = (crop_box.Min.Y + crop_box.Max.Y) / 2.0
        # Use the Z of the crop box Min, assuming it's relevant for placement
        center_z = crop_box.Min.Z
        position = XYZ(center_x, center_y, center_z)
        # print("# Debug: Using Crop Box Center")
    else:
         # Fallback: Use the view's origin if crop box is not active/visible
         position = active_view.Origin
         print("# Warning: Crop box not active/visible. Placing text at view origin.")
         # print("# Debug: Using View Origin")

    # If view origin is also problematic (e.g., None), pick an arbitrary point
    if position is None:
        position = XYZ(0, 0, 0)
        print("# Warning: Could not determine view center from crop box or origin. Placing text at (0,0,0).")
        # print("# Debug: Using Fallback (0,0,0)")


except Exception as e:
    # Fallback if accessing crop box or origin fails
    print("# Error getting view center: {}. Placing text at (0,0,0).".format(e))
    position = XYZ(0, 0, 0) # Absolute fallback


# --- Create Text Note ---
if position and csv_content:
    try:
        # Get default text note type ID
        default_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType)

        # If no default, find the first available TextNoteType
        if default_type_id == ElementId.InvalidElementId:
            print("# Warning: No default TextNoteType set. Searching for any TextNoteType.")
            collector_types = FilteredElementCollector(doc).OfClass(TextNoteType)
            first_type = collector_types.FirstElement()
            if first_type:
                default_type_id = first_type.Id
                print("# Found TextNoteType: {}".format(first_type.Name))
            else:
                print("# Error: No TextNoteType found in the document. Cannot create text note.")
                default_type_id = ElementId.InvalidElementId # Ensure it remains invalid

        if default_type_id != ElementId.InvalidElementId:
             # Create an unwrapped text note.
             # The 'position' is typically the top-left corner for left-aligned text.
             # Centering the text *content* requires TextNoteOptions, but placement at the view's
             # calculated center point is usually sufficient visually.
             TextNote.Create(doc, active_view.Id, position, csv_content, default_type_id)
             print("# Text note created with wall area summary.")
        # else: # Already handled above if no type found
        #    print("# Error: Could not find a valid TextNoteType ID.")

    except Exception as e:
        print("# Error creating text note: {}".format(e))
elif not csv_content:
    print("# No content generated for the text note.")
elif not position:
    print("# Could not determine a position for the text note.")