# Purpose: This script overrides the graphic settings of structural foundations below the active view's cut plane to display them with a dashed line pattern.

﻿import clr
clr.AddReference('RevitAPI')
# clr.AddReference('System.Collections') # Not strictly needed for this specific code

# Required for List generic type hint, though might work without if ToElements() handles it
# from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId,
    LogicalAndFilter, ElementCategoryFilter, BoundingBoxIntersectsFilter, Outline, XYZ,
    OverrideGraphicSettings, LinePatternElement, ViewPlan, ViewSection, View,
    PlanViewPlane, Level # Added Level, PlanViewPlane
    # BuiltInParameter # Not directly used here
)

# --- Configuration ---
target_category = BuiltInCategory.OST_StructuralFoundation
dashed_line_pattern_name = "Dash" # Common dashed line pattern name, adjust if different in your project
tolerance = 0.001 # Small tolerance for floating point comparisons (in feet)
large_coordinate = 10000.0 # Large dimension for filter box (in feet) - adjust if models exceed this size significantly
# --- End Configuration ---

# Get the active view
active_view = doc.ActiveView

# --- Pre-checks ---
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not valid, not a View instance, or is a template.")
# Check if the view type supports a relevant cut plane (Plan or Section)
elif not isinstance(active_view, (ViewPlan, ViewSection)):
     print("# Error: Active view must be a Plan or Section view to determine a cut plane.")
else:
    # Get the view range associated with the view
    view_range = active_view.GetViewRange()

    if not view_range:
        print("# Error: Could not retrieve the view range for the active view.")
    else:
        cut_plane_z = None # Initialize to None
        try:
            # Get the Level ID associated with the cut plane in the view range
            cut_plane_level_id = view_range.GetLevelId(PlanViewPlane.CutPlane)
            # Get the offset distance from that Level
            cut_plane_offset = view_range.GetOffset(PlanViewPlane.CutPlane)

            if cut_plane_level_id == ElementId.InvalidElementId:
                 print("# Error: Cut plane level is not properly defined in the View Range settings.")
            else:
                # Get the Level element itself
                cut_plane_level = doc.GetElement(cut_plane_level_id)
                if not isinstance(cut_plane_level, Level):
                     print("# Error: Could not retrieve a valid Level element associated with the cut plane.")
                else:
                    # Calculate the absolute Z coordinate of the cut plane
                    # Use ProjectElevation for elevation relative to the project origin
                    cut_plane_z = cut_plane_level.ProjectElevation + cut_plane_offset
                    # print("# Debug: Calculated Cut Plane Z = {{0}}".format(cut_plane_z)) # Optional Debug

        except Exception as e:
            # Catch potential errors during view range access
            print("# Error processing view range or calculating cut plane: {{0}}".format(e))

        # Proceed only if we successfully calculated the cut plane Z
        if cut_plane_z is not None:
            # Find the specified dashed line pattern element
            dashed_pattern_id = ElementId.InvalidElementId
            line_pattern_collector = FilteredElementCollector(doc).OfClass(LinePatternElement)
            for pattern_elem in line_pattern_collector:
                # Case-sensitive comparison, ensure pattern name matches exactly
                if pattern_elem.Name == dashed_line_pattern_name:
                    dashed_pattern_id = pattern_elem.Id
                    break

            if dashed_pattern_id == ElementId.InvalidElementId:
                print("# Error: Could not find a Line Pattern named '{{0}}'.".format(dashed_line_pattern_name))
            else:
                # --- Define Filter Logic ---
                # Define an Outline box representing the space *at and above* the cut plane.
                # We use an inverted BoundingBoxIntersectsFilter, so elements whose bounding box
                # DOES NOT intersect this outline (i.e., are fully below) will be selected.
                # Start the box slightly below the cut plane Z to ensure elements exactly on it are *not* considered below.
                min_pt = XYZ(-large_coordinate, -large_coordinate, cut_plane_z - tolerance)
                max_pt = XYZ(large_coordinate, large_coordinate, cut_plane_z + large_coordinate) # Extend very high up
                filter_outline = Outline(min_pt, max_pt)

                # Create the Bounding Box filter (inverted)
                # Selects elements whose bounding box DOES NOT intersect the filter_outline
                bbox_filter = BoundingBoxIntersectsFilter(filter_outline, True) # True = inverted logic

                # Create the Category filter
                category_filter = ElementCategoryFilter(target_category)

                # Combine the category and geometry filters with AND logic
                final_element_filter = LogicalAndFilter(category_filter, bbox_filter)

                # --- Define Override Settings ---
                override_settings = OverrideGraphicSettings()
                # Set the projection lines (lines seen when not cut) to the dashed pattern
                override_settings.SetProjectionLinePatternId(dashed_pattern_id)
                # Optional: Ensure projection lines are visible if they might be hidden by other settings
                # override_settings.SetProjectionLinesVisible(True)

                # --- Apply Filter and Overrides ---
                # Check if graphics overrides are permitted in this view
                if not active_view.AreGraphicsOverridesAllowed():
                     print("# Error: Graphics overrides are not allowed in the active view.")
                else:
                    # Find elements matching the combined filter criteria *within the active view*
                    collector = FilteredElementCollector(doc, active_view.Id)
                    elements_to_override = collector.WherePasses(final_element_filter).ToElements()

                    if not elements_to_override:
                        print("# Info: No structural foundations found entirely below the cut plane (Z={{0}}) in the active view.".format(cut_plane_z))
                    else:
                        count = 0
                        # Apply overrides to each found element individually
                        # Assumes Transaction is handled externally by the caller (e.g., C# wrapper)
                        for elem in elements_to_override:
                            try:
                                active_view.SetElementOverrides(elem.Id, override_settings)
                                count += 1
                            except Exception as e:
                                # Use standard string formatting for IronPython 2.7 compatibility
                                 print("# Warning: Could not apply override to element ID {{0}}: {{1}}".format(elem.Id, e))
                        if count > 0:
                             print("# Applied dashed line override to {{0}} structural foundations below the cut plane.".format(count))