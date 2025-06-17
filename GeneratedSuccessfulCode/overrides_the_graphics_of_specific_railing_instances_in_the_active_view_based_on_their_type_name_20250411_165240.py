# Purpose: This script overrides the graphics of specific railing instances in the active view based on their type name.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory,
    OverrideGraphicSettings, Color, View,
    ElementId, ElementType
)
# Note: Railing class is in Autodesk.Revit.DB.Architecture, but not needed for this logic.

# --- Configuration ---
target_type_name_substring = "Guardrail" # Case-insensitive check will be performed
override_color = Color(255, 165, 0) # Orange

# --- Get Active View ---
# Assume 'doc' is pre-defined and available
active_view = doc.ActiveView

# Proceed only if active_view is valid and allows overrides
if active_view and isinstance(active_view, View) and not active_view.IsTemplate and active_view.AreGraphicsOverridesAllowed():

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()
    # Set the projection line color
    override_settings.SetProjectionLineColor(override_color)

    # --- Collect Railing instances in the active view ---
    railing_collector = FilteredElementCollector(doc, active_view.Id)\
                        .OfCategory(BuiltInCategory.OST_Railings)\
                        .WhereElementIsNotElementType()

    railings_overridden_count = 0
    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the external runner.
    for railing in railing_collector:
        try:
            # Get the ElementType (RailingType) of the railing instance
            element_type_id = railing.GetTypeId()
            if element_type_id != ElementId.InvalidElementId:
                railing_type = doc.GetElement(element_type_id)
                # Check if railing_type is retrieved and is an ElementType
                if railing_type and isinstance(railing_type, ElementType):
                    # Get the 'Type Name' (which is the Name property of the ElementType)
                    # Handle potential null or empty names gracefully
                    type_name = Element.Name.__get__(railing_type) # Use property getter for safety

                    # Check if the Type Name contains the target substring (case-insensitive)
                    if type_name and target_type_name_substring.lower() in type_name.lower():
                        # Apply the override settings to the railing instance in the active view
                        active_view.SetElementOverrides(railing.Id, override_settings)
                        railings_overridden_count += 1
        except Exception as e:
            # Silently ignore railings that might cause errors during processing
            # print("Error processing railing {}: {}".format(railing.Id, e)) # Optional Debug
            pass

    # Optional: Print success message (commented out as per requirements)
    # print("# Applied orange projection line override to {} railings whose Type Name contains '{}' in view '{}'.".format(railings_overridden_count, target_type_name_substring, active_view.Name))
# else:
    # Optional: Handle case where the view is not suitable (commented out)
    # print("# Error: Requires an active, non-template graphical view where overrides are allowed.")