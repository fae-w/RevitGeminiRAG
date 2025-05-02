# Purpose: This script highlights exterior walls in the active Revit view by changing their projection line color to red.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for Int32
from System import Int32
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall,
    OverrideGraphicSettings, Color, View,
    BuiltInParameter, ParameterValueProvider, FilterIntegerRule, FilterNumericEquals, # Removed FilterableValueRule, kept necessary rule types
    ElementId, ElementParameterFilter
)

# --- Configuration ---
# Define the override color (Red)
override_color = Color(255, 0, 0)
# Define the target wall function enum value (Exterior = 1)
# WallFunction enum: Interior=0, Exterior=1, Foundation=2, Retaining=3, Soffit=4, CoreShaft=5
target_wall_function_enum_value = 1

# --- Get Active View ---
# Ensure uidoc is available, otherwise try getting it from __revit__
if 'uidoc' not in globals() and '__revit__' in globals():
    uidoc = __revit__.ActiveUIDocument
elif 'uidoc' not in globals():
     # If uidoc is not available, we cannot get the active view.
     # This case should ideally be handled by the execution environment.
     # For robustness, add a check or rely on the script failing if uidoc is truly missing.
     # print("# Error: uidoc is not defined in the script scope.") # Optional debug
     pass # Allow potential failure later if uidoc was needed and missing

active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    # print("# Error: Requires an active, non-template graphical view.") # Escaped Optional output
    pass # Do nothing if view is invalid
else:
    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()
    # Set the projection line color
    override_settings.SetProjectionLineColor(override_color)

    # --- Define Parameter Filter for Wall Function ---
    # Get the ElementId for the BuiltInParameter 'FUNCTION_PARAM'
    param_id = ElementId(BuiltInParameter.FUNCTION_PARAM)
    # Create a ParameterValueProvider for this parameter
    param_provider = ParameterValueProvider(param_id)
    # Create the filter rule: check if the parameter value equals the integer value for 'Exterior'
    # The value must be wrapped in System.Int32 for FilterIntegerRule
    filter_value = Int32(target_wall_function_enum_value)
    # Use FilterIntegerRule for comparing integer/enum values
    filter_rule = FilterIntegerRule(param_provider, FilterNumericEquals(), filter_value)
    # Create the ElementParameterFilter from the rule
    param_filter = ElementParameterFilter(filter_rule)

    # --- Collect Walls matching the criteria in the active view ---
    wall_collector = FilteredElementCollector(doc, active_view.Id)\
                     .OfCategory(BuiltInCategory.OST_Walls)\
                     .WhereElementIsNotElementType()\
                     .WherePasses(param_filter) # Apply the parameter filter directly

    walls_overridden_count = 0
    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the external runner.
    for wall in wall_collector:
        # Check if it's actually a Wall (though the filter should ensure this)
        if isinstance(wall, Wall):
            try:
                # Apply the override settings to the wall element in the active view
                active_view.SetElementOverrides(wall.Id, override_settings)
                walls_overridden_count += 1
            except Exception as e:
                # print(f"# Debug: Failed to override wall {{wall.Id}}. Error: {{e}}") # Escaped Optional debug
                # Silently ignore walls that might cause errors during override application
                pass

    # print(f"# Applied red projection line override to {{walls_overridden_count}} exterior walls in view '{{active_view.Name}}'.") # Escaped Optional output