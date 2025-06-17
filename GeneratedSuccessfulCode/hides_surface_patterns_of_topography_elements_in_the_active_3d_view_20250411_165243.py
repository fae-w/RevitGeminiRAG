# Purpose: This script hides surface patterns of topography elements in the active 3D view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    ElementId,
    View,
    View3D # Specifically needed for checking view type
)
import System # For exception handling

# Get the active view
active_view = doc.ActiveView

# Check if the active view is a 3D view and not a template
if not active_view or not isinstance(active_view, View3D) or active_view.IsTemplate:
    print("# Error: The active view is not a 3D view or is a view template.")
else:
    # Define the override settings
    override_settings = OverrideGraphicSettings()
    override_settings.SetSurfaceForegroundPatternVisible(False)
    override_settings.SetSurfaceBackgroundPatternVisible(False)

    # Collect topography elements visible in the active 3D view
    # OST_Topography covers both TopographySurface (legacy) and Toposolid (newer)
    collector = FilteredElementCollector(doc, active_view.Id)\
                    .OfCategory(BuiltInCategory.OST_Topography)\
                    .WhereElementIsNotElementType()

    elements_to_override = collector.ToElements()
    applied_count = 0
    error_count = 0

    if not elements_to_override:
        print("# Info: No topography elements found in the active 3D view.")
    else:
        # Apply the overrides (Transaction managed externally)
        for element in elements_to_override:
            try:
                active_view.SetElementOverrides(element.Id, override_settings)
                applied_count += 1
            except System.Exception as e:
                print("# Error applying override to element ID {}: {}".format(element.Id, e))
                error_count += 1

        # Optional: Print summary (commented out per requirements)
        # if applied_count > 0:
        #     print("# Successfully turned off surface patterns for {} topography elements in view '{}'.".format(applied_count, active_view.Name))
        # if error_count > 0:
        #     print("# Failed to apply overrides for {} elements.".format(error_count))
        # if applied_count == 0 and error_count == 0 and elements_to_override:
        #      print("# No overrides were applied, though elements were found. Check for potential issues.")