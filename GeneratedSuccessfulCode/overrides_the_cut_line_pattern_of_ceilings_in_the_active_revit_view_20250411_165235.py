# Purpose: This script overrides the cut line pattern of ceilings in the active Revit view.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Ceiling,
    OverrideGraphicSettings,
    LinePatternElement,
    ElementId,
    View,
    ViewType # To potentially check view type
)

# --- Configuration ---
# The exact name of the line pattern might vary based on Revit language/template
target_line_pattern_name = "Overhead"

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined
active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or the active view is a template.")
    # Optional check if the view is actually an RCP as requested
    # if active_view and active_view.ViewType != ViewType.CeilingPlan:
    #     print("# Warning: The active view '{}' is not a Reflected Ceiling Plan.".format(active_view.Name))
else:
    # --- Find Target Line Pattern Element Id ---
    overhead_pattern_id = ElementId.InvalidElementId
    line_pattern_collector = FilteredElementCollector(doc).OfClass(LinePatternElement)

    found_pattern = False
    for pattern in line_pattern_collector:
        try:
            if pattern.Name == target_line_pattern_name:
                overhead_pattern_id = pattern.Id
                found_pattern = True
                # print("# Debug: Found '{}' line pattern with ID: {}".format(target_line_pattern_name, overhead_pattern_id)) # Optional debug
                break
        except Exception as e:
            # Some elements might not have a Name property or cause other issues
            # print("# Debug: Error accessing pattern name for ID {}: {}".format(pattern.Id, e)) # Optional debug
            pass

    if not found_pattern:
        print("# Error: Line pattern named '{}' not found in the document. Cannot apply override.".format(target_line_pattern_name))
    else:
        # --- Create Override Settings ---
        override_settings = OverrideGraphicSettings()
        override_settings.SetCutLinePatternId(overhead_pattern_id)
        # Note: Other cut line properties (color, weight) are not modified by default.
        # To set them, uncomment and adjust below:
        # override_settings.SetCutLineColor(Color(0, 0, 0)) # Example: Black
        # override_settings.SetCutLineWeight(5) # Example: Weight 5

        # --- Collect Ceiling Elements in Active View ---
        ceiling_collector = FilteredElementCollector(doc, active_view.Id)\
                            .OfCategory(BuiltInCategory.OST_Ceilings)\
                            .WhereElementIsNotElementType()

        ceilings_to_override = list(ceiling_collector)
        overridden_count = 0

        # --- Apply Overrides ---
        # Assumes transaction is handled externally by the C# wrapper.
        if ceilings_to_override:
            for ceiling in ceilings_to_override:
                # Double check type just in case, though collector should handle it
                if isinstance(ceiling, Ceiling):
                    try:
                        active_view.SetElementOverrides(ceiling.Id, override_settings)
                        overridden_count += 1
                    except Exception as e:
                        print("# Error applying override to Ceiling {}: {}".format(ceiling.Id, e))
        # else: # Optional debug/info
            # print("# Debug: No Ceiling elements found by the collector in view '{}'.".format(active_view.Name)) # Optional debug


        # --- Feedback ---
        if overridden_count > 0:
            print("# Applied '{}' cut line pattern override to {} Ceiling(s) in view '{}'.".format(target_line_pattern_name, overridden_count, active_view.Name))
        elif found_pattern: # Only print this if the pattern was found but no ceilings were applicable/found
            print("# No Ceiling elements found or overridden in view '{}'.".format(active_view.Name))
        # If the pattern wasn't found, the error message from earlier suffices.