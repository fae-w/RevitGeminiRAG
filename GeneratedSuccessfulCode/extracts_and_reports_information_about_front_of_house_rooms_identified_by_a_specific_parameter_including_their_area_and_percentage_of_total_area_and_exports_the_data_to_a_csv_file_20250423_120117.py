# Purpose: This script extracts and reports information about 'Front of House' rooms, identified by a specific parameter, including their area and percentage of total area, and exports the data to a CSV file.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Level, ElementId, BuiltInParameter
from Autodesk.Revit.DB.Architecture import Room # Specific import for Room class
import System

# --- Configuration ---
# Assumption: Rooms are identified as "Front of House" if their 'Department' parameter value contains "front of house" (case-insensitive).
# Change this string or the parameter check logic if needed.
FOH_IDENTIFIER_TEXT = "front of house"
FOH_PARAMETER_TO_CHECK = BuiltInParameter.ROOM_DEPARTMENT

# --- Calculate Total Area of All Rooms ---
total_area = 0.0
all_rooms_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in all_rooms_collector:
    # Ensure it is a Room element and potentially placed (Area > 0)
    if isinstance(room, Room):
        try:
            # Check if the room is placed (Unplaced rooms have 0 area)
            # Using Location property check is more reliable for placed status than just Area > 0
            if room.Location is not None:
                area_param = room.get_Parameter(BuiltInParameter.ROOM_AREA)
                if area_param and area_param.HasValue:
                    area_val = area_param.AsDouble()
                    if area_val > 0.001: # Use a small tolerance instead of == 0
                        total_area += area_val
        except Exception as e:
            # Optional: Log error for debugging total area calculation
            # print("Error calculating total area for Room {0}: {1}".format(room.Id.ToString(), e))
            pass # Ignore rooms that cause errors during total area calculation

# --- Process "Front of House" Rooms ---
csv_lines = []
# Add header row
csv_lines.append('"Level","Room Name","Area (sq ft)","Percentage of Total Area (%)"')

processed_count = 0
foh_rooms_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in foh_rooms_collector:
    if not isinstance(room, Room):
        continue

    # Skip unplaced rooms
    if room.Location is None:
        continue

    try:
        # --- Check if it's a "Front of House" room based on the defined parameter ---
        is_foh = False
        check_param = room.get_Parameter(FOH_PARAMETER_TO_CHECK)
        if check_param and check_param.HasValue:
            param_value = check_param.AsString()
            # Check if the parameter value (string) contains the identifier text (case-insensitive)
            if param_value and FOH_IDENTIFIER_TEXT in param_value.lower():
                is_foh = True

        # If not identified as FOH by the parameter, skip this room
        if not is_foh:
            continue

        # --- Get Data for FOH Room ---
        # Level Name
        level_name = "Unknown Level"
        level_id = room.LevelId
        if level_id is not None and level_id != ElementId.InvalidElementId:
            level_element = doc.GetElement(level_id)
            if isinstance(level_element, Level):
                 level_name = level_element.Name
                 if not level_name or level_name == "":
                     level_name = "Unnamed Level"
            elif level_element: # If element exists but isn't a Level
                level_name = "Level Not Level ({0})".format(level_element.GetType().Name)
            else:
                level_name = "Level Element Not Found" # If GetElement returns null
        elif level_id == ElementId.InvalidElementId:
             level_name = "Invalid Level ID" # Typically means Unplaced Room, though we filter those
        else:
             level_name = "No Associated Level"

        # Room Name
        room_name = "Unnamed Room"
        # Try getting name from standard Room Name parameter first
        name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
        if name_param and name_param.HasValue:
            room_name_val = name_param.AsString()
            if room_name_val and room_name_val.strip(): # Check if not None and not empty/whitespace
                 room_name = room_name_val.strip()
            else: # If parameter exists but has no value, fallback
                room_name = room.Name if room.Name else "ID: " + room.Id.ToString()
        elif room.Name: # Fallback to Element.Name if parameter doesn't exist
            room_name = room.Name
        else: # Final fallback if both fail
             room_name = "ID: " + room.Id.ToString()


        # Area
        area_str = "N/A"
        area_value = 0.0
        area_param = room.get_Parameter(BuiltInParameter.ROOM_AREA)
        if area_param and area_param.HasValue:
            area_value = area_param.AsDouble() # Internal units are sq ft
            if area_value > 0.001 : # Only format if area is meaningful
                 area_str = System.String.Format("{0:.2f}", area_value)
            else:
                 area_str = "0.00" # Explicitly show zero for placed rooms with no area

        # Percentage Area
        percentage_str = "N/A"
        if total_area > 0.001 and area_value > 0.001: # Check both total and room area are meaningful
            percentage = (area_value / total_area) * 100.0
            percentage_str = System.String.Format("{0:.2f}", percentage)
        elif total_area <= 0.001:
             percentage_str = "Total Area Zero/Negligible"
        else: # Room area is zero or negligible
             percentage_str = "0.00"


        # Escape quotes for CSV safety and enclose in quotes
        safe_level_name = '"' + level_name.replace('"', '""') + '"'
        safe_room_name = '"' + room_name.replace('"', '""') + '"'
        safe_area_str = '"' + area_str.replace('"', '""') + '"'
        safe_percentage_str = '"' + percentage_str.replace('"', '""') + '"'

        # Append data row
        csv_lines.append(','.join([safe_level_name, safe_room_name, safe_area_str, safe_percentage_str]))
        processed_count += 1

    except Exception as e:
        # Optional: Log errors for specific rooms during processing
        try:
            room_id_str = room.Id.ToString()
            # print("Error processing Room {0}: {1}".format(room_id_str, e))
        except:
            # print("Error processing a Room element (ID unknown): {0}".format(e))
            pass # Silently skip rooms that cause errors

# --- Export Results ---
if processed_count > 0:
    # Format the final data string
    export_data_string = "\n".join(csv_lines)
    suggested_filename = 'front_of_house_rooms_report.csv'
    file_format = 'CSV'
    # Print the export marker and data
    print("EXPORT::{0}::{1}".format(file_format, suggested_filename))
    print(export_data_string)
else:
    # Use print for messages to the user if no data is exported
    print("# INFO: No 'Front of House' rooms found or processed.")
    print("# INFO: This script identifies FOH rooms if their '{0}' parameter contains '{1}' (case-insensitive) and they are placed rooms.".format(FOH_PARAMETER_TO_CHECK.ToString(), FOH_IDENTIFIER_TEXT))
    if total_area <= 0.001:
        print("# INFO: The total area calculated for all placed rooms is zero or negligible, percentages cannot be calculated.")