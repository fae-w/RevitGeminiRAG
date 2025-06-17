# Purpose: This script creates a pie chart in the active Revit view representing the relative areas of different floor types in the project.

# Purpose: This script creates a pie chart in the active Revit view representing the relative areas of different floor types in the project.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Math
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Floor, FloorType, ElementId,
    FilledRegion, FilledRegionType, FillPatternElement, View, ViewType,
    XYZ, Line, Arc, CurveLoop, Plane, BuiltInParameter, FillPattern, ElementClassFilter
)
from System import Math
from System.Collections.Generic import List # Use Generic List for CurveLoop list

# --- Configuration ---
PIE_CHART_RADIUS = 10.0 # Radius of the pie chart in feet
MIN_ANGLE_THRESHOLD = 0.001 # Minimum angle in radians to avoid tiny/degenerate arcs

# --- Helper Functions ---
def get_solid_fill_pattern_id(doc):
    """Finds the ElementId of the first solid fill pattern."""
    collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_fill_pattern_element = None
    for fp_elem in collector:
        # Need to get the FillPattern object from the FillPatternElement
        fill_pattern = fp_elem.GetFillPattern()
        if fill_pattern and fill_pattern.IsSolidFill:
            solid_fill_pattern_element = fp_elem
            break # Found the first one
    if solid_fill_pattern_element:
        return solid_fill_pattern_element.Id
    return ElementId.InvalidElementId

def get_filled_region_types(doc):
    """Gets a list of available FilledRegionType elements, prioritizing solid fill if possible."""
    all_types = FilteredElementCollector(doc).OfClass(FilledRegionType).ToElements()
    if not all_types:
        return [] # Return empty list if none found

    solid_fill_id = get_solid_fill_pattern_id(doc)
    solid_types = []
    other_types = []

    # Convert to a standard Python list for easier manipulation
    all_types_list = list(all_types)

    if solid_fill_id != ElementId.InvalidElementId:
        for frt in all_types_list:
            try:
                is_solid = False
                # Check foreground pattern
                if frt.ForegroundPatternId == solid_fill_id and frt.IsForegroundPatternVisible:
                     solid_types.append(frt)
                     is_solid = True
                # Check background pattern if foreground isn't solid
                # Use elif to avoid adding the same type twice if both patterns are solid
                elif frt.BackgroundPatternId == solid_fill_id and frt.IsBackgroundPatternVisible:
                     # Check again it wasn't already added via foreground
                     if frt not in solid_types:
                         solid_types.append(frt)
                     is_solid = True

                if not is_solid:
                     # Ensure it's not already in solid_types before adding to other_types
                     if frt not in solid_types:
                         other_types.append(frt)
            except Exception:
                 # Add to others if error accessing pattern properties, avoid duplicates
                 if frt not in solid_types and frt not in other_types:
                      other_types.append(frt)

        # Prioritize types identified as solid, then add others
        final_list = solid_types
        for ot in other_types:
            # Ensure no duplicates added
            if ot not in final_list:
                final_list.append(ot)
        return final_list
    else:
        # If no solid pattern found, just return all types
        return all_types_list


# --- Main Script ---

# 1. Get Active View and Check Type
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
    import sys
    sys.exit()

# Define allowed view types where FilledRegion can be created
allowed_view_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.Elevation,
    ViewType.Section, ViewType.Detail, ViewType.DraftingView,
    ViewType.AreaPlan, ViewType.EngineeringPlan, ViewType.Legend # Legends often used too
]
if active_view.ViewType not in allowed_view_types:
    print("# Error: Active view type ({0}) is not suitable for creating Filled Regions.".format(active_view.ViewType))
    print("# Please use a Plan, Section, Elevation, Detail, Drafting, Legend or Area Plan view.")
    import sys
    sys.exit()

active_view_id = active_view.Id

# 2. Collect Floor Data (Project-wide)
floor_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()
floor_type_areas = {} # Dictionary: {ElementId floor_type_id: float_area}
total_project_floor_area = 0.0

for floor in floor_collector:
    # Ensure it's actually a Floor element (not just category match)
    if isinstance(floor, Floor):
        try:
            area_param = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
            # Use GetTypeId() to get the ElementId of the type
            floor_type_id = floor.GetTypeId()

            if area_param and area_param.HasValue and floor_type_id != ElementId.InvalidElementId:
                area = area_param.AsDouble()
                if area > 1e-6: # Ignore negligible areas
                    current_area = floor_type_areas.get(floor_type_id, 0.0)
                    floor_type_areas[floor_type_id] = current_area + area
                    total_project_floor_area += area
        except Exception as e:
            # print("# Warning: Could not process floor {0}: {1}".format(floor.Id, e)) # Optional Debug
            pass

