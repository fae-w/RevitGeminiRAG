# Purpose: This script hides Revit grids that are not perpendicular to the active view direction.

﻿# Import necessary classes
import clr
clr.AddReference('System.Core') # Required for Linq
clr.AddReference('System.Collections') # Required for List<T>
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Grid,
    View,
    XYZ,
    Line,
    Arc,
    ElementId
)
from System import Math # For Math.Abs
from System.Collections.Generic import List

# Get the active view
active_view = doc.ActiveView

# Check if there is an active view and it's valid
if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or the active view is invalid.")
else:
    try:
        # Get the view direction (must be a view type that has a direction)
        view_dir = active_view.ViewDirection
        # Normalize for safety, though it should already be normalized
        view_dir = view_dir.Normalize()

        # List to store the IDs of grids to hide
        grids_to_hide_ids = List[ElementId]()

        # Tolerance for checking perpendicularity (dot product near zero)
        tolerance = 1e-6

        # Collect all Grid elements in the document
        collector = FilteredElementCollector(doc).OfClass(Grid)

        for grid in collector:
            if grid and grid.IsValidObject:
                try:
                    curve = grid.Curve

                    # Check if the grid is linear (Line)
                    if isinstance(curve, Line):
                        line = curve
                        # Get the direction of the grid line
                        line_dir = line.Direction.Normalize()

                        # Calculate the absolute value of the dot product
                        # If vectors are perpendicular, dot product is 0
                        dot_product = Math.Abs(view_dir.DotProduct(line_dir))

                        # If the dot product is greater than the tolerance,
                        # the grid line is NOT perpendicular to the view direction
                        if dot_product > tolerance:
                            # Check if the element can be hidden in this view
                            if grid.CanBeHidden(active_view):
                                grids_to_hide_ids.Add(grid.Id)
                            # else: # Optional debug print
                            #    print(f"# Info: Grid {grid.Id} cannot be hidden in view '{active_view.Name}'.")

                    # Handle Arc grids - perpendicularity is less defined, skip for now
                    elif isinstance(curve, Arc):
                         # print(f"# Info: Skipping Arc grid {grid.Id} - perpendicularity check only implemented for linear grids.")
                         pass
                    # Handle other curve types if necessary
                    else:
                         # print(f"# Info: Skipping grid {grid.Id} with unsupported curve type: {curve.GetType().Name}")
                         pass

                except Exception as ex_grid:
                    # Log error processing a specific grid but continue
                    # print(f"# Warning: Error processing grid {grid.Id}: {ex_grid}")
                    pass

        # Hide the collected non-perpendicular grids in the active view
        # The transaction is handled by the external C# wrapper
        if grids_to_hide_ids.Count > 0:
            try:
                active_view.HideElements(grids_to_hide_ids)
                # print(f"# Attempted to hide {grids_to_hide_ids.Count} non-perpendicular grids in view '{active_view.Name}'.") # Optional output
            except Exception as ex_hide:
                 print(f"# Error: Failed to hide elements in view '{active_view.Name}': {ex_hide}")
        # else:
            # print(f"# No non-perpendicular linear grids found or eligible for hiding in view '{active_view.Name}'.") # Optional output

    except AttributeError:
        print(f"# Error: The active view '{active_view.Name}' (Type: {active_view.ViewType}) does not have a 'ViewDirection' property (e.g., Schedule, Legend).")
    except Exception as ex_main:
        print(f"# An unexpected error occurred: {ex_main}")