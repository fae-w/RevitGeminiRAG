# Purpose: This script highlights walls exceeding a specified thickness by changing their cut pattern color to red.

# Purpose: This script highlights walls thicker than a specified threshold in the active view by changing their cut pattern color to red in Revit.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Required for List<T> potentially, though maybe not used directly
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall, ElementId,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    View
)
from System.Collections.Generic import List # Required for ICollection type args sometimes

# Define the thickness threshold in feet (6 inches = 0.5 feet)
min_thickness_feet = 0.5

# Define the desired color (Red)
red_color = Color(255, 0, 0)

# Find the "Solid fill" pattern ElementId
solid_fill_pattern_id = ElementId.InvalidElementId
fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
for pattern_elem in fill_pattern_collector:
    if pattern_elem.GetFillPattern().IsSolidFill: # More robust than checking name
        # Check if it's a drafting pattern, which is required for overrides
        if pattern_elem.GetFillPattern().Target == FillPatternTarget.Drafting:
            solid_fill_pattern_id = pattern_elem.Id
            break # Found it

if solid_fill_pattern_id == ElementId.InvalidElementId:
    print("# Error: Could not find a 'Solid fill' drafting pattern in the project.")
else:
    # Get the active view
    active_view = doc.ActiveView
    if not active_view or not isinstance(active_view, View):
        print("# Error: No active view or active view is not a graphical view.")
    else:
        # Collect wall instances in the active view
        collector = FilteredElementCollector(doc, active_view.Id)
        wall_collector = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

        walls_modified_count = 0
        for wall in wall_collector:
            if isinstance(wall, Wall):
                try:
                    wall_thickness = wall.Width
                    if wall_thickness > min_thickness_feet:
                        # Wall meets the thickness criteria, apply overrides
                        override_settings = active_view.GetElementOverrides(wall.Id)

                        # Set Cut Foreground Pattern to Solid Fill
                        override_settings.SetCutForegroundPatternId(solid_fill_pattern_id)
                        # Set Cut Foreground Pattern Color to Red
                        override_settings.SetCutForegroundPatternColor(red_color)
                        # Optional: Ensure pattern is visible (usually default, but good practice)
                        override_settings.SetCutForegroundPatternVisible(True)

                        # Apply the modified overrides to the wall in the view
                        active_view.SetElementOverrides(wall.Id, override_settings)
                        walls_modified_count += 1

                except Exception as e:
                    # print(f"# Debug: Skipping wall {wall.Id}, error accessing Width or applying overrides. Error: {e}") # Escaped
                    pass # Silently skip elements that cause errors

        # print(f"# Applied overrides to {walls_modified_count} walls.") # Escaped Optional output