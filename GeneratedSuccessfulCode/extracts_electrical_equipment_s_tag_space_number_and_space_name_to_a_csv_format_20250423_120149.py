# Purpose: This script extracts electrical equipment's tag, space number, and space name to a CSV format.

﻿# Import necessary classes
import clr
import System # Required for str() conversion robustness

# Add references to Revit API assemblies
clr.AddReference('RevitAPI')

# Import specific classes from Revit API namespaces
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    BuiltInParameter,
    Parameter # To check if parameter exists
)

# --- Try to load MEP types ---
mep_available = False
Space = None # Define Space as None initially
try:
    clr.AddReference('RevitAPIMep')
    # Import Space class from its correct namespace only if reference is added
    from Autodesk.Revit.DB.Mechanical import Space
    mep_available = True
except Exception as e:
    # Keep mep_available = False. Space lookups will be skipped.
    # print("DEBUG: RevitAPIMep assembly not found or failed to load: {}".format(e)) # Optional debug
    pass

# List to hold CSV data rows (as lists)
csv_data = []
# Add header row
csv_data.append(["Equipment Tag", "Space Number", "Space Name"])

# Helper function for CSV quoting and escaping
def escape_csv(value):
    """Escapes a value for safe inclusion in a CSV cell."""
    if value is None:
        return '""'
    # Ensure value is a string before replacing quotes
    str_value = System.Convert.ToString(value)
    # Replace double quotes with two double quotes and enclose in double quotes
    return '"' + str_value.replace('"', '""') + '"'

# Get the current document
# doc is assumed to be pre-defined

# Collect all Electrical Equipment instances (FamilyInstances)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ElectricalEquipment).WhereElementIsNotElementType()

# Iterate through collected electrical equipment elements
for element in collector:
    # Ensure the element is a FamilyInstance
    if isinstance(element, FamilyInstance):
        instance = element
        equipment_tag = "No Tag"
        space_number = "N/A"
        space_name = "N/A"

        try:
            # 1. Get Equipment Tag (using the 'Mark' parameter)
            tag_param = instance.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            if tag_param and tag_param.HasValue:
                tag_value = tag_param.AsString()
                # Handle potential empty string value from parameter
                if tag_value and tag_value.strip():
                     equipment_tag = tag_value
                # else: keep "No Tag" if parameter exists but is empty/whitespace

            # 2. Get the Space the instance is located in (only if MEP assembly loaded)
            if mep_available and Space is not None:
                space_obj = instance.Space # This property returns a Space object or None

                if space_obj and isinstance(space_obj, Space):
                    # 3. Get Space Number
                    num_param = space_obj.get_Parameter(BuiltInParameter.ROOM_NUMBER)
                    if num_param and num_param.HasValue:
                        space_number_val = num_param.AsString()
                        if space_number_val and space_number_val.strip():
                            space_number = space_number_val
                        else:
                            space_number = "No Number" # Indicate space found but no number
                    else: # Fallback: Try looking up by name "Number"
                        num_param_by_name = space_obj.LookupParameter("Number")
                        if num_param_by_name and num_param_by_name.HasValue:
                             space_number_val = num_param_by_name.AsString()
                             if space_number_val and space_number_val.strip():
                                 space_number = space_number_val
                             else:
                                 space_number = "No Number"
                        else:
                            space_number = "No Number" # Parameter not found

                    # 4. Get Space Name
                    name_param = space_obj.get_Parameter(BuiltInParameter.ROOM_NAME)
                    if name_param and name_param.HasValue:
                         space_name_val = name_param.AsString()
                         if space_name_val and space_name_val.strip():
                             space_name = space_name_val
                         else:
                             space_name = "No Name" # Indicate space found but no name
                    else: # Fallback: Try looking up by name "Name"
                        name_param_by_name = space_obj.LookupParameter("Name")
                        if name_param_by_name and name_param_by_name.HasValue:
                             space_name_val = name_param_by_name.AsString()
                             if space_name_val and space_name_val.strip():
                                 space_name = space_name_val
                             else:
                                 space_name = "No Name"
                        else:
                             space_name = "No Name" # Parameter not found
                else:
                    # Instance is not located within a Space boundary
                    space_number = "Not in Space"
                    space_name = "Not in Space"
            elif not mep_available:
                # MEP types could not be loaded, indicate this
                space_number = "MEP N/A"
                space_name = "MEP N/A"
            # else: Instance not in a space (handled above) or other issue

            # Append data row to the list
            csv_data.append([equipment_tag, space_number, space_name])

        except Exception as e:
            # Try to get an identifier for the element that caused the error
            err_tag = "Unknown"
            try:
                tag_param = instance.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                if tag_param and tag_param.HasValue:
                   err_tag_val = tag_param.AsString()
                   if err_tag_val and err_tag_val.strip():
                       err_tag = err_tag_val
                   else: # Tag exists but is empty
                       err_tag = "ID:{}".format(instance.Id.ToString())
                else: # No Tag parameter
                   err_tag = "ID:{}".format(instance.Id.ToString())
            except:
                 err_tag = "ID:{}".format(instance.Id.ToString()) # Fallback if parameter access fails
            # Log the error row in the CSV data
            csv_data.append([err_tag, "Error", System.Convert.ToString(e)]) # Ensure error message is string

# Format the collected data (including header) into a CSV string
csv_lines = []
for row in csv_data:
    escaped_row = [escape_csv(cell) for cell in row]
    csv_lines.append(",".join(escaped_row))

# Join all rows with newline characters
file_content = "\n".join(csv_lines)

# Print the export header and the CSV content using the required format
# This will print the header even if no data rows were added (len(csv_data) == 1)
print("EXPORT::CSV::electrical_equipment_space_report.csv")
print(file_content)