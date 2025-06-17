# Purpose: This script adds a missing segment to a selected curtain grid line in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
clr.AddReference('System.Collections')
from System.Collections.Generic import List
import System # For exception handling
from Autodesk.Revit.DB import (
    ElementId,
    CurtainGridLine,
    Curve,
    XYZ,
    CurveArray # Required for properties returning CurveArray
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
        # print("# Debug: Error comparing curves: {}".format(e)) # Keep commented out for final script
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
            # Get all potential segment curves and existing segment curves
            all_curves = grid_line.AllSegmentCurves
            existing_curves = grid_line.ExistingSegmentCurves

            # Check if there are any potential segments
            if all_curves is None or all_curves.IsEmpty:
                print("# The selected grid line (ID: {}) has no potential segments defined.".format(grid_line.Id))
            # Check if all segments already exist
            elif existing_curves is not None and all_curves.Size == existing_curves.Size:
                print("# The selected grid line (ID: {}) already has all its segments.".format(grid_line.Id))
            else:
                segment_added = False
                # Convert existing CurveArray to a list for easier iteration/lookup if needed
                existing_curves_list = list(existing_curves) if existing_curves is not None else []

                # Iterate through all potential segments
                for curve_to_add in all_curves:
                    # Check if this potential segment already exists
                    is_existing = False
                    for existing_curve in existing_curves_list:
                        if curves_are_similar(curve_to_add, existing_curve):
                            is_existing = True
                            break # Found a match, no need to check further for this curve_to_add

                    # If the segment does not exist, try to add it
                    if not is_existing:
                        try:
                            grid_line.AddSegment(curve_to_add)
                            # Successfully added a segment
                            print("# Added one segment to the selected Curtain Grid Line (ID: {}).".format(grid_line.Id))
                            segment_added = True
                            # Stop after adding the first missing segment found
                            break
                        except System.Exception as add_ex:
                            # Log error if adding the specific segment fails
                            print("# Error attempting to add a segment to Curtain Grid Line (ID: {}): {}".format(grid_line.Id, add_ex))
                            # Optional: Could break here or continue trying other missing segments
                            # Breaking here prevents potential repeated errors if there's a general issue.
                            break

                # If loop finished but no segment was added, and counts suggest one should be addable
                if not segment_added:
                    # Recalculate sizes *after* potential add attempt failed/didn't happen
                    current_existing_curves = grid_line.ExistingSegmentCurves
                    current_existing_size = current_existing_curves.Size if current_existing_curves is not None else 0
                    if all_curves.Size > current_existing_size:
                         print("# Could not identify or add a missing segment using the available curves, although potential segments seem to be missing.")
                         print("# Check for complex geometry or Revit limitations. Consider using 'Add All Segments' tool if appropriate.")
                    # else: # This case implies all segments were present after all (or became present due to concurrent changes).
                        # print("# All segments appear to be present now.")


        except System.Exception as e:
            print("# Error processing Curtain Grid Line (ID: {}): {}".format(grid_line.Id, e))
    else:
        print("# The selected element (ID: {}) is not a Curtain Grid Line.".format(selected_id))