# Purpose: This script updates wall descriptions based on type and level from input data.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall, Level, WallType,
    BuiltInParameter, ParameterFilterRuleFactory, ElementParameterFilter,
    LogicalAndFilter, ElementId
)

# --- Input Data ---
# Format: TypeName,LevelName,DescriptionValue
# Assumes LevelName matches the Name property of Level elements.
# Assumes TypeName matches the Name property of WallType elements.
data_string = """TypeName,Level,Description
EXT-MetalPanel,Level 1,Ground Floor Facade
EXT-MetalPanel,Level 2,Upper Facade
INT-CMU,Basement,Basement Partition"""

# --- Configuration ---
description_param_name = "Description" # Standard parameter name
# Using BuiltInParameter as a fallback if LookupParameter fails
description_bip = BuiltInParameter.ALL_MODEL_DESCRIPTION

# --- Helper Functions ---
def parse_data(data_str):
    """Parses the input data string into a list of dictionaries."""
    lines = data_str.strip().split('\n')
    parsed_data = []
    if not lines or len(lines) < 2:
        print("# Warning: Input data string is empty or missing header.")
        return parsed_data

    header = [h.strip() for h in lines[0].split(',')]
    required_headers = ['TypeName', 'Level', 'Description']
    if not all(h in header for h in required_headers):
        print("# Error: Input data header is missing required columns. Expected: {}".format(", ".join(required_headers)))
        return parsed_data # Return empty list on header error

    for i, line in enumerate(lines[1:], 1):
        values = [v.strip() for v in line.split(',')]
        if len(values) == len(header):
            row_dict = dict(zip(header, values))
            # Basic validation
            if not row_dict.get('TypeName') or not row_dict.get('Level') or row_dict.get('Description') is None: # Description can be empty string
                 print("# Warning: Skipping malformed or incomplete data line {}: {}".format(i + 1, line))
                 continue
            parsed_data.append(row_dict)
        else:
            print("# Warning: Skipping malformed data line {}: {}".format(i + 1, line))
    return parsed_data

# --- Script Core Logic ---

# 1. Parse the input data
input_rows = parse_data(data_string)

if not input_rows:
    print("# No valid data rows parsed from input string. Script terminated.")
else:
    # 2. Create Lookups for Levels and WallTypes
    levels_collector = FilteredElementCollector(doc).OfClass(Level)
    level_name_to_id = {lvl.Name: lvl.Id for lvl in levels_collector}

    wall_types_collector = FilteredElementCollector(doc).OfClass(WallType)
    type_name_to_id = {wt.Name: wt.Id for wt in wall_types_collector}

    # 3. Initialize Counters & Logs
    total_rows_processed = 0
    walls_matched_count = 0
    walls_updated_count = 0
    rows_skipped_type_not_found = 0
    rows_skipped_level_not_found = 0
    param_update_errors = 0
    param_not_found_on_wall = set() # Log which walls had missing param by ID
    param_read_only_on_wall = set() # Log which walls had read-only param by ID

    # 4. Iterate through parsed data rows and update walls
    for row_data in input_rows:
        total_rows_processed += 1
        type_name = row_data['TypeName']
        level_name = row_data['Level']
        target_description = row_data['Description']

        # Find target Level and WallType IDs
        target_level_id = level_name_to_id.get(level_name)
        target_type_id = type_name_to_id.get(type_name)

        if not target_level_id:
            print("# Warning: Level '{}' from data row not found in project. Skipping row.".format(level_name))
            rows_skipped_level_not_found += 1
            continue

        if not target_type_id:
            print("# Warning: WallType '{}' from data row not found in project. Skipping row.".format(type_name))
            rows_skipped_type_not_found += 1
            continue

        # Create filters to find matching walls
        try:
            # Filter by Wall Type using ELEM_TYPE_PARAM
            type_rule = ParameterFilterRuleFactory.CreateEqualsRule(ElementId(BuiltInParameter.ELEM_TYPE_PARAM), target_type_id)
            type_filter = ElementParameterFilter(type_rule)

            # Filter by Level using WALL_BASE_CONSTRAINT
            level_rule = ParameterFilterRuleFactory.CreateEqualsRule(ElementId(BuiltInParameter.WALL_BASE_CONSTRAINT), target_level_id)
            level_filter = ElementParameterFilter(level_rule)

            # Combine filters
            combined_filter = LogicalAndFilter(type_filter, level_filter)

            # Find matching walls
            matching_walls_collector = FilteredElementCollector(doc)\
                                       .OfCategory(BuiltInCategory.OST_Walls)\
                                       .WhereElementIsNotElementType()\
                                       .WherePasses(combined_filter)

            # Update the Description parameter for each matching wall
            row_walls_found = 0
            for wall in matching_walls_collector:
                if isinstance(wall, Wall):
                    row_walls_found += 1
                    walls_matched_count += 1
                    try:
                        # Try finding the parameter by name first, then by BuiltInParameter
                        desc_param = wall.LookupParameter(description_param_name)
                        if not desc_param:
                             desc_param = wall.get_Parameter(description_bip)

                        if desc_param:
                            if not desc_param.IsReadOnly:
                                current_value = desc_param.AsString()
                                # Only update if the value is different
                                if current_value != target_description:
                                    # Transaction is handled externally by C# wrapper
                                    desc_param.Set(target_description)
                                    walls_updated_count += 1
                            else:
                                # Parameter is read-only for this wall instance
                                param_read_only_on_wall.add(wall.Id.IntegerValue)
                        else:
                            # Parameter not found on this wall instance
                            param_not_found_on_wall.add(wall.Id.IntegerValue)

                    except Exception as e:
                        print("# Error updating Description for Wall ID {}: {}".format(wall.Id.IntegerValue, repr(e)))
                        param_update_errors += 1

            # Optional: Info message if no walls matched a specific row
            # if row_walls_found == 0:
            #    print("# Info: No walls found matching Type '{}' and Level '{}'.".format(type_name, level_name))

        except Exception as filter_ex:
             print("# Error creating/applying filters for row (Type: '{}', Level: '{}'): {}".format(type_name, level_name, repr(filter_ex)))
             param_update_errors += 1 # Count as a general update error for this row

    # 5. Print Summary
    print("--- Wall Description Update Summary ---")
    print("# Data Rows Processed: {}".format(total_rows_processed))
    print("# Rows Skipped (Level Not Found): {}".format(rows_skipped_level_not_found))
    print("# Rows Skipped (WallType Not Found): {}".format(rows_skipped_type_not_found))
    print("# Total Wall Instances Matched Criteria: {}".format(walls_matched_count))
    print("# Wall Instances Successfully Updated: {}".format(walls_updated_count))
    print("# Parameter Update Errors (Excluding Not Found/Read Only): {}".format(param_update_errors))
    if param_not_found_on_wall:
        print("# 'Description' Parameter Not Found on {} Wall Instance(s) (IDs: {})".format(len(param_not_found_on_wall), ", ".join(map(str, sorted(list(param_not_found_on_wall))))))
    if param_read_only_on_wall:
        print("# 'Description' Parameter Read-Only on {} Wall Instance(s) (IDs: {})".format(len(param_read_only_on_wall), ", ".join(map(str, sorted(list(param_read_only_on_wall))))))