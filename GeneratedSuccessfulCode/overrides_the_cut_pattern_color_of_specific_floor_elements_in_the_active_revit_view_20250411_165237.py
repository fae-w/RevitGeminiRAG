# Purpose: This script overrides the cut pattern color of specific floor elements in the active Revit view.

﻿# Purpose: This script overrides the cut pattern color to magenta for all Floor elements
#          whose 'Type Name' contains 'Composite Deck' in the active Revit view.

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Floor,
    FloorType,
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    FillPatternTarget, # Needed for refining solid pattern search
    ElementId,
    BuiltInCategory,
    View
)
# from System import String # Not strictly required for .lower() method in IronPython

# --- Configuration ---
# Target substring in Floor Type Name
type_name_substring = "Composite Deck"
# Override color (Magenta)
override_color = Color(255, 0, 255)

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view found or the active 'view' is not a valid View element.")
    # Use raise Exception() for better error handling in RevitPythonShell/pyRevit
    raise ValueError("No active view found or it's not a valid View.")
else:
    # --- Find Solid Fill Pattern Element Id ---
    solid_pattern_id = ElementId.InvalidElementId
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement).WhereElementIsNotElementType()
    solid_fill_elements = []
    for pattern in fill_pattern_collector:
        try:
            fill_patt = pattern.GetFillPattern()
            # Check if the pattern object is valid and if it's a solid fill
            if fill_patt and fill_patt.IsSolidFill:
                solid_fill_elements.append(pattern)
        except Exception as e:
            # Some patterns might throw errors on GetFillPattern(), ignore them
            # print("# Debug: Error checking fill pattern {}: {}".format(pattern.Id, e)) # Escaped debug
            pass

    if solid_fill_elements:
        # Prefer Drafting patterns if available, otherwise take any solid fill
        drafting_solid = [p for p in solid_fill_elements if p.GetFillPattern().Target == FillPatternTarget.Drafting]
        if drafting_solid:
            solid_pattern_id = drafting_solid[0].Id
        else:
            # Fallback to the first solid fill pattern found, regardless of target
            solid_pattern_id = solid_fill_elements[0].Id
            # print("# Debug: Using a non-Drafting solid fill pattern.") # Escaped optional debug
    else:
        print("# Warning: Could not find any 'Solid fill' pattern element using IsSolidFill. Color override will be applied without explicit pattern ID.")

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set Cut Fill Pattern Colors to Magenta
    override_settings.SetCutForegroundPatternColor(override_color)
    override_settings.SetCutBackgroundPatternColor(override_color)

    # Set Cut Fill Pattern Visibility to True
    override_settings.SetCutBackgroundPatternVisible(True)
    override_settings.SetCutForegroundPatternVisible(True)

    # Set Cut Fill Pattern to Solid Fill if found
    if solid_pattern_id != ElementId.InvalidElementId:
        override_settings.SetCutForegroundPatternId(solid_pattern_id)
        override_settings.SetCutBackgroundPatternId(solid_pattern_id)
        # print("# Debug: Using solid fill pattern ID: {}".format(solid_pattern_id)) # Escaped optional debug
    # else: # If no solid pattern ID found, the color settings alone will make it appear solid.
        # pass # No action needed

    # --- Collect and Filter Floors ---
    # Collect all Floor instances in the document
    floor_collector = FilteredElementCollector(doc)\
                     .OfCategory(BuiltInCategory.OST_Floors)\
                     .WhereElementIsNotElementType()

    floors_overridden_count = 0
    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the C# wrapper.
    for floor in floor_collector:
        if isinstance(floor, Floor):
            try:
                floor_type_id = floor.GetTypeId()
                if floor_type_id != ElementId.InvalidElementId:
                    floor_type = doc.GetElement(floor_type_id)
                    # Ensure the retrieved element is indeed a FloorType
                    if isinstance(floor_type, FloorType):
                        type_name = floor_type.Name
                        # Case-insensitive check for the substring
                        if type_name_substring.lower() in type_name.lower():
                            # Apply the override to this specific floor element in the active view
                            active_view.SetElementOverrides(floor.Id, override_settings)
                            floors_overridden_count += 1
            except Exception as e:
                print("# Error processing Floor {}: {}".format(floor.Id, e)) # Escaped format
                # Continue processing other elements if one fails

    # Provide feedback to the user
    if floors_overridden_count > 0:
        print("# Applied magenta cut pattern override to {} Floor(s) with 'Type Name' containing '{}' in the active view.".format(floors_overridden_count, type_name_substring)) # Escaped format
    else:
        print("# No Floor elements found with 'Type Name' containing '{}' to apply overrides.".format(type_name_substring)) # Escaped format