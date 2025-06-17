# Purpose: This script exports a list of all placed rooms in the project to an Excel file (CSV format).

import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # For String formatting and Math

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, Level, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB.Architecture import Room # Room class is in the Architecture namespace
import System

# List to hold CSV lines (for Excel export)
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
                     val_str = str(param.AsDouble())
                 elif storage_type == System.StorageType.Integer:
                     val_str = str(param.AsInteger())
                 elif storage_type == System.StorageType.String:
                      val_str = param.AsString() # Re-try AsString for explicit String storage
                 elif storage_type == System.StorageType.ElementId:
                      element_id = param.AsElementId()
                      if element_id is not None and element_id != ElementId.InvalidElementId:
                          related_element = doc.GetElement(element_id)
                          if related_element:
                              val_str = related_element.Name # Often more useful than just the ID
                          else:
                              val_str = element_id.ToString() # Fallback to ID string
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
            # Area is in Revit's internal units (square feet)
            area_internal = room.Area
            # Only process rooms with a non-negligible area (i.e., placed rooms)
            if area_internal > 1e-6:
                # --- Get Level Name ---
                level_name = "N/A"
                level_id = room.LevelId # Use LevelId first as Level property might be null sometimes
                if level_id is not None and level_id != ElementId.InvalidElementId:
                    level_element = doc.GetElement(level_id)
                    if isinstance(level_element, Level):
                        level_name = level_element.Name
                        if not level_name or level_name == "":
                            level_name = "Unnamed Level (ID: {0})".format(level_id.ToString())
                    else:
                        level_name = "Invalid Level Element (ID: {0})".format(level_id.ToString())
                else:
                    # Fallback using Level property if LevelId is invalid
                    level_prop = room.Level
                    if level_prop and isinstance(level_prop, Level):
                         level_name = level_prop.Name
                         if not level_name or level_name == "":
                             level_name = "Unnamed Level (ID: {0})".format(level_prop.Id.ToString())
                    else:
                        level_name = "No Associated Level"


                # --- Get Room Number ---
                number = get_parameter_value_string(room, BuiltInParameter.ROOM_NUMBER, "N/A")

                # --- Get Room Name ---
                # Use Element.Name first, as it's often the primary name for Rooms
                name = element.Name
                if not name or name == "":
                    # Fallback to the Room Name parameter if Element.Name is empty
                    name = get_parameter_value_string(room, BuiltInParameter.ROOM_NAME, "Unnamed Room (ID: {0})".format(room.Id.ToString()))


                # --- Get Area ---
                # Area is already retrieved (in internal units, square feet)
                area_str = System.String.Format("{0:.2f}", area_internal)

                # --- Get Perimeter ---
                # Perimeter is in Revit's internal units (feet)
                perimeter_internal = get_parameter_value_double(room, BuiltInParameter.ROOM_PERIMETER, 0.0)
                perimeter_str = System.String.Format("{0:.2f}", perimeter_internal)

                # --- Get Volume ---
                # Volume is in Revit's internal units (cubic feet)
                # Note: Volume computation must be enabled in Revit settings for this to work reliably
                volume_internal = room.Volume # Direct property access
                if volume_internal is not None and abs(volume_internal) > 1e-6:
                    volume_str = System.String.Format("{0:.2f}", volume_internal)
                else:
                     # Check parameter as fallback or if Volume property is 0/None
                     volume_param_val = get_parameter_value_double(room, BuiltInParameter.ROOM_VOLUME, 0.0)
                     if abs(volume_param_val) > 1e-6:
                         volume_str = System.String.Format("{0:.2f}", volume_param_val)
                     else:
                         volume_str = "N/A (Check Volume Computations)" # Indicate potential issue


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
    # Format the final output for export as CSV (Excel compatible)
    file_content = "\n".join(csv_lines)
    # Indicate EXCEL format, suggest .xlsx extension. Data is CSV formatted.
    print("EXPORT::EXCEL::all_rooms_report.xlsx")
    print(file_content)
else:
    # If only the header exists, print a message indicating no rooms were found/processed
    print("# No placed room elements found or processed in the project.")