# 3. Handle No Floors Case
if total_project_floor_area < 1e-6 or not floor_type_areas:
    print("# No floors with valid types and positive area found in the project.")
    import sys
    sys.exit()

# 4. Get Available Filled Region Types
available_fr_types = get_filled_region_types(doc)
if not available_fr_types:
    print("# Error: No Filled Region Types found in the project. Cannot create pie chart.")
    print("# Please ensure at least one Filled Region Type exists.")
    import sys
    sys.exit()

# 5. Define Chart Geometry & Plane
try:
    view_normal = active_view.ViewDirection
    view_origin = active_view.Origin # Base origin of the view
    view_right = active_view.RightDirection
    view_up = active_view.UpDirection

    # Determine center point - attempt to use center of visible crop region
    center_point = view_origin # Default to view origin
    try:
        crop_box = active_view.CropBox
        if active_view.CropBoxActive and active_view.CropBoxVisible and crop_box and not crop_box.IsEmpty:
            # CropBox min/max are in the view's coordinate system relative to its origin
            center_view_coords = (crop_box.Min + crop_box.Max) / 2.0
            # Transform this 2D center (relative to view origin) into model space using view directions
            center_point = view_origin + view_right * center_view_coords.X + view_up * center_view_coords.Y
        # else: keep default center_point = view_origin
    except Exception as crop_err:
        print("# Warning: Could not determine center from CropBox, using View Origin. Error: {}".format(crop_err))
        center_point = view_origin

    # 6. Create Pie Slices
    start_angle = 0.0 # Start angle in radians
    fr_type_index = 0 # Index to cycle through available filled region types

    # Sort by floor type name for consistent order
    sorted_floor_types = sorted(floor_type_areas.keys(), key=lambda tid: doc.GetElement(tid).Name if doc.GetElement(tid) else "")

    print("# Found {0} floor types with area.".format(len(sorted_floor_types)))

    for i, floor_type_id in enumerate(sorted_floor_types):
        area = floor_type_areas[floor_type_id]
        proportion = area / total_project_floor_area
        sweep_angle = proportion * 2.0 * Math.PI

        floor_type_name = doc.GetElement(floor_type_id).Name if doc.GetElement(floor_type_id) else "UnknownType"
        # print("# Processing: Type='{0}', Area={1:.2f}, Proportion={2:.3f}, SweepAngle={3:.3f} rad".format(floor_type_name, area, proportion, sweep_angle)) # Debug

        # Check if the slice is too small
        if sweep_angle < MIN_ANGLE_THRESHOLD:
            print("# Skipping tiny slice for Floor Type '{0}' (ID: {1})".format(floor_type_name, floor_type_id))
            continue

        end_angle = start_angle + sweep_angle

        # If only one type, it should be a full circle
        is_full_circle = abs(sweep_angle - 2 * Math.PI) < MIN_ANGLE_THRESHOLD and len(sorted_floor_types) == 1

        # Get the Filled Region Type for this slice
        current_fr_type = available_fr_types[fr_type_index % len(available_fr_types)]
        fr_type_id_to_use = current_fr_type.Id
        fr_type_index += 1
        # print("# Using Filled Region Type: '{0}'".format(current_fr_type.Name)) # Debug

        # Create geometry
        try:
            loops = List[CurveLoop]()
            if is_full_circle:
                # Create a full circle using two semi-circular arcs
                # Use center, radius, angles method for robustness
                arc1 = Arc.Create(center_point, PIE_CHART_RADIUS, start_angle, start_angle + Math.PI, view_right, view_up)
                arc2 = Arc.Create(center_point, PIE_CHART_RADIUS, start_angle + Math.PI, start_angle + 2 * Math.PI, view_right, view_up)

                curve_loop = CurveLoop()
                # Check if arcs are valid before appending
                if arc1 and arc2 and arc1.Length > 1e-6 and arc2.Length > 1e-6:
                     curve_loop.Append(arc1)
                     curve_loop.Append(arc2)
                     if not curve_loop.IsOpen():
                         loops.Add(curve_loop)
                     else:
                          print("# Error: Full circle CurveLoop is open for Type '{0}'. Skipping.".format(floor_type_name))
                          continue # Skip this type
                else:
                    print("# Error: Could not create valid arcs for full circle (Type '{0}'). Skipping.".format(floor_type_name))
                    continue # Skip this type
            else:
                # Create a pie slice (arc + 2 lines)
                # Calculate arc points using view's Right and Up directions
                start_point = center_point + PIE_CHART_RADIUS * (view_right * Math.Cos(start_angle) + view_up * Math.Sin(start_angle))
                end_point = center_point + PIE_CHART_RADIUS * (view_right * Math.Cos(end_angle) + view_up * Math.Sin(end_angle))

                # Check if start/end points are too close (can happen with numerical precision)
                if start_point.IsAlmostEqualTo(end_point, 1e-9):
                     print("# Skipping slice for Floor Type '{0}' due to coincident start/end points (Angle: {1:.4f} rad).".format(floor_type_name, sweep_angle))
                     start_angle = end_angle # Still update start angle for next iteration
                     continue

                # Create Arc for the slice edge
                arc = None
                try:
                     # Use Center, Radius, StartAngle, EndAngle version for robustness
                     arc = Arc.Create(center_point, PIE_CHART_RADIUS, start_angle, end_angle, view_right, view_up)
                     if not arc or arc.Length < 1e-6: # Check if arc creation succeeded and is valid
                         print("# Warning: Arc creation using angles failed or resulted in zero length for '{0}'. Trying 3-point method.".format(floor_type_name))
                         arc = None # Reset arc
                         # Attempt 3-point arc as fallback if needed (less robust for exact angles)
                         mid_angle = (start_angle + end_angle) / 2.0
                         mid_point = center_point + PIE_CHART_RADIUS * (view_right * Math.Cos(mid_angle) + view_up * Math.Sin(mid_angle))
                         if not start_point.IsAlmostEqualTo(mid_point, 1e-9) and not mid_point.IsAlmostEqualTo(end_point, 1e-9):
                              arc = Arc.Create(start_point, end_point, mid_point)
                         else:
                              print("# Error: Cannot create 3-point arc due to coincident points for '{0}'. Skipping slice.".format(floor_type_name))
                              start_angle = end_angle
                              continue
                except Exception as arc_err:
                     print("# Error creating arc for Floor Type '{0}': {1}. Skipping slice.".format(floor_type_name, arc_err))
                     start_angle = end_angle # Ensure next slice starts correctly
                     continue # Skip this slice

                if not arc or arc.Length < 1e-6:
                     print("# Error: Failed to create a valid arc for Floor Type '{0}'. Skipping slice.".format(floor_type_name))
                     start_angle = end_angle
                     continue

                # Create lines from center to arc ends
                line1 = Line.CreateBound(center_point, start_point)
                line2 = Line.CreateBound(end_point, center_point)

                if not line1 or not line2 or line1.Length < 1e-9 or line2.Length < 1e-9:
                     print("# Error: Failed to create valid boundary lines for Floor Type '{0}'. Skipping slice.".format(floor_type_name))
                     start_angle = end_angle
                     continue

                # Create CurveLoop
                curve_loop = CurveLoop()
                curve_loop.Append(line1)
                curve_loop.Append(arc)
                curve_loop.Append(line2)

                if curve_loop.IsOpen():
                    print("# Error: Pie slice CurveLoop is open for Type '{0}'. Attempting self-intersection check/fix (simple)".format(floor_type_name))
                    # Basic check: Does it look like a pie slice?
                    if curve_loop.NumberOfCurves() == 3:
                         # Sometimes forcing closure helps if endpoints are *almost* identical
                         curve_loop.Close() # See if API can handle tiny gaps
                         if curve_loop.IsOpen(): # Check again
                              print("# Error: CurveLoop remains open after Close() attempt for '{0}'. Skipping.".format(floor_type_name))
                              start_angle = end_angle
                              continue
                    else:
                         print("# Error: Unexpected number of curves in loop for '{0}'. Skipping.".format(floor_type_name))
                         start_angle = end_angle
                         continue

                loops.Add(curve_loop)


            # Create Filled Region if loops were generated
            if loops.Count > 0:
                try:
                    # Transaction is handled externally by the C# wrapper
                    FilledRegion.Create(doc, fr_type_id_to_use, active_view_id, loops)
                    # print("# Created slice/circle for Floor Type: '{0}'".format(floor_type_name)) # Optional Debug
                except Exception as create_err:
                    print("# Error creating Filled Region for Floor Type '{0}': {1}".format(floor_type_name, create_err))
                    # Print geometry info for debugging
                    print("#   Center: {0}, Radius: {1}, StartAngle: {2}, EndAngle: {3}".format(center_point, PIE_CHART_RADIUS, start_angle, end_angle))

        except Exception as geom_err:
            print("# Error during geometry creation for Floor Type '{0}': {1}".format(floor_type_name, geom_err))
            import traceback
            # print(traceback.format_exc()) # Verbose debug

        # Update start angle for the next slice (regardless of success for this slice)
        start_angle = end_angle
        # Handle potential floating point creep if we go past 2*PI
        if start_angle >= 2 * Math.PI:
             start_angle -= 2 * Math.PI


    print("# Pie chart creation process finished.")

except Exception as global_err:
    # Catch any unexpected error during the overall process
    import traceback
    print("# An unexpected error occurred during pie chart script execution:")
    print(traceback.format_exc())

# --- End of Script ---