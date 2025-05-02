# Purpose: This script highlights Revit elements with warnings by applying a red color override in the active view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Color and Exceptions
from Autodesk.Revit.DB import (
    ElementId,
    OverrideGraphicSettings,
    Color,
    View,
    FailureMessage # Required for GetWarnings
)
import System # For exception handling

# --- Configuration ---
# Define the override color (Red: R=255, G=0, B=0)
override_color = Color(255, 0, 0)

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Requires an active, non-template graphical view to apply overrides.")
    # Exit script cleanly if no suitable view
    import sys
    sys.exit()

# --- Create Override Settings ---
override_settings = OverrideGraphicSettings()
# Override projection lines
override_settings.SetProjectionLineColor(override_color)
# Override surface foreground pattern color for better visibility
override_settings.SetSurfaceForegroundPatternColor(override_color)
# Optionally override other aspects like cut lines, etc.
# override_settings.SetCutLineColor(override_color)
# override_settings.SetCutForegroundPatternColor(override_color)

# --- Identify Elements with Warnings ---
warning_element_ids = set() # Use a set to store unique element IDs
try:
    warnings = doc.GetWarnings()
    if warnings:
        for warning in warnings:
            failing_elements = warning.GetFailingElements()
            if failing_elements:
                for element_id in failing_elements:
                    # Check if the element ID is valid and not ElementId.InvalidElementId
                    if element_id and element_id != ElementId.InvalidElementId:
                        warning_element_ids.add(element_id)
except System.Exception as e:
    print("# Error retrieving warnings: {}".format(e.Message))
    # Exit script cleanly if warnings cannot be retrieved
    import sys
    sys.exit()


# --- Apply Overrides ---
applied_count = 0
error_count = 0

if not warning_element_ids:
    print("# No elements found associated with warnings.")
else:
    print("# Found {} unique elements associated with warnings.".format(len(warning_element_ids)))
    for element_id in warning_element_ids:
        try:
            # Check if element still exists (might have been deleted)
            element = doc.GetElement(element_id)
            if element is not None:
                 # Check if the element can have overrides applied in the current view
                 # Some elements might not be visible or support overrides
                 if active_view.CanApplyElementOverrides(element_id):
                      active_view.SetElementOverrides(element_id, override_settings)
                      applied_count += 1
                 else:
                      # Optionally log elements that cannot have overrides applied in this view
                      # print("# Skipping Element ID {} - Cannot apply override in this view.".format(element_id))
                      error_count += 1 # Count as an error/skip if needed
            else:
                # Optionally log elements that no longer exist
                # print("# Skipping Element ID {} - Element not found.".format(element_id))
                error_count += 1 # Count as an error/skip
        except System.Exception as e:
            # print("# Error applying override to Element ID {}: {}".format(element_id, e.Message)) # Optional detailed error message
            error_count += 1

# --- Final Summary ---
if applied_count > 0:
    print("# Successfully applied red override to {} elements with warnings in view '{}'.".format(applied_count, active_view.Name))
if error_count > 0:
    print("# Encountered {} issues (element not found, not visible, or other error) while applying overrides.".format(error_count))
if applied_count == 0 and len(warning_element_ids) > 0:
     print("# No overrides were successfully applied, though warning elements were identified. Check view visibility or specific element issues.")