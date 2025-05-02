# Purpose: This script highlights lighting fixtures exceeding a specified wattage threshold in red.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Required for UIDocument
clr.AddReference('System') # Required for Color and Exceptions
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    # LightingFixture removed - it's in Autodesk.Revit.DB.Electrical and not needed for category filtering
    ElementId,
    OverrideGraphicSettings,
    Color,
    View,
    Parameter,
    BuiltInParameter,
    StorageType
)
import System # For exception handling

# --- Configuration ---
# Define the override color (Red: R=255, G=0, B=0)
override_color = Color(255, 0, 0)
# Define the Wattage threshold
wattage_threshold = 100.0 # Assuming the parameter unit is Watts

# --- Get Active View ---
# Ensure uidoc is available (provided by the execution environment)
if uidoc is None:
    print("# Error: UIDocument is not available.")
    import sys
    sys.exit()

active_view = uidoc.ActiveView
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
# Optionally set a solid fill pattern if desired (requires finding a Solid Fill Pattern ElementId)
# override_settings.SetSurfaceForegroundPatternVisible(True)
# Consider Cut patterns if elements can be cut in the view
# override_settings.SetCutLineColor(override_color)
# override_settings.SetCutForegroundPatternColor(override_color)

# --- Find Elements and Apply Overrides ---
# Ensure doc is available (provided by the execution environment)
if doc is None:
    print("# Error: Document is not available.")
    import sys
    sys.exit()

# Collect Lighting Fixtures in the active view
collector = FilteredElementCollector(doc, active_view.Id)
lighting_fixtures = collector.OfCategory(BuiltInCategory.OST_LightingFixtures).WhereElementIsNotElementType().ToElements()

applied_count = 0
skipped_no_param = 0
skipped_wrong_type = 0
skipped_below_threshold = 0
error_count = 0

print("# Processing {} Lighting Fixtures in view '{}'...".format(len(lighting_fixtures), active_view.Name))

# Note: Transaction is handled externally by the C# wrapper/executor

for fixture in lighting_fixtures:
    try:
        # Attempt to get the 'Wattage' parameter
        # Try BuiltInParameter first (FBX_LIGHT_WATTAGE seems less common for actual wattage, consider others if needed)
        # Common built-in parameters for electrical load might be more reliable depending on family setup
        # E.g., BuiltInParameter.RBS_ELEC_APPARENT_LOAD or others defined in the family
        wattage_param = fixture.get_Parameter(BuiltInParameter.FBX_LIGHT_WATTAGE) # Keep as fallback or remove if unreliable

        # More reliable: Check standard electrical parameters if FBX one fails or isn't standard
        if not wattage_param:
             # Try apparent load (often in VA, might need conversion or use as is if threshold is adjusted)
             # wattage_param = fixture.get_Parameter(BuiltInParameter.RBS_ELEC_APPARENT_LOAD)
             # Check for 'Wattage' by name as a common custom or shared parameter
             wattage_param = fixture.LookupParameter("Wattage")

        if wattage_param:
            # Check if the parameter stores a number (Double)
            # Note: Wattage is often stored as Double even if displayed as Integer
            if wattage_param.StorageType == StorageType.Double or wattage_param.StorageType == StorageType.Integer:
                # Revit API often returns internal units (e.g., Watts for power). Check family if unsure.
                wattage_value = wattage_param.AsDouble() # AsDouble works for Integer too

                # Check if the value exceeds the threshold
                if wattage_value > wattage_threshold:
                    # Apply the override
                    active_view.SetElementOverrides(fixture.Id, override_settings)
                    applied_count += 1
                else:
                    # Value is below threshold
                    skipped_below_threshold += 1
            else:
                # Parameter is not a number type
                # print("# Skipping Fixture ID {}: 'Wattage' parameter is not a number (Type: {}).".format(fixture.Id, wattage_param.StorageType))
                skipped_wrong_type += 1
        else:
            # Parameter not found
            # print("# Skipping Fixture ID {}: 'Wattage' parameter not found.".format(fixture.Id))
            skipped_no_param += 1
    except System.Exception as e:
        # print("# Error processing Fixture ID {}: {}".format(fixture.Id, e.Message)) # Optional detailed error
        error_count += 1

# --- Final Summary ---
print("# Override process complete.")
print("# Applied red override to {} lighting fixtures with Wattage > {}W.".format(applied_count, wattage_threshold))
if skipped_no_param > 0:
    print("# Skipped {} fixtures: 'Wattage' parameter not found.".format(skipped_no_param))
if skipped_wrong_type > 0:
    print("# Skipped {} fixtures: 'Wattage' parameter not a numeric type.".format(skipped_wrong_type))
if skipped_below_threshold > 0:
    print("# Skipped {} fixtures: Wattage <= {}W.".format(skipped_below_threshold, wattage_threshold))
if error_count > 0:
    print("# Encountered errors processing {} fixtures.".format(error_count))
if applied_count == 0 and len(lighting_fixtures) > 0 and error_count == 0:
    print("# Note: No fixtures met the criteria or all applicable fixtures were skipped.")