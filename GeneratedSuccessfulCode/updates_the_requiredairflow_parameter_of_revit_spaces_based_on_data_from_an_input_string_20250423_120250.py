# Purpose: This script updates the 'RequiredAirflow' parameter of Revit spaces based on data from an input string.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Level, ElementId, StorageType
from Autodesk.Revit.DB.Mechanical import Space # Correct namespace for Space
import System

# --- Parameter Configuration ---
# The name of the parameter to update.
target_parameter_name = "RequiredAirflow" # Assumes this Project/Shared parameter exists and is numeric

# --- Input Data ---
# Format: Level,Number,RequiredAirflow
input_data = """Level,Number,RequiredAirflow
Level 1,MECH-101,500
Level 1,ELEC-102,100
Level 2,DATA-201,1200"""

# --- Data Parsing ---
lines = input_data.strip().split('\n')
if not lines or len(lines) < 2:
     raise System.Exception("Input data missing or invalid.")

header = [h.strip() for h in lines[0].split(',')]
data_rows = []
try:
    data_rows = [dict(zip(header, [val.strip() for val in line.split(',', 2)])) for line in lines[1:]]
except Exception as parse_error:
    raise System.Exception("Input data parsing failed: " + str(parse_error))


# --- Level Collection ---
levels_by_name = {level.Name: level for level in FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()}

# --- Space Collection ---
spaces_by_level_and_number = {}
space_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MEPSpaces).WhereElementIsNotElementType()

for element in space_collector:
    # Ensure the element is a Space and is placed (has a location)
    if isinstance(element, Space) and element.Location is not None:
        space = element
        level_name = None
        space_number = None
        try:
            # Get Space Number (Uses the same BuiltInParameter as Room Number)
            num_param = space.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if num_param and num_param.HasValue:
                space_number = num_param.AsString()

            # Get Level Name
            level_prop = space.Level # Preferred method
            if level_prop:
                level_name = level_prop.Name
            else:
                # Fallback if Level property is null (less common for placed spaces)
                level_id_param = space.get_Parameter(BuiltInParameter.SPACE_LEVEL_ID) # Correct BuiltInParameter for Space Level ID
                if level_id_param and level_id_param.HasValue:
                     level_id = level_id_param.AsElementId()
                     if level_id != ElementId.InvalidElementId:
                         level_element = doc.GetElement(level_id)
                         if isinstance(level_element, Level):
                             level_name = level_element.Name

            # Add to dictionary if we got both level name and space number
            if level_name and space_number:
                lookup_key = (level_name.strip(), space_number.strip())
                spaces_by_level_and_number[lookup_key] = space

        except Exception as e:
            # Optional: Log errors for spaces that couldn't be processed
            # print("# Error processing space {}: {}".format(element.Id.ToString(), str(e)))
            pass # Continue processing other spaces

# --- Update Space Parameters ---
updated_count = 0
not_found_count = 0
param_not_found_count = 0
param_read_only_count = 0
param_wrong_type_count = 0
value_error_count = 0
level_not_found_count = 0
error_count = 0

for row_data in data_rows:
    target_level_name = row_data.get('Level')
    target_number = row_data.get('Number')
    new_airflow_str = row_data.get('RequiredAirflow')

    if not target_level_name or not target_number or new_airflow_str is None:
        # print("# Skipping row with missing data: {}".format(str(row_data)))
        error_count += 1
        continue

    # Check if the level exists in the project dictionary
    if target_level_name not in levels_by_name:
        # print("# Level '{}' specified in data not found in the project.".format(target_level_name))
        level_not_found_count += 1
        continue

    # Try converting airflow value to float
    try:
        # Revit API expects airflow in internal units (typically CFM).
        # Assume input data is already in the correct units (e.g., CFM).
        # Use UnitUtils.ConvertToInternalUnits if conversion from display units is needed.
        new_airflow_value = float(new_airflow_str)
    except ValueError:
        # print("# Error: Invalid numeric value '{}' for Space '{}' on Level '{}'.".format(new_airflow_str, target_number, target_level_name))
        value_error_count += 1
        continue

    lookup_key = (target_level_name, target_number)

    if lookup_key in spaces_by_level_and_number:
        space_to_update = spaces_by_level_and_number[lookup_key]
        try:
            # Find the target parameter by name
            airflow_param = space_to_update.LookupParameter(target_parameter_name)

            if airflow_param:
                if not airflow_param.IsReadOnly:
                    # Check if the parameter type is suitable for a number (Double)
                    if airflow_param.StorageType == StorageType.Double:
                        # Set the parameter value. Assumes the input value is already in Revit's internal units.
                        airflow_param.Set(new_airflow_value)
                        updated_count += 1
                    else:
                        # print("# Warning: Parameter '{}' is not numeric (Double) for Space '{}' on Level '{}'.".format(target_parameter_name, target_number, target_level_name))
                        param_wrong_type_count += 1
                else:
                    # print("# Warning: Parameter '{}' is read-only for Space '{}' on Level '{}'.".format(target_parameter_name, target_number, target_level_name))
                    param_read_only_count += 1
            else:
                # print("# Warning: Parameter '{}' not found for Space '{}' on Level '{}'.".format(target_parameter_name, target_number, target_level_name))
                param_not_found_count += 1

        except Exception as ex:
            # print("# Error updating Space '{}' on Level '{}': {}".format(target_number, target_level_name, str(ex)))
            error_count += 1
    else:
        # print("# Space with Number '{}' on Level '{}' not found or not placed.".format(target_number, target_level_name))
        not_found_count += 1

# --- Output Summary ---
total_issues = not_found_count + level_not_found_count + param_not_found_count + param_read_only_count + param_wrong_type_count + value_error_count + error_count
if updated_count > 0:
    print("# Successfully updated {} space(s). Issues encountered: {}".format(updated_count, total_issues))
elif total_issues > 0:
     print("# No spaces were updated. Found issues: Not Found={}, Level Not Found={}, Param Not Found={}, Param ReadOnly={}, Param WrongType={}, Invalid Value={}, Other Errors={}".format(not_found_count, level_not_found_count, param_not_found_count, param_read_only_count, param_wrong_type_count, value_error_count, error_count))
else:
     print("# No matching spaces found or no valid data rows provided for update.")