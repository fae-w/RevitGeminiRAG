# Purpose: This script overrides the color of Revit text notes in the active view based on their font.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    Color,
    ElementId,
    TextNote, # Specific class for Text Notes
    BuiltInParameter,
    StorageType
)

# Get the active view
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
    # Stop processing if no active view
    active_view = None
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: View '{0}' (Type: {1}) does not support graphic overrides.".format(active_view.Name, active_view.ViewType))
     # Stop processing if view doesn't support overrides
     active_view = None


if active_view:
    # Define the target color (Green)
    green_color = Color(0, 128, 0) # Standard Green
    # green_color = Color(0, 255, 0) # Bright Green

    # Create OverrideGraphicSettings
    override_settings = OverrideGraphicSettings()
    # Set projection line color (this typically affects Text Note color)
    override_settings.SetProjectionLineColor(green_color)

    # Collector for Text Notes in the active view
    collector = FilteredElementCollector(doc, active_view.Id)
    collector.OfCategory(BuiltInCategory.OST_TextNotes)
    collector.WhereElementIsNotElementType() # We want instances, not types

    # Parameter name and value to check
    font_param_bip = BuiltInParameter.TEXT_FONT
    target_font_name = "Arial" # Case-sensitive comparison

    # Iterate through Text Notes and collect IDs
    elements_to_override_ids = []
    for text_note in collector:
        # Get the 'Text Font' parameter using BuiltInParameter
        font_param = text_note.get_Parameter(font_param_bip)

        # Check if parameter exists, has a value, is a string, and matches 'Arial'
        if font_param and font_param.HasValue and font_param.StorageType == StorageType.String:
            param_value = font_param.AsString()
            # Ensure param_value is not None before comparing
            if param_value and param_value == target_font_name:
                elements_to_override_ids.append(text_note.Id)

    # Apply overrides (No Transaction needed per instructions)
    if elements_to_override_ids:
        for element_id in elements_to_override_ids:
            try:
                active_view.SetElementOverrides(element_id, override_settings)
            except Exception as e:
                print("# Warning: Failed to override element {0} in view '{1}'. Error: {2}".format(element_id.IntegerValue, active_view.Name, e))
        # print("# Applied green override to {0} text notes with font '{1}' in view '{2}'.".format(len(elements_to_override_ids), target_font_name, active_view.Name)) # Optional log
    else:
        print("# No Text Notes with font '{0}' found in the active view '{1}'.".format(target_font_name, active_view.Name))

# else: Handled by initial view check prints