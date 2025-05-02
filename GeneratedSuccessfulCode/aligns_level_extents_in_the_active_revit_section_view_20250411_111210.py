# Purpose: This script aligns level extents in the active Revit section view.

# Purpose: This script aligns the start and end points of levels in the active Revit section view by averaging their X coordinates, ensuring they are vertically aligned within the view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector, Level, ElementId, ViewType, ViewSection, DatumPlane, DatumExtentType, XYZ, Line

# Get the active view
active_view = doc.ActiveView

# Check if the active view is a section view
if not active_view:
    print("# Error: No active view.")
elif not isinstance(active_view, ViewSection):
    print("# Error: Active view is not a Section View.")
else:
    # Collect Level elements visible in the active section view
    levels_collector = FilteredElementCollector(doc, active_view.Id).OfClass(Level)
    levels = list(levels_collector)

    if not levels:
        print("# No Level elements found in the active view.")
    else:
        start_points = []
        end_points = []
        valid_levels_for_alignment = []
        levels_data = {} # Store original curve data per level

        # Loop 1: Collect existing curve endpoints and ensure view-specific extents
        for level in levels:
            if isinstance(level, DatumPlane): # Ensure it's a DatumPlane (Levels are)
                try:
                    # Ensure extents are view-specific for modification.
                    # This might change the level's appearance if it was previously using model extents.
                    is_modified = False
                    if level.GetDatumExtentTypeInView(DatumExtentType.End0, active_view) != DatumExtentType.ViewSpecific:
                         level.SetDatumExtentType(DatumExtentType.End0, active_view, DatumExtentType.ViewSpecific)
                         is_modified = True # Mark that we changed the type
                    if level.GetDatumExtentTypeInView(DatumExtentType.End1, active_view) != DatumExtentType.ViewSpecific:
                         level.SetDatumExtentType(DatumExtentType.End1, active_view, DatumExtentType.ViewSpecific)
                         is_modified = True # Mark that we changed the type

                    # If we just changed extent type, Revit might need to regenerate before GetCurvesInView works reliably.
                    # However, running regeneration here isn't possible within the script context.
                    # Proceeding optimistically.

                    curves = level.GetCurvesInView(DatumExtentType.ViewSpecific, active_view)
                    if curves and curves.Count > 0:
                        # Assume the first curve is the main one for alignment
                        curve = curves[0]
                        if isinstance(curve, Line):
                            p0 = curve.GetEndPoint(0)
                            p1 = curve.GetEndPoint(1)
                            start_points.append(p0)
                            end_points.append(p1)
                            valid_levels_for_alignment.append(level)
                            levels_data[level.Id] = (p0, p1) # Store original points
                        # else:
                            # print(f"# Skipping Level {level.Name} - curve is not a Line in this view.") # Escaped
                    # else:
                        # print(f"# Skipping Level {level.Name} - no view-specific curve found (might need regeneration after extent type change).") # Escaped
                except Exception as e:
                    # print(f"# Error processing Level {level.Id} ({level.Name}) during collection: {e}") # Escaped
                    pass # Skip levels that cause errors

        if not valid_levels_for_alignment:
            print("# No valid levels with view-specific line geometry found or processed for alignment.")
        else:
            # Calculate average X coordinates
            avg_start_x = sum(pt.X for pt in start_points) / len(start_points)
            avg_end_x = sum(pt.X for pt in end_points) / len(end_points)

            # Loop 2: Apply new averaged X coordinates
            aligned_count = 0
            for level in valid_levels_for_alignment:
                try:
                    if level.Id in levels_data:
                        p0, p1 = levels_data[level.Id] # Use stored original points for YZ

                        # Create new points with averaged X, keeping original YZ
                        # Y typically represents elevation in a section, Z is depth.
                        new_p0 = XYZ(avg_start_x, p0.Y, p0.Z)
                        new_p1 = XYZ(avg_end_x, p1.Y, p1.Z)

                        # Check if points are effectively the same (avoid creating zero-length line)
                        if new_p0.IsAlmostEqualTo(new_p1):
                            # print(f"# Skipping Level {level.Name} - start/end points too close after averaging.") # Escaped
                            continue

                        new_line = Line.CreateBound(new_p0, new_p1)
                        level.SetCurveInView(DatumExtentType.ViewSpecific, active_view, new_line)
                        aligned_count += 1
                except Exception as e:
                    # print(f"# Error aligning Level {level.Id} ({level.Name}): {e}") # Escaped
                    pass # Skip levels that fail during update

            # Optional: Print summary message (commented out by default)
            # print(f"# Attempted to align {aligned_count} levels in view '{active_view.Name}'.") # Escaped