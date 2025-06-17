# Purpose: This script calculates wall areas by type, formats it as CSV, and creates a text note in the active view.

# Purpose: This script calculates wall areas per type in the active view, formats the data as CSV, and creates a text note with the results.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    WallType,
    ElementId,
    TextNote,
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
    # sys.exit() # Cannot exit here, let script finish

# --- Calculate Wall Areas per Type ---
wall_type_areas = Dictionary[ElementId, float]()
total_area = 0.0

collector = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

for wall in collector:
    if isinstance(wall, Wall):
        try:
            area_param = wall.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            if area_param and area_param.HasValue:
                area = area_param.AsDouble()
                if area > 0:
                    wall_type_id = wall.GetTypeId()
                    if wall_type_id != ElementId.InvalidElementId:
                        if wall_type_areas.ContainsKey(wall_type_id):
                            wall_type_areas[wall_type_id] += area
                        else:
                            wall_type_areas[wall_type_id] = area
                        total_area += area
        except Exception as e:
            # print("# Skipping wall {{{{}}}} due to error: {{{{}}}}".format(wall.Id, e)) # Optional debug
            pass

# --- Format CSV Content ---
csv_lines = []
csv_lines.append('"Wall Type Name","Total Area (sq ft)","Percentage"') # Header

if total_area > 0:
    # Sort wall types by name for consistent output
    sorted_type_ids = sorted(wall_type_areas.Keys, key=lambda type_id: doc.GetElement(type_id).Name if doc.GetElement(type_id) else "")

    for type_id in sorted_type_ids:
        try:
            wall_type = doc.GetElement(type_id)
            if wall_type:
                type_name = wall_type.Name
                area = wall_type_areas[type_id]
                percentage = (area / total_area) * 100.0

                # Escape quotes in name just in case
                safe_name = '"' + type_name.replace('"', '""') + '"'
                area_str = "{:.2f}".format(area) # Escaped format
                perc_str = "{:.2f}%".format(percentage) # Escaped format

                csv_lines.append(','.join([safe_name, area_str, perc_str]))
        except Exception as e:
            # print("# Error processing wall type {{{{}}}} : {{{{}}}}".format(type_id, e)) # Optional debug
            pass
else:
    csv_lines.append("No walls with area found in this view.")

csv_content = "\n".join(csv_lines)

# --- Determine Text Note Position (Center of View Crop Box) ---
position = None
try:
    crop_box = active_view.CropBox
    if active_view.CropBoxActive and active_view.CropBoxVisible:
         # Calculate center of the crop box
        center_x = (crop_box.Min.X + crop_box.Max.X) / 2.0
        center_y = (crop_box.Min.Y + crop_box.Max.Y) / 2.0
        # Use the Z of the crop box Min, or view origin Z if needed
        center_z = crop_box.Min.Z
        position = XYZ(center_x, center_y, center_z)
    else:
         # Fallback: Use the view's origin if crop box is not active/visible
         position = active_view.Origin
         print("# Warning: Crop box not active/visible. Placing text at view origin.")

    # If view origin is also problematic, pick an arbitrary point
    if position is None:
        position = XYZ(0, 0, 0)
        print("# Warning: Could not determine view center. Placing text at (0,0,0).")

except Exception as e:
    # Fallback if accessing crop box fails
    print("# Error getting view center: {{{{}}}}. Placing text at view origin.".format(e)) # Escaped
    try:
        position = active_view.Origin
        if position is None: # Last resort
             position = XYZ(0, 0, 0)
             print("# Warning: View origin is null. Placing text at (0,0,0).")
    except:
        position = XYZ(0, 0, 0) # Absolute fallback
        print("# Error getting view origin. Placing text at (0,0,0).")


# --- Create Text Note ---
if position and csv_content:
    try:
        # Get default text note type
        default_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType)
        if default_type_id == ElementId.InvalidElementId:
            # If no default, try finding any text note type
            collector = FilteredElementCollector(doc).OfClass(TextNoteType)
            first_type = collector.FirstElement()
            if first_type:
                default_type_id = first_type.Id
            else:
                print("# Error: No TextNoteType found in the document.")
                # sys.exit() # Cannot exit

        if default_type_id != ElementId.InvalidElementId:
             # Use TextNoteOptions for alignment (optional, default is Left/Top)
            # opts = TextNoteOptions(default_type_id)
            # opts.HorizontalAlignment = HorizontalTextAlignment.Center
            # opts.VerticalAlignment = VerticalTextAlignment.Middle # Not directly settable for creation position

            # Create unwrapped text note using the simpler overload
            # The position for left-aligned text is the top-left corner.
            # To truly center, calculation based on text size/width is needed, which is complex.
            # Placing at the calculated center point is usually sufficient visually.
            TextNote.Create(doc, active_view.Id, position, csv_content, default_type_id)
            print("# Text note created.")
        else:
            print("# Error: Could not find a valid TextNoteType ID.")

    except Exception as e:
        print("# Error creating text note: {{{{}}}}".format(e)) # Escaped
elif not csv_content:
    print("# No content generated for the text note.")
elif not position:
    print("# Could not determine a position for the text note.")