# Purpose: This script extracts room numbers, names, and intersecting furniture marks to a CSV format.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # For potential future use, though Python join is sufficient
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, SpatialElementGeometryCalculator,
    SpatialElementBoundaryOptions, ElementIntersectsSolidFilter, FamilyInstance,
    BuiltInParameter, ElementId, Solid, Options, ForgeTypeId
)
from Autodesk.Revit.DB.Architecture import Room # Explicit import

# --- Configuration ---
FURNITURE_MARK_SEPARATOR = "; " # Separator for concatenated marks

# --- Collect Data ---
csv_lines = []
# Add header row - Ensure correct parameter names are referenced if different from standard
csv_lines.append('"Room Number","Room Name","Furniture Marks"')

# Collect all Furniture elements once
furniture_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType()
all_furniture = list(furniture_collector) # Convert to list for efficient filtering per room

# Collect all placed Room elements
room_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()
placed_rooms = [r for r in room_collector if isinstance(r, Room) and r.Area > 0 and r.Location is not None and r.LevelId != ElementId.InvalidElementId]

# Initialize Geometry Calculator
calculator = None
try:
    # Use default options, usually sufficient for room geometry
    # calc_options = SpatialElementBoundaryOptions() # Example if specific options needed
    calculator = SpatialElementGeometryCalculator(doc)
except Exception as calc_init_e:
    print("# Error: Could not initialize SpatialElementGeometryCalculator: {}".format(calc_init_e))
    # Script will likely fail below or produce no results if calculator is None

# --- Process Rooms ---
if calculator and placed_rooms: # Proceed only if calculator is ready and rooms exist
    processed_room_count = 0
    for room in placed_rooms:
        room_number = "N/A"
        room_name = "N/A"
        furniture_marks_list = []

        try:
            # Get Room Number
            # Try standard parameter first
            num_param = room.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if num_param and num_param.HasValue:
                room_number = num_param.AsString()
            elif hasattr(room, 'Number'): # Fallback to Number property
                 room_number = room.Number
            else: # Fallback using ForgeTypeId if available (Revit 2022+)
                try:
                    room_num_param_id = ParameterTypeId.ElemRoomNumber
                    num_param_forge = room.get_Parameter(room_num_param_id)
                    if num_param_forge and num_param_forge.HasValue:
                        room_number = num_param_forge.AsString()
                except AttributeError: # ParameterTypeId not available in older Revit API versions
                    pass # Keep "N/A"

            # Get Room Name
            # Try standard parameter first
            name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
            if name_param and name_param.HasValue:
                room_name = name_param.AsString()
            elif hasattr(room, 'Name'): # Fallback to Name property
                 room_name = room.Name
            else: # Fallback using ForgeTypeId if available (Revit 2022+)
                 try:
                    room_name_param_id = ParameterTypeId.ElemRoomName
                    name_param_forge = room.get_Parameter(room_name_param_id)
                    if name_param_forge and name_param_forge.HasValue:
                        room_name = name_param_forge.AsString()
                 except AttributeError:
                     pass # Keep "N/A"

            # If name is still N/A or empty, use Element ID as fallback identifier
            if not room_name or room_name == "N/A":
                 room_name = "Room ID: {}".format(room.Id.ToString())
            if not room_number or room_number == "N/A":
                 room_number = "N/A" # Keep N/A if number truly not found

            # Calculate Room Geometry Solid
            room_solid = None
            try:
                geo_results = calculator.CalculateSpatialElementGeometry(room)
                # Check if GetGeometry returns a valid Solid object
                temp_solid = geo_results.GetGeometry()
                if isinstance(temp_solid, Solid) and temp_solid.Volume > 1e-6:
                    room_solid = temp_solid
                #else:
                     # print("# Debug: Room {} ({}) has no valid solid geometry.".format(room.Id, room_name)) # Optional debug
            except Exception as geo_ex:
                # print("# Error calculating geometry for Room {} ({}): {}".format(room.Id, room_name, geo_ex)) # Optional debug
                room_solid = None

            # Find Furniture intersecting the room solid
            if room_solid and all_furniture: # Proceed only if solid exists and furniture list isn't empty
                try:
                    # Create the intersection filter
                    intersects_filter = ElementIntersectsSolidFilter(room_solid)

                    # Apply the filter to the pre-collected furniture list
                    intersecting_furniture = [furn for furn in all_furniture if intersects_filter.PassesFilter(furn)]

                    for furniture in intersecting_furniture:
                         # Verify it's a type that can have a Mark (e.g., FamilyInstance)
                         if isinstance(furniture, FamilyInstance):
                             mark_param = furniture.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                             if mark_param and mark_param.HasValue:
                                 mark_value = mark_param.AsString()
                                 # Add mark only if it's not None and not just whitespace
                                 if mark_value and mark_value.strip():
                                     furniture_marks_list.append(mark_value.strip())

                except Exception as filter_ex:
                     # print("# Error filtering/processing furniture for Room {} ({}): {}".format(room.Id, room_name, filter_ex)) # Optional debug
                     furniture_marks_list.append("Furniture Check Error") # Indicate error in output

            # If no solid was found, indicate that furniture couldn't be checked
            elif not room_solid and all_furniture:
                 furniture_marks_list.append("Room Geometry Error")
            elif not all_furniture:
                 # No furniture in the project, so list is empty - do nothing, mark string will be empty
                 pass


            processed_room_count += 1
        except Exception as room_proc_ex:
             # print("# Error processing Room {}: {}".format(room.Id, room_proc_ex)) # Optional debug
             # Ensure safe default values if error occurred mid-processing
             room_number = room_number if room_number != "N/A" else "Error"
             room_name = room_name if room_name != "N/A" else "Error Processing Room {}".format(room.Id)
             furniture_marks_list = ["Room Processing Error"] # Indicate error in output

        # Concatenate marks using the defined separator
        concatenated_marks = FURNITURE_MARK_SEPARATOR.join(furniture_marks_list)

        # Escape quotes for CSV safety and enclose in quotes
        safe_room_number = '"' + str(room_number).replace('"', '""') + '"'
        safe_room_name = '"' + str(room_name).replace('"', '""') + '"'
        safe_marks = '"' + concatenated_marks.replace('"', '""') + '"'

        # Append data row
        csv_lines.append(','.join([safe_room_number, safe_room_name, safe_marks]))

# --- Export Results ---
if len(csv_lines) > 1: # More than just the header means some rooms were processed
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::room_furniture_marks.csv")
    print(file_content)
elif not calculator:
    # Error message already printed during initialization attempt
     print("# INFO: Script halted due to SpatialElementGeometryCalculator initialization failure.")
elif not placed_rooms:
    print("# INFO: No placed Room elements found in the project.")
elif processed_room_count == 0 and placed_rooms:
     print("# INFO: Placed rooms were found, but none could be processed successfully. Check logs or room/furniture data.")
else: # Header exists, but no data rows were added (e.g., rooms processed but had no furniture or geometry)
     # This case might indicate successful processing but no relevant data found.
     # An export with only headers might still be desired, or a message. Let's provide a message.
     print("# INFO: No furniture marks found for the processed rooms, or rooms lacked geometry. Exporting header only.")
     file_content = "\n".join(csv_lines)
     print("EXPORT::CSV::room_furniture_marks.csv")
     print(file_content) # Still export header