# Purpose: This script adds a comment to mullions hosted on walls with names starting with 'Facade_'.

﻿# Mandatory Imports
import clr
import System # For exception handling
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Mullion,
    Wall,
    CurtainGrid,
    CurtainGridLine,
    Element,
    BuiltInParameter,
    StorageType,
    ElementId # Though not explicitly used for lookup, good practice
)

# Define the comment to add
comment_text = "Exterior Use"
modified_count = 0
error_count = 0
skipped_non_facade_count = 0
skipped_no_host_count = 0
skipped_param_issue_count = 0

# --- Script Core Logic ---

# Collect all Mullion elements in the project
mullion_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType()

# Iterate through each mullion
for mullion in mullion_collector:
    if not isinstance(mullion, Mullion):
        continue

    try:
        # Get the host of the Mullion, which should be a CurtainGridLine
        host_element = None
        curtain_grid = None
        wall_host = None

        # Mullions are hosted on CurtainGridLines
        if mullion.Host and isinstance(mullion.Host, CurtainGridLine):
             grid_line = mullion.Host
             # Get the CurtainGrid from the GridLine
             curtain_grid = grid_line.Grid
             if curtain_grid:
                 # Get the Host of the CurtainGrid (typically the Wall or CurtainSystem)
                 host_element = doc.GetElement(curtain_grid.HostId)

        if host_element and isinstance(host_element, Wall):
            wall_host = host_element
        else:
            # Sometimes the mullion host might be the grid itself? Less common. Check HostId.
            if mullion.HostId != ElementId.InvalidElementId:
                 possible_host = doc.GetElement(mullion.HostId)
                 # If the host is the wall directly (might happen in some modeling cases?)
                 if isinstance(possible_host, Wall):
                     wall_host = possible_host
                 # Or maybe the host is the grid? Check grid's host.
                 elif isinstance(possible_host, CurtainGrid):
                     grid_host_element = doc.GetElement(possible_host.HostId)
                     if isinstance(grid_host_element, Wall):
                         wall_host = grid_host_element

        # If we couldn't find a hosting Wall, skip this mullion
        if not wall_host:
            skipped_no_host_count += 1
            continue

        # Check if the hosting Wall's name starts with "Facade_"
        wall_name = wall_host.Name
        if wall_name.StartsWith("Facade_"):
            # Found a mullion on a target wall, now get and set the parameter
            comments_param = mullion.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

            if comments_param and not comments_param.IsReadOnly:
                # Check if the parameter storage type is String
                if comments_param.StorageType == StorageType.String:
                    try:
                        # Set the parameter value
                        comments_param.Set(comment_text)
                        modified_count += 1
                    except Exception as set_ex:
                        # print("# Error setting comments for Mullion ID {}: {}".format(mullion.Id, set_ex)) # Optional debug
                        error_count += 1
                else:
                    # print("# Comments parameter for Mullion ID {} is not a String type.".format(mullion.Id)) # Optional debug
                    skipped_param_issue_count += 1
            else:
                # print("# Comments parameter not found or is read-only for Mullion ID {}.".format(mullion.Id)) # Optional debug
                skipped_param_issue_count += 1
        else:
            # Mullion is on a wall, but not one named "Facade_"
            skipped_non_facade_count += 1

    except System.Exception as ex:
        # Log any unexpected errors during processing
        print("# Error processing Mullion ID {}: {}".format(mullion.Id, ex))
        error_count += 1

# --- Final Report ---
print("# --- Mullion Comment Update Summary ---")
print("# Successfully updated comments for {} mullions.".format(modified_count))
# print("# Skipped {} mullions not hosted on walls named 'Facade_*'.".format(skipped_non_facade_count)) # Optional info
# print("# Skipped {} mullions where a hosting Wall could not be determined.".format(skipped_no_host_count)) # Optional info
# print("# Skipped {} mullions due to issues with the 'Comments' parameter (missing, read-only, or wrong type).".format(skipped_param_issue_count)) # Optional info
if error_count > 0:
    print("# Encountered {} errors during processing.".format(error_count))