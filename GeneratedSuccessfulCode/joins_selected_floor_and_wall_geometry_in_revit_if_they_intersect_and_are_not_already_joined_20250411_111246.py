# Purpose: This script joins selected floor and wall geometry in Revit if they intersect and are not already joined.

# Purpose: This script joins the geometry of selected floors and walls in Revit if they are not already joined and intersect.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    Element,
    Floor,
    Wall,
    JoinGeometryUtils,
    ElementId
)
# No System imports needed for this specific script

# Get selected element IDs
selection_ids = uidoc.Selection.GetElementIds()

if not selection_ids or selection_ids.Count == 0:
    print("# No elements selected.")
else:
    selected_elements = [doc.GetElement(el_id) for el_id in selection_ids]

    # Filter selected elements into walls and floors
    selected_floors = [el for el in selected_elements if isinstance(el, Floor)]
    selected_walls = [el for el in selected_elements if isinstance(el, Wall)]

    if not selected_floors:
        print("# No floors found in the selection.")
    elif not selected_walls:
        print("# No walls found in the selection.")
    else:
        join_count = 0
        skipped_already_joined = 0
        skipped_no_intersection = 0
        error_count = 0

        # Iterate through all pairs of selected floors and walls
        # Assumption: User wants to join every selected floor with every selected wall if they intersect.
        for floor in selected_floors:
            if not floor or not floor.IsValidObject: continue # Skip invalid elements

            for wall in selected_walls:
                if not wall or not wall.IsValidObject: continue # Skip invalid elements
                if floor.Id == wall.Id: continue # Should not happen with Floors/Walls, but good practice

                # Check if they are already joined
                try:
                    are_joined = JoinGeometryUtils.AreElementsJoined(doc, floor, wall)
                except Exception as e_check:
                    # print(f"# Error checking join status for Floor {floor.Id} and Wall {wall.Id}: {e_check}") # Escaped
                    error_count += 1
                    continue # Skip this pair if checking fails

                if not are_joined:
                    # Attempt to join the geometry
                    try:
                        JoinGeometryUtils.JoinGeometry(doc, floor, wall)
                        # Verify if join succeeded (JoinGeometry might not throw error but fail)
                        if JoinGeometryUtils.AreElementsJoined(doc, floor, wall):
                            join_count += 1
                            # print(f"# Joined Floor {floor.Id} and Wall {wall.Id}") # Escaped
                        else:
                            # Join command executed but elements are still not joined - likely no intersection
                            skipped_no_intersection += 1
                            # print(f"# Skipped: Floor {floor.Id} and Wall {wall.Id} do not intersect sufficiently to join.") # Escaped
                    except Exception as e_join:
                        # This usually happens if elements cannot be joined (e.g., incompatible types, geometry issues)
                        # Often indicates they don't intersect properly.
                        skipped_no_intersection += 1
                        # print(f"# Could not join Floor {floor.Id} and Wall {wall.Id}. Reason: {e_join}") # Escaped
                else:
                    skipped_already_joined += 1
                    # print(f"# Skipped: Floor {floor.Id} and Wall {wall.Id} are already joined.") # Escaped

        # Optional summary (uncomment to see results in RPS console)
        # total_pairs = len(selected_floors) * len(selected_walls)
        # print("# --- Join Geometry Summary ---") # Escaped
        # print("# Selected Floors: {}".format(len(selected_floors))) # Escaped
        # print("# Selected Walls: {}".format(len(selected_walls))) # Escaped
        # print("# Total Pairs Checked: {}".format(total_pairs)) # Escaped
        # print("# Successful Joins: {}".format(join_count)) # Escaped
        # print("# Skipped (Already Joined): {}".format(skipped_already_joined)) # Escaped
        # print("# Skipped (No Intersection/Error): {}".format(skipped_no_intersection + error_count)) # Escaped
        # if error_count > 0:
        #     print("#   (Errors during status check: {})".format(error_count)) # Escaped