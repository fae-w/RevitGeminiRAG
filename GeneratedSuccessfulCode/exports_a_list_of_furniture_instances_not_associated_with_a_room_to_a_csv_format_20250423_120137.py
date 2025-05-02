# Purpose: This script exports a list of furniture instances not associated with a room to a CSV format.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, FamilyInstance,
    BuiltInParameter, ElementId, LocationPoint, XYZ
)
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System # For string formatting

# List to hold CSV lines for Excel export
csv_lines = []
# Add header row - ensuring quotes for safety
csv_lines.append('"Mark","Family / Type Name","Element ID"')

# Collect all Furniture instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType()

# Iterate through furniture instances
processed_count = 0
for inst in collector:
    if isinstance(inst, FamilyInstance):
        is_in_room = False
        try:
            # --- Check Room association using FamilyInstance.Room property ---
            # This property gets the room for the instance in the *last* phase of the document.
            # If it's None, the instance is considered not in a room for that phase.
            if hasattr(inst, 'Room') and inst.Room is not None:
                 # Check if the room object retrieved is actually a valid Room element
                 room_element = doc.GetElement(inst.Room.Id)
                 if room_element is not None and isinstance(room_element, Room):
                     is_in_room = True

            # Optional: Fallback using GetRoomAtPoint if Room property is None or not reliable
            # if not is_in_room:
            #     location = inst.Location
            #     if location and isinstance(location, LocationPoint):
            #         point = location.Point
            #         if point:
            #             # Check room at the instance's location point in the last phase
            #             room_at_point = doc.GetRoomAtPoint(point)
            #             if room_at_point is not None and isinstance(room_at_point, Room):
            #                 is_in_room = True # Found a room using location point

            # If the instance is NOT associated with a room, collect its data
            if not is_in_room:
                furniture_mark = "N/A"
                family_type_name = "N/A"
                element_id_str = "N/A"

                # Get Furniture Mark
                mark_param = inst.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                if mark_param and mark_param.HasValue:
                    furniture_mark = mark_param.AsString()
                    if not furniture_mark: # Handle empty string case
                        furniture_mark = "N/A"
                else:
                    # Check if the instance itself has a Mark property (less common for Mark)
                    if hasattr(inst, 'Mark') and inst.Mark:
                         furniture_mark = inst.Mark
                    else: # If no parameter and no property, mark as N/A
                        furniture_mark = "N/A"

                # Get Family and Type Name
                family_symbol = inst.Symbol
                if family_symbol:
                    type_name = family_symbol.Name
                    # Try getting family name from symbol first, then from family object
                    family_name = "Unknown Family"
                    if hasattr(family_symbol, 'FamilyName') and family_symbol.FamilyName:
                        family_name = family_symbol.FamilyName
                    elif hasattr(family_symbol, 'Family') and family_symbol.Family and hasattr(family_symbol.Family, 'Name'):
                         family_name = family_symbol.Family.Name

                    family_type_name = "{0} / {1}".format(family_name, type_name)
                else:
                    # Fallback using parameters if symbol access fails
                    fam_param = inst.get_Parameter(BuiltInParameter.ELEM_FAMILY_PARAM)
                    type_param = inst.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM)
                    fam_name = fam_param.AsValueString() if fam_param and fam_param.HasValue else "Unknown Family"
                    typ_name = type_param.AsValueString() if type_param and type_param.HasValue else "Unknown Type"
                    family_type_name = "{0} / {1}".format(fam_name, typ_name)

                # Get Element ID
                element_id_str = inst.Id.ToString() # Use ToString for ElementId

                # Escape double quotes for CSV/Excel compatibility and enclose fields in quotes
                safe_mark = '"' + str(furniture_mark).replace('"', '""') + '"'
                safe_family_type = '"' + str(family_type_name).replace('"', '""') + '"'
                safe_elem_id = '"' + element_id_str.replace('"', '""') + '"'

                # Append data row
                csv_lines.append(safe_mark + ',' + safe_family_type + ',' + safe_elem_id)
                processed_count += 1

        except Exception as e:
            # Optional: Print errors during development/debugging
            # print("Error processing Furniture Instance {0}: {1}".format(inst.Id.ToString(), str(e)))
            # Attempt to add an error row
            try:
                 safe_mark_error = '"' + "Error" + '"'
                 safe_family_type_error = '"' + "Error Processing Instance" + '"'
                 safe_elem_id_error = '"' + inst.Id.ToString() + '"'
                 csv_lines.append(safe_mark_error + ',' + safe_family_type_error + ',' + safe_elem_id_error)
            except:
                pass # Ignore if error logging fails

# Check if we gathered any data (more than just the header)
if processed_count > 0:
    # Format the final output for export as Excel (using CSV data)
    file_content = "\n".join(csv_lines)
    print("EXPORT::EXCEL::furniture_without_rooms.xlsx")
    print(file_content)
else:
    # If only the header exists, print a message indicating no relevant furniture was found
    print("# No placed furniture instances found that are not associated with a room.")