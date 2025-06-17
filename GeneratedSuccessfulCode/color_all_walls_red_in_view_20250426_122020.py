# Purpose: This script colors all walls red in the active Revit view by changing their projection line color.

import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Byte if used, though integers often suffice

# Import necessary classes from Autodesk.Revit.DB
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall,
    OverrideGraphicSettings, Color, View, ElementId, ViewType # Added ViewType
)

# --- Configuration ---
# Define the override color (Red)
override_color = Color(255, 0, 0)

# --- Get Active View ---
# Ensure uidoc is available, otherwise try getting it from __revit__
# This check might be redundant depending on the execution environment setup,
# but provides some robustness if uidoc isn't directly injected.
# Note: The provided environment guarantees uidoc and doc are available.
active_view = doc.ActiveView

# --- Validate Active View ---
# Proceed only if there is an active view, it's a graphical view, and not a template
if active_view and isinstance(active_view, View) and not active_view.IsTemplate and active_view.ViewType != ViewType.Schedule:

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()
    # Set the projection line color to red
    override_settings.SetProjectionLineColor(override_color)
    # Optional: uncomment below to also set surface patterns (might be better for 3D)
    # override_settings.SetSurfaceForegroundPatternColor(override_color)
    # override_settings.SetSurfaceForegroundPatternId(ElementId(solid_fill_pattern_id)) # Requires finding solid fill pattern ID
    # override_settings.SetSurfaceBackgroundPatternColor(override_color) # Less common

    # --- Collect Walls in Active View ---
    # Filter for wall instances visible in the active view
    collector = FilteredElementCollector(doc, active_view.Id)
    wall_collector = collector.OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    walls_overridden_count = 0
    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the external runner.
    for wall in wall_collector:
        # Basic check if it's a Wall (though filter should ensure this)
        if isinstance(wall, Wall):
            try:
                # Apply the override settings to the wall element in the active view
                active_view.SetElementOverrides(wall.Id, override_settings)
                walls_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Failed to override wall {{{{{{{{wall.Id}}}}}}}}. Error: {{{{{{{{e}}}}}}}}") # Optional escaped debug
                # Silently ignore walls that might cause errors during override application
                pass

    # print(f"# Applied red projection line override to {{{{{{{{walls_overridden_count}}}}}}}} walls in view '{{{{{{{{active_view.Name}}}}}}}}'.") # Optional escaped output
# else:
    # No action needed if the view is not suitable (e.g., schedule, template)
    # print("# Info: Active view is not a graphical view or is a template. No overrides applied.") # Optional escaped info