# Purpose: This script sets a specified parameter on selected structural columns to the nearest grid intersection name.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
from System import Exception # Explicit exception import

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    ElementId,
    Grid,
    FamilyInstance,
    LocationPoint,
    Parameter,
    XYZ,
    Line,
    Curve,
    BuiltInParameter # Although target is custom, keep for reference/fallback
)
# Assuming Structural Columns category for columns
# Assuming 'Grid Location' is a text parameter

# --- Constants ---
TARGET_PARAMETER_NAME = "Grid Location"
DEFAULT_GRID_NAME = "?" # Placeholder if no grid found
TOLERANCE = 1e-6 # For vector comparisons

# --- Helper Functions ---
def get_element_location(element):
    """Attempts to get a representative XYZ point for an element."""
    location = element.Location
    if isinstance(location, LocationPoint):
        return location.Point
    else:
        # Fallback to bounding box center if no LocationPoint
        # Ensure a view context is provided for bounding box if needed, using None for model coords
        bb = element.get_BoundingBox(None)
        if bb:
            # Check if bounding box is valid (min/max are not None and Min is less than Max)
            if bb.Min is not None and bb.Max is not None and \
               bb.Min.X < bb.Max.X and bb.Min.Y < bb.Max.Y and bb.Min.Z < bb.Max.Z:
                 return (bb.Min + bb.Max) / 2.0
            else: # Bounding box is degenerate or invalid
                return None
        else: # Bounding box is None
            return None
    return None # Should not be reached if logic is correct

# --- Script Core Logic ---

# 1. Get Selected Elements
try:
    selected_ids = uidoc.Selection.GetElementIds()
    if not selected_ids:
        print("# No elements selected.")
        selected_elements = []
    else:
        selected_elements = [doc.GetElement(id) for id in selected_ids if doc.GetElement(id) is not None] # Filter out nulls if any ID is invalid
except Exception as e:
    print("# Error getting selection: {}".format(e))
    selected_elements = [] # Ensure it's an empty list on error

# 2. Filter for Structural Columns
columns = []
structural_column_category_id_int = int(BuiltInCategory.OST_StructuralColumns)
for elem in selected_elements:
    # Check category first - more reliable than class for columns
    # Also ensure element is valid
    if elem and elem.IsValidObject and elem.Category and elem.Category.Id.IntegerValue == structural_column_category_id_int:
         columns.append(elem)

if not columns:
    print("# No structural columns found in the current selection.")
    # Stop script execution if no relevant elements selected

# 3. Collect and Categorize Grids
horizontal_grids = [] # Tuples: (name, curve)
vertical_grids = []   # Tuples: (name, curve)

try:
    # Use FilteredElementCollector for better performance
    grid_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType()
    all_grids = list(grid_collector) # Collect grids into a list

    xaxis = XYZ.BasisX
    yaxis = XYZ.BasisY

    for grid in all_grids:
        if isinstance(grid, Grid) and grid.IsValidObject: # Ensure grid is valid
            curve = grid.Curve
            # Check if curve is bound and is a Line
            if curve and curve.IsBound and isinstance(curve, Line):
                try:
                    name = grid.Name
                    if not name: # Check if name is empty or None
                        # print("# Skipping grid ID {} - no name.".format(grid.Id)) # Debug
                        continue # Skip grids without names

                    direction = curve.Direction.Normalize()

                    # Check if grid line is parallel to X-axis (Horizontal Grid)
                    if direction.IsAlmostEqualTo(xaxis, TOLERANCE) or direction.IsAlmostEqualTo(-xaxis, TOLERANCE):
                        horizontal_grids.append((name, curve))
                    # Check if grid line is parallel to Y-axis (Vertical Grid)
                    elif direction.IsAlmostEqualTo(yaxis, TOLERANCE) or direction.IsAlmostEqualTo(-yaxis, TOLERANCE):
                        vertical_grids.append((name, curve))
                    # else: grid is diagonal, ignore for nearest orthogonal check
                except Exception as grid_ex:
                    print("# Error processing Grid ID {}: {}".format(grid.Id, grid_ex))
            # else: grid curve is not a bound Line (e.g., Arc or unbound), ignore
except Exception as e:
    print("# Error collecting or processing Grids: {}".format(e))
    # Allow processing columns, but grid location might be incomplete

# --- Process Columns ---
updated_count = 0
skipped_no_location = 0
skipped_no_param = 0
error_count = 0

