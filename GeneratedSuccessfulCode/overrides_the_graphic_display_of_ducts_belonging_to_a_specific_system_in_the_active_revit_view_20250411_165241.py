# Purpose: This script overrides the graphic display of ducts belonging to a specific system in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for String comparison if using FilterStringRule

# Import base DB classes
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory,
    OverrideGraphicSettings, ElementId, View,
    LinePatternElement,
    BuiltInParameter, ParameterValueProvider, FilterStringRule, FilterStringEquals,
    ElementParameterFilter
)
# Import Mechanical specific classes
from Autodesk.Revit.DB.Mechanical import Duct # Duct class is in Autodesk.Revit.DB.Mechanical

from System import String # Explicit import for clarity if needed

# --- Configuration ---
target_system_name = "Exhaust Air"
target_line_pattern_name = "DashDot"

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate or not active_view.AreGraphicsOverridesAllowed():
    # Error: Requires an active, non-template graphical view where overrides are allowed.
    pass # Exit gracefully if the view is not suitable
else:
    # --- Find the Line Pattern Element ---
    dash_dot_pattern_id = ElementId.InvalidElementId
    line_pattern_collector = FilteredElementCollector(doc).OfClass(LinePatternElement)
    for pattern in line_pattern_collector:
        # Use GetLinePattern() if available or Name property directly if sufficient
        # For robustness, could check pattern.GetLinePattern().Name if direct Name fails
        if pattern.Name == target_line_pattern_name:
            dash_dot_pattern_id = pattern.Id
            break

    if dash_dot_pattern_id == ElementId.InvalidElementId:
        # Error: Line pattern '{target_line_pattern_name}' not found in the document.
        pass # Exit if pattern not found
    else:
        # --- Create Override Settings ---
        override_settings = OverrideGraphicSettings()
        # Set the projection line pattern
        override_settings.SetProjectionLinePatternId(dash_dot_pattern_id)

        # --- Define Parameter Filter for System Classification ---
        # Get the ElementId for the BuiltInParameter 'RBS_SYSTEM_CLASSIFICATION_PARAM'
        param_id = ElementId(BuiltInParameter.RBS_SYSTEM_CLASSIFICATION_PARAM)
        # Create a ParameterValueProvider for this parameter
        param_provider = ParameterValueProvider(param_id)
        # Create the filter rule: check if the parameter value equals the target system name (case-sensitive)
        # Use FilterStringEquals() for exact match. Set caseSensitive argument to True or False.
        # Assuming case-sensitive comparison is desired for system names like "Exhaust Air" vs "exhaust air"
        # Note: Some parameters might store system name differently (e.g., RBS_DUCT_SYSTEM_TYPE_PARAM uses System Type Name)
        # RBS_SYSTEM_CLASSIFICATION_PARAM usually holds the classification like "Exhaust Air", "Supply Air", etc.
        filter_rule = FilterStringRule(param_provider, FilterStringEquals(), target_system_name, True) # Case-sensitive match
        # Create the ElementParameterFilter from the rule
        param_filter = ElementParameterFilter(filter_rule)

        # --- Collect Ducts matching the criteria in the active view ---
        duct_collector = FilteredElementCollector(doc, active_view.Id)\
                         .OfCategory(BuiltInCategory.OST_DuctCurves)\
                         .WhereElementIsNotElementType()\
                         .WherePasses(param_filter) # Apply the parameter filter

        ducts_overridden_count = 0
        # --- Apply Overrides ---
        # Note: The script runs inside an existing transaction provided by the external runner.
        for duct in duct_collector:
            # The collector already filters for Ducts by category, but an explicit check is safe.
            if isinstance(duct, Duct):
                try:
                    # Apply the override settings to the duct element in the active view
                    active_view.SetElementOverrides(duct.Id, override_settings)
                    ducts_overridden_count += 1
                except Exception as e:
                    # Debug: Failed to override duct {duct.Id}. Error: {e}
                    # Silently ignore ducts that might cause errors during override application
                    pass

        # Optional: Print success message (commented out as per requirements)
        # print(f"Applied '{target_line_pattern_name}' projection line pattern override to {ducts_overridden_count} ducts belonging to '{target_system_name}' system in view '{active_view.Name}'.")