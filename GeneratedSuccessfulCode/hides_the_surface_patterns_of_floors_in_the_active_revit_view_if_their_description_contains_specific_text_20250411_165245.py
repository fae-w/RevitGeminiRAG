# Purpose: This script hides the surface patterns of floors in the active Revit view if their description contains specific text.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Floor,
    OverrideGraphicSettings,
    Parameter,
    BuiltInParameter,
    ElementId,
    View
)
import System # For exception handling

# --- Configuration ---
# Text to search for in the 'Description' parameter (case-insensitive)
search_text = "Concrete Topping"

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active view found, the active 'view' is not a valid View element, or it is a view template.")
    # Optional: Raise an exception if preferred for automation workflows
    # raise ValueError("Active view is not suitable for applying overrides.")
else:
    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()
    # Set surface pattern visibility to False (off)
    override_settings.SetSurfaceForegroundPatternVisible(False)
    override_settings.SetSurfaceBackgroundPatternVisible(False)

    # --- Collect Floor Elements ---
    floor_collector = FilteredElementCollector(doc)\
                     .OfCategory(BuiltInCategory.OST_Floors)\
                     .WhereElementIsNotElementType()

    floors_overridden_count = 0
    elements_processed = 0
    error_count = 0

    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the C# wrapper.
    for floor in floor_collector:
        elements_processed += 1
        if isinstance(floor, Floor):
            try:
                description_param = None
                # Try common ways to get the 'Description' parameter
                # 1. BuiltInParameter
                bip_param = floor.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION)
                if bip_param and bip_param.HasValue:
                    description_param = bip_param
                else:
                    # 2. LookupParameter by name (fallback)
                    lookup_param = floor.LookupParameter("Description")
                    if lookup_param and lookup_param.HasValue:
                        description_param = lookup_param

                # Check if parameter found and contains the search text
                if description_param:
                    description_value = description_param.AsString()
                    # Perform case-insensitive check
                    if description_value and search_text.lower() in description_value.lower():
                        # Apply the override to this specific floor element in the active view
                        active_view.SetElementOverrides(floor.Id, override_settings)
                        floors_overridden_count += 1

            except System.Exception as e:
                print("# Error processing Floor ID {}: {}".format(floor.Id, e)) # Escaped format
                error_count += 1
        # else: # Uncomment to debug if non-Floor elements are collected (shouldn't happen with current filter)
            # print("# Debug: Skipped non-Floor element ID {}".format(floor.Id)) # Escaped format

    # --- Provide Feedback ---
    if floors_overridden_count > 0:
        print("# Turned off surface patterns for {} Floor(s) containing '{}' in their 'Description' parameter in the active view '{}'.".format(floors_overridden_count, search_text, active_view.Name)) # Escaped format
    else:
         if elements_processed > 0 and error_count == 0:
             print("# No Floor elements found with 'Description' parameter containing '{}' to apply overrides.".format(search_text)) # Escaped format
         elif elements_processed == 0:
             print("# No Floor elements found in the document.")
         elif error_count > 0:
             print("# Processed {} elements, applied overrides to {}, but encountered {} errors.".format(elements_processed, floors_overridden_count, error_count)) # Escaped format