# 4. Process Each Selected Column
for column in columns:
    col_id = column.Id # Store ID for error messages
    try:
        # Get column location
        col_location = get_element_location(column)
        if not col_location:
            # print("# Skipping column ID {} - cannot determine location.".format(col_id)) # Debug
            skipped_no_location += 1
            continue

        # Find the target parameter
        # LookupParameter is case-sensitive
        grid_loc_param = column.LookupParameter(TARGET_PARAMETER_NAME)

        # If not found by name, maybe check common built-in params (though unlikely for 'Grid Location')
        # if not grid_loc_param:
        #     grid_loc_param = column.get_Parameter(BuiltInParameter.COLUMN_LOCATION_MARK) # Example

        if not grid_loc_param:
            # print("# Skipping column ID {} - parameter '{}' not found.".format(col_id, TARGET_PARAMETER_NAME)) # Debug
            skipped_no_param += 1
            continue
        elif grid_loc_param.IsReadOnly:
             # print("# Skipping column ID {} - parameter '{}' is read-only.".format(col_id, TARGET_PARAMETER_NAME)) # Debug
             skipped_no_param += 1
             continue

        # Ensure parameter is of type String (Text)
        # Needs StorageType check, but Set(string) often handles conversion for some types.
        # Add check if errors occur: if grid_loc_param.StorageType != StorageType.String: continue

        # Find nearest horizontal grid
        nearest_h_name = DEFAULT_GRID_NAME
        min_dist_h = float('inf')
        if horizontal_grids:
            for name, curve in horizontal_grids:
                try:
                    # Project the point onto the unbounded line geometry
                    projection_result = curve.Project(col_location)
                    if projection_result:
                        dist = col_location.DistanceTo(projection_result.XYZPoint)
                        if dist < min_dist_h:
                            min_dist_h = dist
                            nearest_h_name = name
                except Exception as proj_ex:
                     # Potentially noisy, comment out if needed
                     # print("# Warn: Error projecting onto horizontal grid '{}' for column {}: {}".format(name, col_id, proj_ex))
                     pass


        # Find nearest vertical grid
        nearest_v_name = DEFAULT_GRID_NAME
        min_dist_v = float('inf')
        if vertical_grids:
             for name, curve in vertical_grids:
                try:
                    # Project the point onto the unbounded line geometry
                    projection_result = curve.Project(col_location)
                    if projection_result:
                        dist = col_location.DistanceTo(projection_result.XYZPoint)
                        if dist < min_dist_v:
                            min_dist_v = dist
                            nearest_v_name = name
                except Exception as proj_ex:
                     # Potentially noisy, comment out if needed
                     # print("# Warn: Error projecting onto vertical grid '{}' for column {}: {}".format(name, col_id, proj_ex))
                     pass

        # Construct the grid location string (Assume convention is Vertical-Horizontal e.g., A-1)
        # Adjust format if needed: "{}-{}".format(nearest_h_name, nearest_v_name) for H-V
        grid_location_string = "{}-{}".format(nearest_v_name, nearest_h_name)

        # Set the parameter value
        try:
            # Check if the value actually needs updating
            current_value = grid_loc_param.AsString() # Get current value safely
            # Handle potential None value from AsString() if parameter is empty
            if current_value is None:
                current_value = ""

            if current_value != grid_location_string:
                # Use SetValueString for better type handling if Set(string) causes issues
                # success = grid_loc_param.SetValueString(grid_location_string)
                success = grid_loc_param.Set(grid_location_string)
                if success:
                    updated_count += 1
                else:
                    # This 'else' might not be reliable, Set throws exception on failure usually
                    # print("# Failed to set parameter for column ID {} (Set returned False).".format(col_id)) # Debug
                    error_count += 1
            # else: Parameter already has the correct value, no need to update

        except Exception as set_ex:
            print("# Error setting parameter for column ID {}: {}".format(col_id, set_ex))
            error_count += 1

    except Exception as col_ex:
        print("# Error processing column ID {}: {}".format(col_id, col_ex))
        error_count += 1

# 5. Optional Summary (commented out per instructions)
# print("--- Column Grid Location Update Summary ---")
# print("Total columns processed: {}".format(len(columns)))
# print("Successfully updated: {}".format(updated_count))
# print("Skipped (No Location): {}".format(skipped_no_location))
# print("Skipped (Parameter '{}' not found/read-only): {}".format(TARGET_PARAMETER_NAME, skipped_no_param))
# print("Errors during processing/update: {}".format(error_count))