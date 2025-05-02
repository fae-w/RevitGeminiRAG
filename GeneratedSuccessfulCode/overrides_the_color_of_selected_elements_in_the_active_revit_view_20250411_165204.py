# Purpose: This script overrides the color of selected elements in the active Revit view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Color and Exceptions
from Autodesk.Revit.DB import (
    ElementId,
    OverrideGraphicSettings,
    Color,
    View
)
import System # For exception handling

# --- Configuration ---
# Define the desired color (Purple: R=128, G=0, B=128)
override_color = Color(128, 0, 128)

# --- Script Core Logic ---

# Get the current selection
selection = uidoc.Selection
selected_ids = selection.GetElementIds()

# Check if any elements are selected
if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected. Nothing to override.")
else:
    # Get the active view
    active_view = doc.ActiveView
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
        print("# Error: No active graphical view found or active view is a template.")
        # Exit script cleanly if no suitable view
        import sys
        sys.exit()

    # Create the override graphic settings object
    override_settings = OverrideGraphicSettings()

    # Set the projection line color
    override_settings.SetProjectionLineColor(override_color)
    # Optionally, set other properties like cut lines, patterns etc.
    # override_settings.SetCutLineColor(override_color)
    # override_settings.SetSurfaceForegroundPatternColor(override_color)
    # override_settings.SetCutForegroundPatternColor(override_color)

    # --- Apply Overrides to Selected Elements ---
    applied_count = 0
    error_count = 0

    for element_id in selected_ids:
        try:
            # Apply the override settings to the element in the active view
            active_view.SetElementOverrides(element_id, override_settings)
            applied_count += 1
        except System.Exception as e:
            # print(f"# Error applying override to Element ID {{element_id}}: {{e.Message}}") # Optional detailed error message
            error_count += 1

    # --- Final Summary ---
    if applied_count > 0:
        print("# Successfully applied color override to {} selected elements.".format(applied_count))
    if error_count > 0:
        print("# Encountered {} errors while applying overrides.".format(error_count))
    elif applied_count == 0 and selected_ids.Count > 0:
         print("# No overrides were successfully applied, though elements were selected. Check for errors or view compatibility.")