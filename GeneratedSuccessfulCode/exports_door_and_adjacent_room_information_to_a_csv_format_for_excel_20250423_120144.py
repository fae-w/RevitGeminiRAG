# Purpose: This script exports door and adjacent room information to a CSV format for Excel.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, FamilyInstance, Phase
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System # For string formatting

# List to hold CSV lines (for Excel export)
csv_lines = []
# Add header row
csv_lines.append('"Door Mark","To Room Number","To Room Name","From Room Number","From Room Name"')

# Function to safely get parameter value as string, handling None parameters/values
def get_parameter_value_string(element, built_in_param, default="N/A"):
    param = element.get_Parameter(built_in_param)
    if param and param.HasValue:
        # Try AsValueString first, then AsString
        val_str = param.AsValueString()
        if val_str is None:
            val_str = param.AsString()
        return val_str if val_str else default
    return default

# Function to safely get room info
def get_room_info(room):
    if room and isinstance(room, Room):
        # Get Room Number
        number = get_parameter_value_string(room, BuiltInParameter.ROOM_NUMBER, "N/A")

        # Get Room Name using the Name property first, fallback to parameter
        name = room.Name
        if not name or name == "":
             name = get_parameter_value_string(room, BuiltInParameter.ROOM_NAME, "Unnamed")

        return number, name
    else:
        return "N/A", "N/A"

# Function to escape quotes for CSV
def escape_csv(value):
    if value is None:
        return '""'
    # Ensure value is string, replace double quotes with two double quotes, and enclose in double quotes
    return '"' + str(value).replace('"', '""') + '"'

# Collect all Door elements
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

# Determine the phase to use (typically the last phase is 'New Construction')
# If doc.Phases is empty or causes issues, default to None or handle error
current_phase = None
if doc.Phases and doc.Phases.Size > 0:
    # Using the last phase in the project
    current_phase = doc.Phases.get_Item(doc.Phases.Size - 1)
else:
    # If no phases, maybe log a warning or use a specific phase known to exist
    # For this script, we'll proceed assuming phase is not strictly needed or will default appropriately
    # Note: get_ToRoom/get_FromRoom *require* a Phase argument.
    # If no phases exist, this script part will fail. Let's raise an error comment
    print("# Error: Could not determine a valid Phase. Door to/from Room relationships depend on Phases.")
    # We will let the script proceed and likely fail later if current_phase remains None, or handle None inside loop

processed_count = 0
if current_phase: # Only proceed if we found a phase
    for element in collector:
        if isinstance(element, FamilyInstance):
            door = element
            try:
                # Get Door Mark
                door_mark = get_parameter_value_string(door, BuiltInParameter.ALL_MODEL_MARK, "N/A")

                # Get To Room and its info
                to_room = door.get_ToRoom(current_phase) # Requires Phase
                to_room_number, to_room_name = get_room_info(to_room)

                # Get From Room and its info
                from_room = door.get_FromRoom(current_phase) # Requires Phase
                from_room_number, from_room_name = get_room_info(from_room)

                # Add row to CSV lines, escaping fields
                csv_line = ",".join([
                    escape_csv(door_mark),
                    escape_csv(to_room_number),
                    escape_csv(to_room_name),
                    escape_csv(from_room_number),
                    escape_csv(from_room_name)
                ])
                csv_lines.append(csv_line)
                processed_count += 1
            except Exception as e:
                # Optional: Print errors for debugging
                # print("Error processing door {}: {}".format(door.Id.ToString(), e)) # Use standard string formatting
                pass # Silently skip doors that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final output for export as CSV (Excel compatible)
    file_content = "\n".join(csv_lines)
    # Indicate EXCEL format, suggest .xlsx extension. Data is CSV formatted.
    print("EXPORT::EXCEL::door_room_report.xlsx")
    print(file_content)
elif not current_phase:
    # Message already printed about missing phase
    pass
else:
    # If only the header exists, print a message indicating no doors were found/processed
    print("# No door elements found or processed.")