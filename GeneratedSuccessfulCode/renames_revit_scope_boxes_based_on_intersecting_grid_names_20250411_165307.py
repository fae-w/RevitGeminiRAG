# Purpose: This script renames Revit scope boxes based on intersecting grid names.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
from System import Exception # Explicit exception import
from System.Collections.Generic import List # Might not be strictly needed but good practice

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    ElementId, # Good practice
    Grid,
    BoundingBoxXYZ,
    XYZ,
    Line,
    Curve,
    Parameter,
    BuiltInParameter # Potentially needed for name if .Name fails
)

# --- Helper Function for Sorting ---
def sort_grid_names(names):
    """
    Sorts a list of grid names.
    Attempts numeric sort first, falls back to alphabetical.
    """
    try:
        # Try sorting numerically
        return sorted(names, key=int)
    except ValueError:
        # Fallback to alphabetical sort if conversion to int fails
        return sorted(names)
    except Exception as e:
         # General fallback in case of other sorting errors
         print("# Warning: Could not sort grid names effectively. Using original order. Error: {}".format(e))
         return names # Return original list on other errors

# --- Initialization ---
renamed_count = 0
skipped_count = 0
error_count = 0
processed_count = 0

# --- Step 1: Collect Scope Boxes ---
try:
    scope_boxes = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_VolumeOfInterest).WhereElementIsNotElementType().ToElements()
    if not scope_boxes:
        print("# No Scope Boxes found in the project.")
        # Exit script gracefully if no scope boxes
        # return # Cannot use return here, just let it proceed to grid collection
except Exception as e:
    print("# Error collecting Scope Boxes: {}".format(e))
    scope_boxes = [] # Ensure it's an empty list if collection fails

# --- Step 2: Collect and Categorize Grids ---
horizontal_grids = [] # Tuples: (name, y_coord, grid_element)
vertical_grids = []   # Tuples: (name, x_coord, grid_element)

try:
    all_grids = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType().ToElements()

    xaxis = XYZ.BasisX
    yaxis = XYZ.BasisY
    tolerance = 1e-6 # Tolerance for vector comparison

    for grid in all_grids:
        if isinstance(grid, Grid):
            curve = grid.Curve
            if isinstance(curve, Line):
                try:
                    name = grid.Name
                    if not name: # Check if name is empty or None
                         # print("# Warning: Grid ID {} has no name, skipping.".format(grid.Id))
                         continue # Skip grids without names

                    direction = curve.Direction.Normalize()

                    # Check if grid line is parallel to X-axis (Horizontal Grid)
                    if direction.IsAlmostEqualTo(xaxis, tolerance) or direction.IsAlmostEqualTo(-xaxis, tolerance):
                        # Use the midpoint Y coordinate for robustness if needed, start point is usually fine
                        y_coord = curve.GetEndPoint(0).Y
                        horizontal_grids.append((name, y_coord, grid))
                    # Check if grid line is parallel to Y-axis (Vertical Grid)
                    elif direction.IsAlmostEqualTo(yaxis, tolerance) or direction.IsAlmostEqualTo(-yaxis, tolerance):
                         # Use the midpoint X coordinate for robustness if needed, start point is usually fine
                        x_coord = curve.GetEndPoint(0).X
                        vertical_grids.append((name, x_coord, grid))
                    # else: grid is diagonal, ignore for this script
                except Exception as grid_ex:
                    # print("# Error processing Grid ID {}: {}".format(grid.Id, grid_ex))
                    error_count += 1 # Count as an error if grid processing fails
            # else: grid curve is not a Line (e.g., Arc), ignore
except Exception as e:
    print("# Error collecting or processing Grids: {}".format(e))
    # Continue processing scope boxes even if grid collection had issues, might lead to skips

if not horizontal_grids and not vertical_grids:
    print("# No suitable horizontal or vertical grids found.")
    # Allow script to finish if scope boxes exist but no grids were found

# --- Step 3: Process Each Scope Box ---
for sb in scope_boxes:
    processed_count += 1
    original_name = "<Unknown>" # Default for error case
    try:
        original_name = sb.Name
        bb = sb.get_BoundingBox(None) # Get BoundingBoxXYZ in model coordinates

        if not bb:
            # print("# Skipping Scope Box '{}' (ID: {}), could not get bounding box.".format(original_name, sb.Id))
            skipped_count += 1
            continue

        min_pt = bb.Min
        max_pt = bb.Max

        # Find intersecting grids based on coordinate range
        intersecting_h_grid_names = []
        for name, y_coord, grid_elem in horizontal_grids:
            if min_pt.Y - tolerance <= y_coord <= max_pt.Y + tolerance: # Add tolerance
                intersecting_h_grid_names.append(name)

        intersecting_v_grid_names = []
        for name, x_coord, grid_elem in vertical_grids:
            if min_pt.X - tolerance <= x_coord <= max_pt.X + tolerance: # Add tolerance
                intersecting_v_grid_names.append(name)

        # Check if we found grids in both directions
        if not intersecting_h_grid_names or not intersecting_v_grid_names:
            # print("# Skipping Scope Box '{}' (ID: {}), no intersecting horizontal or vertical grids found within its range.".format(original_name, sb.Id))
            skipped_count += 1
            continue

        # Sort the names to find the min/max range
        sorted_h_names = sort_grid_names(intersecting_h_grid_names)
        sorted_v_names = sort_grid_names(intersecting_v_grid_names)

        h_min_name = sorted_h_names[0]
        h_max_name = sorted_h_names[-1]
        v_min_name = sorted_v_names[0]
        v_max_name = sorted_v_names[-1]

        # Construct the new name: SB_HminVmin-HmaxVmax (e.g., SB_A1-C3)
        new_name = "SB_{}{}-{}{}".format(h_min_name, v_min_name, h_max_name, v_max_name)

        # Rename if necessary
        if original_name != new_name:
            try:
                sb.Name = new_name
                renamed_count += 1
                # print("# Renamed Scope Box '{}' to '{}'".format(original_name, new_name))
            except Exception as rename_ex:
                error_count += 1
                # print("# Error renaming Scope Box '{}' (ID: {}) to '{}': {}".format(original_name, sb.Id, new_name, rename_ex))
        else:
             skipped_count += 1 # Already named correctly
             # print("# Skipping Scope Box '{}' (ID: {}), name already correct.".format(original_name, sb.Id))

    except Exception as outer_ex:
        error_count += 1
        # print("# Error processing Scope Box '{}' (ID: {}): {}".format(original_name, sb.Id, outer_ex))

# --- Step 4: Optional Summary ---
# print("--- Scope Box Renaming Summary ---")
# print("Total Scope Boxes Processed: {}".format(processed_count))
# print("Successfully Renamed: {}".format(renamed_count))
# print("Skipped (No Grids/Correct Name/No BBox): {}".format(skipped_count))
# print("Errors Encountered: {}".format(error_count))