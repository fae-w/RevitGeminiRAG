# Purpose: This script highlights generic annotations containing 'TBC' in their 'Text' parameter within the active Revit view.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, OverrideGraphicSettings, Color, ElementId, StorageType, Parameter

# Get the active view
active_view = doc.ActiveView
if not active_view:
    raise Exception("No active view found.") # Or handle appropriately if exceptions aren't desired

# Define the target color (Yellow)
yellow_color = Color(255, 255, 0)

# Create OverrideGraphicSettings
override_settings = OverrideGraphicSettings()
# Set line color - this usually affects the boundary or lines within the annotation
override_settings.SetProjectionLineColor(yellow_color)
# You might also want to set pattern color if the annotation has filled regions
# override_settings.SetSurfaceForegroundPatternColor(yellow_color)

# Collector for Generic Annotations in the active view
collector = FilteredElementCollector(doc, active_view.Id)
collector.OfCategory(BuiltInCategory.OST_GenericAnnotation)
collector.WhereElementIsNotElementType()

# Parameter name to check (case-sensitive)
param_name = "Text"
# String to search for (case-sensitive)
search_string = "TBC"

# Iterate through Generic Annotations and collect IDs
elements_to_override_ids = []
for element in collector:
    # Get the 'Text' parameter
    text_param = element.LookupParameter(param_name)

    # Check if parameter exists, has a value, is a string, and contains 'TBC'
    if text_param and text_param.HasValue and text_param.StorageType == StorageType.String:
        param_value = text_param.AsString()
        # Ensure param_value is not None before checking 'in'
        if param_value and search_string in param_value:
            elements_to_override_ids.append(element.Id)

# Apply overrides (No Transaction needed per instructions)
for element_id in elements_to_override_ids:
    active_view.SetElementOverrides(element_id, override_settings)