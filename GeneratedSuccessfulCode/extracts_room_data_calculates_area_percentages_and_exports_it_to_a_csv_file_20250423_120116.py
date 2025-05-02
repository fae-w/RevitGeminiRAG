# Purpose: This script extracts room data, calculates area percentages, and exports it to a CSV file.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Level, ElementId, BuiltInParameter
from Autodesk.Revit.DB.Architecture import Room # Specific import for Room class
import System

# --- Calculate Total Area of All Placed Rooms ---
total_area = 0.0
all_rooms_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in all_rooms_collector:
    # Ensure it is a Room element
    if isinstance(room, Room):
        try:
            # Check if the room is placed (Unplaced rooms have Location=None or Area=0)
            # Using Location property check is generally reliable for placed status
            if room.Location is not None:
                area_param = room.get_Parameter(BuiltInParameter.ROOM_AREA)
                if area_param and area_param.HasValue:
                    area_val = area_param.AsDouble()
                    if area_val > 1e-6: # Use a small tolerance to consider it having area
                        total_area += area_val
        except Exception as e:
            # Optional: Log error for debugging total area calculation
            # print("Error calculating total area for Room {0}: {1}".format(room.Id.ToString(), e))
            pass # Ignore rooms that cause errors during total area calculation

# --- Process All Placed Rooms for CSV Data ---
csv_lines = []
# Add header row
csv_lines.append('"Level","Room Name","Area (sq ft)","Percentage of Total Area (%)"')

processed_count = 0
rooms_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

for room in rooms_collector:
    if not isinstance(room, Room):
        continue

    # Skip unplaced rooms
    if room.Location is None:
        continue

    try:
        # --- Get Data for Placed Room ---

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
                level_name = "Associated Element Not Level ({0})".format(level_element.GetType().Name)
            else:
                level_name = "Level Element Not Found" # If GetElement returns null
        elif level_id == ElementId.InvalidElementId:
             level_name = "Invalid Level ID" # Should not happen for placed rooms normally
        else:
             # SpatialElement.Level property is another way
             level_prop = room.Level
             if level_prop:
                 level_name = level_prop.Name
                 if not level_name or level_name == "":
                     level_name = "Unnamed Level (from Property)"
             else:
                 level_name = "No Associated Level Found"

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
            if area_value > 1e-6 : # Only format if area is meaningful
                 area_str = System.String.Format("{0:.2f}", area_value)
            else:
                 area_str = "0.00" # Explicitly show zero for placed rooms with negligible area
                 area_value = 0.0 # Ensure value is 0 for percentage calculation

        # Percentage Area
        percentage_str = "N/A"
        if total_area > 1e-6: # Check total area is meaningful before dividing
            if area_value >= 0: # Ensure area is not negative
                 percentage = (area_value / total_area) * 100.0
                 percentage_str = System.String.Format("{0:.2f}", percentage)
            else:
                 percentage_str = "Invalid Area"
        elif area_value <= 1e-6: # If both total and room area are zero/negligible
             percentage_str = "0.00"
        else: # Total area is zero/negligible, but room area is not (edge case)
             percentage_str = "Total Area Zero"


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
    suggested_filename = 'rooms_area_report.csv'
    file_format = 'CSV'
    # Print the export marker and data
    print("EXPORT::{0}::{1}".format(file_format, suggested_filename))
    print(export_data_string)
else:
    # Use print for messages to the user if no data is exported
    print("# INFO: No placed Room elements found or processed in the project.")
    if total_area <= 1e-6:
        print("# INFO: The total area calculated for all placed rooms is zero or negligible.")