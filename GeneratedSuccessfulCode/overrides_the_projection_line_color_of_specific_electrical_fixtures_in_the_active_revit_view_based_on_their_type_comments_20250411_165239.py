# Purpose: This script overrides the projection line color of specific electrical fixtures in the active Revit view based on their type comments.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
# Import base DB classes
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory,
    OverrideGraphicSettings, Color, View,
    BuiltInParameter, ElementId, ElementType
)
# Removed problematic import: from Autodesk.Revit.DB.Electrical import ElectricalFixture

# --- Configuration ---
target_type_comment = "LED"
override_color = Color(0, 255, 255) # Cyan

# --- Get Active View ---
# Ensure uidoc is available, otherwise try getting it from __revit__ if available
if 'uidoc' not in globals() and '__revit__' in globals():
    uidoc = __revit__.ActiveUIDocument
elif 'uidoc' not in globals():
     # Handle case where uidoc might not be directly available
     # This part might need adjustment depending on the execution context
     # For simplicity, we'll assume uidoc is available or derivable
     pass

# Proceed only if uidoc and doc are valid
if 'uidoc' in globals() and uidoc and uidoc.Document:
    doc = uidoc.Document # Ensure doc is assigned from uidoc if not pre-defined
    active_view = doc.ActiveView
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate or not active_view.AreGraphicsOverridesAllowed():
        # Error: Requires an active, non-template graphical view where overrides are allowed.
        # Silently exit if the view is not suitable.
        pass
    else:
        # --- Create Override Settings ---
        override_settings = OverrideGraphicSettings()
        # Set the projection line color
        override_settings.SetProjectionLineColor(override_color)

        # --- Collect Electrical Fixtures in the active view ---
        fixture_collector = FilteredElementCollector(doc, active_view.Id)\
                            .OfCategory(BuiltInCategory.OST_ElectricalFixtures)\
                            .WhereElementIsNotElementType()

        fixtures_overridden_count = 0
        # --- Apply Overrides ---
        # Note: The script runs inside an existing transaction provided by the external runner.
        for fixture in fixture_collector:
            try:
                # Get the ElementType (Symbol) of the fixture instance
                element_type_id = fixture.GetTypeId()
                if element_type_id != ElementId.InvalidElementId:
                    fixture_type = doc.GetElement(element_type_id)
                    # Check if fixture_type is retrieved and is an ElementType
                    if fixture_type and isinstance(fixture_type, ElementType):
                        # Get the 'Type Comments' parameter from the ElementType
                        type_comments_param = fixture_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)

                        # Check if the parameter exists and its value matches the target
                        if type_comments_param and type_comments_param.HasValue and type_comments_param.AsString() == target_type_comment:
                            # Apply the override settings to the fixture instance in the active view
                            active_view.SetElementOverrides(fixture.Id, override_settings)
                            fixtures_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Failed to process fixture {{fixture.Id}}. Error: {{e}}") # Escaped Optional debug
                # Silently ignore fixtures that might cause errors
                pass

        # Optional: Print success message (commented out as per requirements)
        # print(f"# Applied cyan projection line override to {{fixtures_overridden_count}} electrical fixtures with Type Comments '{{target_type_comment}}' in view '{{active_view.Name}}'.")
# else:
    # Optional: Handle case where uidoc or doc is not available (commented out)
    # print("# Error: Could not access the active document or UI document.")