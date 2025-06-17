# Purpose: This script deletes unlocked mullions associated with a selected curtain grid line in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
clr.AddReference('System.Collections')
from System.Collections.Generic import List
import System # For exception handling
from Autodesk.Revit.DB import (
    ElementId,
    CurtainGridLine,
    CurtainGrid,
    Mullion,
    Curve,
    CurveArray, # Required for properties returning CurveArray
    XYZ
)

# Helper function to compare curves based on endpoints (simplistic)
# Note: This is a basic geometric comparison and might fail in complex cases.
def curves_are_similar(curve1, curve2, tolerance=1e-6):
    """Checks if two curves are likely the same segment based on endpoints."""
    if not curve1 or not curve2:
        return False
    try:
        # Check if both curves have valid endpoints
        if not hasattr(curve1, 'GetEndPoint') or not hasattr(curve2, 'GetEndPoint'):
             return False # Cannot compare if endpoint method is missing

        p1_start = curve1.GetEndPoint(0)
        p1_end = curve1.GetEndPoint(1)
        p2_start = curve2.GetEndPoint(0)
        p2_end = curve2.GetEndPoint(1)

        # Check if endpoints match (either direction) using Revit's tolerance check
        match1 = p1_start.IsAlmostEqualTo(p2_start, tolerance) and p1_end.IsAlmostEqualTo(p2_end, tolerance)
        match2 = p1_start.IsAlmostEqualTo(p2_end, tolerance) and p1_end.IsAlmostEqualTo(p2_start, tolerance)

        return match1 or match2
    except Exception as e:
        # print("# Debug: Error comparing curves: {{}}".format(e)) # Keep commented out
        return False

# --- Script Core Logic ---

# Get current selection
selected_ids = uidoc.Selection.GetElementIds()

# Check if exactly one element is selected
if len(selected_ids) != 1:
    print("# Please select exactly one Curtain Grid Line.")
else:
    selected_id = selected_ids[0]
    selected_element = doc.GetElement(selected_id)

    # Check if the selected element is a CurtainGridLine
    if isinstance(selected_element, CurtainGridLine):
        grid_line = selected_element
        try:
            # Get the parent CurtainGrid
            parent_grid = grid_line.Grid
            if not parent_grid:
                print("# Could not find the parent CurtainGrid for the selected line (ID: {}).".format(grid_line.Id))

            else:
                # Get the existing segment curves of the selected grid line
                grid_line_segments = grid_line.ExistingSegmentCurves
                if grid_line_segments is None or grid_line_segments.IsEmpty:
                    print("# The selected grid line (ID: {}) has no existing segments.".format(grid_line.Id))

                else:
                    # Get IDs of unlocked mullions associated with the parent grid
                    # Unlocked mullions are typically those added manually or modified.
                    # Locked mullions (from type) usually cannot be deleted individually this way.
                    unlocked_mullion_ids = parent_grid.GetUnlockedMullionIds()
                    mullion_ids_to_delete = List[ElementId]()
                    deleted_count = 0

                    if unlocked_mullion_ids and unlocked_mullion_ids.Count > 0:
                        for mullion_id in unlocked_mullion_ids:
                            mullion = doc.GetElement(mullion_id)
                            if isinstance(mullion, Mullion):
                                mullion_curve = None
                                try:
                                    # Get the location curve of the mullion
                                    if hasattr(mullion, 'LocationCurve') and mullion.LocationCurve:
                                         mullion_curve = mullion.LocationCurve
                                except System.Exception as lc_ex:
                                    print("# Warning: Could not get LocationCurve for Mullion ID {}: {}".format(mullion_id, lc_ex))
                                    continue # Skip this mullion

                                if mullion_curve:
                                    # Compare the mullion's curve to the segments of the selected grid line
                                    for segment_curve in grid_line_segments:
                                        if curves_are_similar(mullion_curve, segment_curve):
                                            # Found a mullion matching a segment of the selected line
                                            mullion_ids_to_delete.Add(mullion_id)
                                            break # Move to the next mullion
                    # Attempt to delete the collected mullions
                    if mullion_ids_to_delete.Count > 0:
                        try:
                            # The actual deletion happens within the Transaction managed by the C# wrapper
                            deleted_ids = doc.Delete(mullion_ids_to_delete)
                            deleted_count = deleted_ids.Count if deleted_ids else 0
                            print("# Deleted {} unlocked mullion(s) associated with the selected Curtain Grid Line (ID: {}).".format(deleted_count, grid_line.Id))
                        except System.Exception as del_ex:
                            print("# Error deleting mullions: {}".format(del_ex))
                            print("# Note: Some mullions might be locked or have dependencies preventing deletion.")
                    else:
                        print("# No unlocked mullions found associated with the segments of the selected Curtain Grid Line (ID: {}). Check if mullions are locked by type.".format(grid_line.Id))

        except System.Exception as e:
            print("# Error processing Curtain Grid Line (ID: {}): {}".format(grid_line.Id, e))
    else:
        print("# The selected element (ID: {}) is not a Curtain Grid Line.".format(selected_id))