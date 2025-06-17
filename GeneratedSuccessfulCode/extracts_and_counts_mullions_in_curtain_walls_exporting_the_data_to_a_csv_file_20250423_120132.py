# Purpose: This script extracts and counts mullions in curtain walls, exporting the data to a CSV file.

﻿import clr
clr.AddReference('System.Collections') # Required for ICollection
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall, CurtainGrid,
    ElementId, BuiltInParameter, Element
)
from System.Collections.Generic import ICollection # Explicit import

# --- Helper Functions ---
def format_csv_value(value):
    """Formats a value for CSV, quoting if necessary and escaping quotes."""
    str_val = str(value)
    # Escape double quotes within the string
    escaped_val = str_val.replace('"', '""')
    # Enclose in double quotes if it contains comma, double quote, or newline
    if ',' in escaped_val or '"' in escaped_val or '\n' in escaped_val or '\r' in escaped_val:
        return '"' + escaped_val + '"'
    else:
        return escaped_val

def get_wall_identifier(wall_element):
    """Gets the Mark parameter value, or falls back to Element ID."""
    if not wall_element:
        return "N/A"
    identifier = "N/A"
    try:
        # Try getting the Mark parameter
        mark_param = wall_element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
        if mark_param and mark_param.HasValue:
            mark_value = mark_param.AsString()
            # Check if mark is not None and not just whitespace
            if mark_value and mark_value.strip():
                identifier = mark_value.strip()
            else:
                # Mark parameter exists but is empty, use ID as fallback
                identifier = "ID:{}".format(wall_element.Id.IntegerValue)
        else:
            # Mark parameter doesn't exist or has no value, use ID
            identifier = "ID:{}".format(wall_element.Id.IntegerValue)
    except Exception:
        # Error retrieving Mark, fallback to ID
        try:
            identifier = "ID:{}".format(wall_element.Id.IntegerValue)
        except:
             identifier = "ErrorGettingID" # Should not happen but safe fallback
    return identifier

# --- Main Logic ---

# List to hold CSV lines
csv_lines = []
# Define headers
headers = ["Curtain Wall Identifier", "Mullion Count"]
csv_lines.append(",".join([format_csv_value(h) for h in headers]))

# Collect all Wall elements that are not element types
wall_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

processed_curtain_walls = 0

# Iterate through collected walls
for wall in wall_collector:
    # Ensure it's a Wall instance (redundant due to filter, but safe)
    if not isinstance(wall, Wall):
        continue

    curtain_grid = None
    try:
        # Accessing CurtainGrid property confirms it's a curtain wall type
        # If it's not a curtain wall, accessing this will likely raise an exception or return None
        curtain_grid = wall.CurtainGrid
    except Exception:
        # Not a curtain wall or error accessing property, skip this wall
        continue

    # Proceed only if we successfully got a CurtainGrid object
    if curtain_grid:
        processed_curtain_walls += 1
        wall_identifier = get_wall_identifier(wall)
        mullion_count = 0
        try:
            # GetMullionIds includes both locked and unlocked mullions
            mullion_ids = curtain_grid.GetMullionIds()
            if mullion_ids is not None:
                mullion_count = mullion_ids.Count
        except Exception as e_mullion:
            # Log error internally if needed, but report count as 0 for the summary
            mullion_count = 0 # Default to 0 on error
            # print("# Warning: Could not retrieve mullions for Wall '{}'. Error: {}".format(wall_identifier, e_mullion))

        # Create row data
        row_data = [wall_identifier, mullion_count]
        csv_lines.append(",".join([format_csv_value(d) for d in row_data]))

# --- Output Preparation ---
if processed_curtain_walls > 0:
    # Combine all lines into a single string for export
    csv_data_string = "\n".join(csv_lines)
    output_filename = "curtain_wall_mullion_summary.csv"
    # Print the export marker and data
    print("EXPORT::CSV::{}".format(output_filename))
    print(csv_data_string)
else:
    # No curtain walls found or processed
    print("# No Curtain Wall instances with accessible Curtain Grids found in the document.")