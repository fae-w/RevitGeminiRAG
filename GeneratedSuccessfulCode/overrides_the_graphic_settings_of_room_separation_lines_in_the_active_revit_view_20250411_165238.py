# Purpose: This script overrides the graphic settings of room separation lines in the active Revit view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    ElementId,
    ModelLine # Room Separation Lines are often ModelLines
)

# --- Configuration ---
new_projection_line_weight = 4

# --- Get Active View ---
try:
    active_view = doc.ActiveView
    if not active_view:
        print("# Error: No active view found.")
        active_view = None # Ensure it's None if not found
    elif not isinstance(active_view, View) or active_view.IsTemplate or not active_view.AreGraphicsOverridesAllowed():
        print("# Error: Active view is not suitable for overrides (e.g., template, non-graphical).")
        active_view = None
except AttributeError:
    print("# Error: Could not get active view.")
    active_view = None

if active_view:
    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set the projection line weight
    # Line weights must be between 1 and 16.
    if 1 <= new_projection_line_weight <= 16:
        try:
            override_settings.SetProjectionLineWeight(new_projection_line_weight)
        except Exception as e:
            print("# Error setting projection line weight in OverrideGraphicSettings: {}".format(e))
            override_settings = None # Invalidate settings if failed
    else:
        print("# Error: Line weight {} is invalid. Must be between 1 and 16.".format(new_projection_line_weight))
        override_settings = None

    if override_settings:
        # --- Collect Room Separation Line Elements in the active view ---
        # Room Separation Lines are Detail Lines under the OST_RoomSeparationLines category
        # but filtering by category is usually sufficient.
        collector = FilteredElementCollector(doc, active_view.Id)
        room_sep_collector = collector.OfCategory(BuiltInCategory.OST_RoomSeparationLines).WhereElementIsNotElementType()

        elements_overridden_count = 0
        elements_checked_count = 0
        elements_error_count = 0

        # --- Apply Overrides ---
        for element in room_sep_collector:
            elements_checked_count += 1
            try:
                # Apply the override
                active_view.SetElementOverrides(element.Id, override_settings)
                elements_overridden_count += 1
            except Exception as override_err:
                # print("# Debug: Failed to override element {}: {}".format(element.Id, override_err)) # Optional debug
                elements_error_count += 1

        # Optional: Print a summary message (will appear in RevitPythonShell output if uncommented)
        # print("# Summary: Checked: {}, Overridden: {}, Errors: {}".format(elements_checked_count, elements_overridden_count, elements_error_count))
    # else:
        # Error message printed above where settings failed
        # pass

# else:
    # Error message printed above where view failed
    # pass