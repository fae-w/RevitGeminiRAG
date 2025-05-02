# Purpose: This script highlights floors with a specific thickness in the active Revit view.

﻿import clr
import math

# Add References to RevitAPI and RevitAPIUI
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

# Import necessary classes from Autodesk.Revit.DB
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Floor,
    FloorType,
    ElementId,
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    FillPatternTarget,
    View,
    BuiltInParameter,
    UnitUtils,
    SpecTypeId # Keep for potential future use, but not for the conversion directly
)
# Import UnitTypeId for correct unit conversion in newer Revit versions
try:
    from Autodesk.Revit.DB import UnitTypeId
    _use_unit_type_id = True
except ImportError:
    # Fallback for older Revit versions that might use DisplayUnitType
    from Autodesk.Revit.DB import DisplayUnitType
    _use_unit_type_id = False

# --- Script Core Logic ---

# Define the target thickness in millimeters
target_thickness_mm = 150.0

# Convert mm to internal feet using the correct Unit Identifier
target_thickness_feet = None
if _use_unit_type_id:
    try:
        # Revit 2021+ approach using UnitTypeId
        millimeters_unit_id = UnitTypeId.Millimeters # Use the specific unit ID
        target_thickness_feet = UnitUtils.ConvertToInternalUnits(target_thickness_mm, millimeters_unit_id)
    except Exception: # Broad exception if UnitTypeId exists but fails unexpectedly
        _use_unit_type_id = False # Force fallback

if target_thickness_feet is None and not _use_unit_type_id:
    # Older Revit approach using DisplayUnitType
    try:
        target_thickness_feet = UnitUtils.ConvertToInternalUnits(target_thickness_mm, DisplayUnitType.DUT_MILLIMETERS)
    except Exception:
        # Manual fallback (least robust) if both API methods fail
        target_thickness_feet = target_thickness_mm / (1000.0 * 0.3048) # mm to m, m to ft

if target_thickness_feet is None:
    # If conversion still failed, raise an error or print message.
    # For this context, we might just exit or log, but since printing is discouraged,
    # we'll rely on the later checks to handle the lack of a valid thickness.
    print("# Error: Could not convert target thickness to internal units.")
    # Set a value that won't match to prevent unintended overrides
    target_thickness_feet = -99999.9

# Define a small tolerance for floating point comparison
tolerance = 1e-6

# Define the desired color (Red)
red_color = Color(255, 0, 0)

# Find the "Solid fill" pattern ElementId (Drafting pattern required for overrides)
solid_fill_pattern_id = ElementId.InvalidElementId
fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
for pattern_elem in fill_pattern_collector:
    fill_pattern = pattern_elem.GetFillPattern()
    # Check for solid fill and ensure it's a drafting pattern
    if fill_pattern.IsSolidFill and fill_pattern.Target == FillPatternTarget.Drafting:
        solid_fill_pattern_id = pattern_elem.Id
        break # Found the first solid drafting pattern

if solid_fill_pattern_id == ElementId.InvalidElementId:
    # Error message as comment if pattern not found, per format rules
    # print("# Error: Could not find a 'Solid fill' drafting pattern in the project.")
    pass # Script will simply not modify anything if pattern is not found
else:
    # Get the active view
    active_view = doc.ActiveView
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
        # print("# Error: No active graphical view found or the active view is a template.")
        pass # Script will not modify anything if view is invalid
    else:
        # Collect floor instances in the active view
        collector = FilteredElementCollector(doc, active_view.Id)
        floor_collector = collector.OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

        floors_modified_count = 0 # Optional counter
        
        for floor in floor_collector:
            # Ensure it's actually a Floor element (though collector should handle this)
            if isinstance(floor, Floor):
                try:
                    # Get the FloorType associated with the Floor instance
                    floor_type_id = floor.GetTypeId()
                    if floor_type_id != ElementId.InvalidElementId:
                        floor_type = doc.GetElement(floor_type_id)
                        if isinstance(floor_type, FloorType):
                            # Get the 'Default Thickness' parameter from the FloorType
                            # BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM corresponds to "Default Thickness"
                            thickness_param = floor_type.get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM)

                            if thickness_param and thickness_param.HasValue:
                                floor_thickness_feet = thickness_param.AsDouble()

                                # Check if the floor thickness matches the target thickness within tolerance
                                if abs(floor_thickness_feet - target_thickness_feet) < tolerance:
                                    # Thickness matches, apply overrides
                                    override_settings = OverrideGraphicSettings() # Create new settings object
                                    
                                    # Check existing overrides to potentially merge, but simplest is to create new
                                    # existing_override = active_view.GetElementOverrides(floor.Id)
                                    # override_settings = existing_override # Start with existing settings if needed

                                    # Set Surface Foreground Pattern to Solid Fill
                                    override_settings.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
                                    # Set Surface Foreground Pattern Color to Red
                                    override_settings.SetSurfaceForegroundPatternColor(red_color)
                                    # Ensure pattern is visible
                                    override_settings.SetSurfaceForegroundPatternVisible(True)

                                    # Apply the modified overrides to the floor in the view
                                    # Transaction is handled externally
                                    active_view.SetElementOverrides(floor.Id, override_settings)
                                    floors_modified_count += 1
                                # else: Thickness does not match - do nothing

                            # else: Could not get thickness parameter value from type - do nothing
                        # else: Element retrieved by TypeId was not a FloorType - do nothing
                    # else: Floor has no valid TypeId - do nothing

                except Exception as e:
                    # Silently skip elements that cause errors to avoid halting the whole script
                    # print("# Error processing Floor ID {}: {}".format(floor.Id.ToString(), e)) # Optional debug
                    pass

        # Optional: Print summary using print function (often captured by pyRevit/Dynamo)
        # print("Floors modified: {}".format(floors_modified_count))