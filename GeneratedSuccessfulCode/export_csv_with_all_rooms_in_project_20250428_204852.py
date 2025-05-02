# Purpose: This script exports a list of all placed rooms in the project to a CSV file.

import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # For String formatting and Math

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, Level, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System

# List to hold CSV lines
csv_lines = []
# Add header row - including common room parameters
csv_lines.append('"Level","Room Number","Room Name","Area (sq ft)","Perimeter (ft)","Volume (cu ft)"')

# Function to safely get parameter value as string, handling None parameters/values
def get_parameter_value_string(element, built_in_param, default="N/A"):
    param = element.get_Parameter(built_in_param)
    if param and param.HasValue:
        # Use AsString() which usually gives a formatted value based on project units
        val_str = param.AsString()
        # If AsString returns None or empty, try AsValueString (often better for things like family/type names)
        if val_str is None or val_str == "":
            val_str = param.AsValueString()
        # Final fallback to raw value as string if others fail
        if val_str is None or val_str == "":
             try:
                 # Attempt to get the value in a suitable format and convert to string
                 storage_type = param.StorageType
                 if storage_type == System.StorageType.Double:
                     # Format double values consistently before converting to string
                     val_str = System.String.Format("{0:.2f}", param.AsDouble())
                 elif storage_type == System.StorageType.Integer:
                     val_str = str(param.AsInteger())
                 elif storage_type == System.StorageType.String:
                      val_str = param.AsString() # Re-try AsString for explicit String storage
                 elif storage_type == System.StorageType.ElementId:
                      element_id = param.AsElementId()
                      if element_id is not None and element_id != ElementId.InvalidElementId:
                          # Try getting the element name if it's an ElementId
                          linked_element = doc.GetElement(element_id)
                          if linked_element:
                              val_str = linked_element.Name
                          else:
                              val_str = element_id.ToString()
                      else:
                          val_str = default
                 else:
                     val_str = default # Cannot determine type or value easily
             except Exception:
                 val_str = default # If conversion fails
        return val_str if val_str else default # Return the found string or default
    return default

# Function to safely get parameter value as double, handling None parameters/values
def get_parameter_value_double(element, built_in_param, default=0.0):
    param = element.get_Parameter(built_in_param)
    if param and param.HasValue:
        try:
            return param.AsDouble()
        except Exception:
            return default # In case AsDouble fails for some reason
    return default

# Function to escape quotes for CSV
def escape_csv(value):
    if value is None:
        return '""'
    # Ensure value is string, replace double quotes with two double quotes, and enclose in double quotes
    return '"' + str(value).replace('"', '""') + '"'

# Collect all Room elements
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType()

processed_count = 0
for element in collector:
    # Ensure the element is a Room
    if isinstance(element, Room):
        room = element
        try:
            # Use the Area property from SpatialElement to check if room is placed
            # Unplaced rooms have Area = 0 or very close to 0.
            area_internal = room.Area
            # Only process rooms with a non-negligible area (i.e., placed rooms)
            if area_internal > 1e-6:
                # --- Get Level Name ---
                level_name = "N/A"
                level_obj = None
                # Prefer Level property if available
                try:
                    level_obj = room.Level
                except Exception: # Sometimes accessing Level can fail
                    level_obj = None

                if level_obj and isinstance(level_obj, Level):
                    level_name = level_obj.Name
                    if not level_name:
                        level_name = "Unnamed Level (ID: {0})".format(level_obj.Id.ToString())
                else:
                    # Fallback using LevelId if Level property is null or invalid
                    level_id = room.LevelId
                    if level_id is not None and level_id != ElementId.InvalidElementId:
                        level_element = doc.GetElement(level_id)
                        if isinstance(level_element, Level):
                            level_name = level_element.Name
                            if not level_name:
                                level_name = "Unnamed Level (ID: {0})".format(level_id.ToString())
                        else:
                            level_name = "Invalid Level Element (ID: {0})".format(level_id.ToString())
                    else:
                        level_name = "No Associated Level"

                # --- Get Room Number ---
                number = get_parameter_value_string(room, BuiltInParameter.ROOM_NUMBER, "N/A")

                # --- Get Room Name ---
                # Use Element.Name first, as it's often the primary name for Rooms
                name = element.Name
                if not name:
                    # Fallback to the Room Name parameter if Element.Name is empty
                    name = get_parameter_value_string(room, BuiltInParameter.ROOM_NAME, "Unnamed Room (ID: {0})".format(room.Id.ToString()))


                # --- Get Area ---
                # Area is already retrieved (in internal units, square feet)
                area_str = System.String.Format("{0:.2f}", area_internal)

                # --- Get Perimeter ---
                perimeter_internal = get_parameter_value_double(room, BuiltInParameter.ROOM_PERIMETER, 0.0)
                perimeter_str = System.String.Format("{0:.2f}", perimeter_internal)

                # --- Get Volume ---
                # Note: Volume computation must be enabled in Revit settings for this to work
                volume_internal = 0.0
                try:
                    # Access Volume property, handle potential exceptions
                    volume_internal = room.Volume if room.Volume is not None else 0.0
                except Exception:
                     volume_internal = 0.0 # Set to 0 if property access fails

                if abs(volume_internal) > 1e-6:
                    volume_str = System.String.Format("{0:.2f}", volume_internal)
                else:
                     # Check parameter as fallback or if Volume property is 0/None/Error
                     volume_param_val = get_parameter_value_double(room, BuiltInParameter.ROOM_VOLUME, 0.0)
                     if abs(volume_param_val) > 1e-6:
                         volume_str = System.String.Format("{0:.2f}", volume_param_val)
                     else:
                         volume_str = "N/A (Check Vol Computations)" # Indicate potential issue


                # Add row to CSV lines, escaping fields
                csv_line = ",".join([
                    escape_csv(level_name),
                    escape_csv(number),
                    escape_csv(name),
                    escape_csv(area_str),
                    escape_csv(perimeter_str),
                    escape_csv(volume_str)
                ])
                csv_lines.append(csv_line)
                processed_count += 1
        except Exception as e:
            # Optional: Print errors for debugging in RevitPythonShell or pyRevit console
            # print("Error processing room {0}: {1}".format(element.Id.ToString(), e))
            pass # Silently skip rooms that cause errors

# Check if we gathered any data
if processed_count > 0:
    # Format the final output for export as CSV
    file_content = "\n".join(csv_lines)
    # Indicate CSV format, suggest .csv extension.
    print("EXPORT::CSV::all_rooms_report.csv")
    print(file_content)
else:
    # If only the header exists, print a message indicating no rooms were found/processed
    print("# No placed room elements found or processed in the project.")