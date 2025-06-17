# Purpose: This script extracts and calculates the total length of each wall type in a Revit model and outputs the data to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, WallType, Wall, BuiltInCategory, BuiltInParameter, ElementId

# Initialize dictionary to store data: {WallTypeId: [Name, TotalLength]}
wall_type_data = {}

# Collect all Wall Types and initialize data
wall_type_collector = FilteredElementCollector(doc).OfClass(WallType)
for wt in wall_type_collector:
    if isinstance(wt, WallType):
        # Ensure the type ID isn't already added (though OfClass should be unique types)
        if wt.Id not in wall_type_data:
            wall_type_data[wt.Id] = [wt.Name, 0.0] # Store Name and initialize length to 0.0 feet

# Collect all Wall instances
wall_instance_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

# Iterate through instances and aggregate lengths
for wall in wall_instance_collector:
    if isinstance(wall, Wall):
        try:
            wall_type_id = wall.WallTypeId
            length_param = wall.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)

            # Check if the type exists in our dictionary and length parameter is valid
            if wall_type_id in wall_type_data and length_param and length_param.HasValue:
                length = length_param.AsDouble() # Length is in internal units (decimal feet)
                wall_type_data[wall_type_id][1] += length # Add length to the specific type
        except Exception as e:
            # Optional: Log errors for specific walls if needed for debugging
            # print("# Error processing Wall {}: {}".format(wall.Id, e))
            pass # Silently skip walls that cause errors or don't have the parameter

# Format for CSV output
csv_lines = []
# Add header row
csv_lines.append('"Wall Type Name","Total Length (ft)"')

# Iterate through the collected data sorted by Wall Type Name for consistent output
# Sorting requires converting dictionary items to a list and sorting by name (index 0 of the value list)
sorted_wall_type_data = sorted(wall_type_data.items(), key=lambda item: item[1][0])

for type_id, data in sorted_wall_type_data:
    name = data[0]
    total_length = data[1]

    # Escape quotes in name for CSV safety
    safe_name = '"' + name.replace('"', '""') + '"'
    # Format length to 2 decimal places
    length_str = "{:.2f}".format(total_length)

    csv_lines.append(','.join([safe_name, length_str]))

# Print Export block
if len(csv_lines) > 1: # Check if any data was added beyond the header
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::wall_type_total_lengths.csv")
    print(file_content)
else:
    # This message covers cases where no WallTypes exist or no Wall Instances exist
    print("# No Wall Types or Wall Instances found/processed in the project.")