# Purpose: This script overrides the graphic display of selected floors to a solid gray color in the active view.

# Purpose: This script overrides the graphic display settings of selected floor elements in the active Revit view to a solid gray color using a solid fill pattern.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Floor,
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    ElementId,
    BuiltInCategory
)
from System import InvalidOperationException # For potential errors during collection
from System.Collections.Generic import List # For selection handling

# Get the active view
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
    # Use raise Exception() for better error handling in RevitPythonShell/pyRevit
    raise ValueError("No active view found.")

# Get selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected.")
    # Use raise Exception() instead of returning/exiting silently
    raise ValueError("No elements selected.")

# --- Find a Solid Fill Pattern ---
solid_fill_pattern_id = ElementId.InvalidElementId
solid_pattern_found = False
try:
    # Find the first solid fill pattern element
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement).WhereElementIsNotElementType()
    solid_fill_pattern = None
    for fp in fill_pattern_collector:
        fill_pattern = fp.GetFillPattern()
        # Ensure it's a solid fill pattern suitable for surface overrides (typically drafting target, implicitly handled)
        if fill_pattern and fill_pattern.IsSolidFill:
            solid_fill_pattern = fp
            break # Found the first one

    if solid_fill_pattern:
        solid_fill_pattern_id = solid_fill_pattern.Id
        solid_pattern_found = True
    else:
        print("# Error: No solid fill pattern found in the document. Cannot apply solid fill.")
        # Use raise Exception() instead of returning/exiting silently
        raise ValueError("No solid fill pattern found in the document.")

except InvalidOperationException: # Catches if filtering finds nothing or logic errors
    print("# Warning: Error occurred while searching for solid fill pattern.")
    # Use raise Exception() instead of returning/exiting silently
    raise ValueError("Error occurred while searching for solid fill pattern.")
except Exception as e:
    print("# Error finding solid fill pattern: {}".format(e))
    # Use raise Exception() instead of returning/exiting silently
    raise ValueError("Error finding solid fill pattern: {}".format(e))

# Define the gray color
gray_color = Color(128, 128, 128)

# --- Apply Overrides to Selected Floors ---
floors_overridden_count = 0
for elem_id in selected_ids:
    element = doc.GetElement(elem_id)
    if isinstance(element, Floor):
        try:
            ogs = OverrideGraphicSettings()

            # Set surface foreground pattern color to gray
            ogs.SetSurfaceForegroundPatternColor(gray_color)
            ogs.SetSurfaceForegroundPatternVisible(True)
            ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)

            # Set surface background pattern color to gray (for solid fill appearance)
            ogs.SetSurfaceBackgroundPatternColor(gray_color)
            ogs.SetSurfaceBackgroundPatternVisible(True)
            ogs.SetSurfaceBackgroundPatternId(solid_fill_pattern_id)

            # Apply the graphic overrides to the floor in the active view
            active_view.SetElementOverrides(element.Id, ogs)
            floors_overridden_count += 1

        except Exception as e:
            print("# Error setting overrides for Floor {}: {}".format(element.Id, e))
            # Continue processing other elements if one fails

if floors_overridden_count > 0:
    print("# Successfully applied solid gray surface pattern to {} selected floors.".format(floors_overridden_count))
else:
    print("# No floor elements were found in the selection to apply overrides.")