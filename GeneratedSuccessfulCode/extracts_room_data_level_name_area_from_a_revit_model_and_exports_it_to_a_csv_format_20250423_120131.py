# Purpose: This script extracts room data (level, name, area) from a Revit model and exports it to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Level, ElementId, BuiltInParameter
from Autodesk.Revit.DB.Architecture import Room # Specific import for Room class
import System

# List to hold CSV lines
csv_lines = []
# Add header row (without quotes as requested)
csv_lines.append('Level,Room Name,Area (sq ft)')

processed_count = 0
rooms_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in rooms_collector:
    if not isinstance(room, Room):
        continue

    # Skip unplaced rooms (Location is None for unplaced rooms)
    if room.Location is None:
        continue

    try:
        # --- Get Data for Placed Room ---

        # Level Name
        level_name = "Unknown_Level" # Use underscore to avoid potential comma issues if level name had comma
        level_id = room.LevelId
        if level_id is not None and level_id != ElementId.InvalidElementId:
            level_element = doc.GetElement(level_id)
            if isinstance(level_element, Level):
                 level_name_raw = level_element.Name
                 # Basic sanitization: replace commas if any, although user requested direct values
                 level_name = level_name_raw.replace(',', ';') if level_name_raw else "Unnamed_Level"
            elif level_element:
                level_name = "Associated_Element_Not_Level"
            else:
                level_name = "Level_Element_Not_Found"
        elif room.Level: # Alternative way to get level
             level_name_raw = room.Level.Name
             level_name = level_name_raw.replace(',', ';') if level_name_raw else "Unnamed_Level_Property"
        else:
             level_name = "No_Associated_Level"


        # Room Name
        room_name = "Unnamed_Room"
        name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
        if name_param and name_param.HasValue:
            room_name_raw = name_param.AsString()
            if room_name_raw and room_name_raw.strip():
                 # Basic sanitization: replace commas
                 room_name = room_name_raw.strip().replace(',', ';')
            else: # Parameter exists but is empty/whitespace
                 room_name_raw = room.Name
                 room_name = room_name_raw.replace(',', ';') if room_name_raw else "ID_" + room.Id.ToString()
        elif room.Name: # Fallback to Element.Name
            room_name_raw = room.Name
            room_name = room_name_raw.replace(',', ';')
        else: # Final fallback
             room_name = "ID_" + room.Id.ToString()


        # Area
        area_str = "0.00"
        area_value = 0.0
        area_param = room.get_Parameter(BuiltInParameter.ROOM_AREA)
        if area_param and area_param.HasValue:
            area_value = area_param.AsDouble() # Internal units are sq ft
            if area_value > 1e-6 : # Only format if area is meaningful
                 # Format to 2 decimal places, using standard locale formatting
                 area_str = System.String.Format("{0:.2f}", area_value)
                 # Replace potential locale-specific decimal separators like comma with a period
                 area_str = area_str.replace(',', '.')
            else:
                 area_str = "0.00" # Explicitly show zero

        # Append data row (without quotes)
        csv_lines.append(','.join([level_name, room_name, area_str]))
        processed_count += 1

    except Exception as e:
        # Optional: Log errors for specific rooms during processing
        try:
            room_id_str = room.Id.ToString()
            # print("# Error processing Room {0}: {1}".format(room_id_str, e)) # Commented out for production
        except:
            # print("# Error processing a Room element (ID unknown): {0}".format(e)) # Commented out
            pass # Silently skip rooms that cause errors

# --- Export Results ---
if processed_count > 0:
    # Format the final data string
    export_data_string = "\n".join(csv_lines)
    suggested_filename = 'room_area_report_no_quotes.csv'
    file_format = 'CSV'
    # Print the export marker and data
    print("EXPORT::{0}::{1}".format(file_format, suggested_filename))
    print(export_data_string)
else:
    # Use print for messages to the user if no data is exported
    print("# INFO: No placed Room elements found or processed in the project.")