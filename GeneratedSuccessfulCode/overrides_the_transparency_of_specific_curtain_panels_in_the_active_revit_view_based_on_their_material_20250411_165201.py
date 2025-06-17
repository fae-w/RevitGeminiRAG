# Purpose: This script overrides the transparency of specific curtain panels in the active Revit view based on their material.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Color
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Material,
    PanelType,
    ElementId,
    Element,
    Parameter,
    StorageType,
    BuiltInCategory,
    FamilyInstance,
    View,
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    FillPatternTarget,
    BuiltInParameter # To get TypeId
)
import System # For exception handling and Color

# --- Configuration ---
target_material_name = "Spandrel Glass" # Case-sensitive material name
# Assumption: The material of the PanelType is controlled by a type parameter named "Material".
# Adjust this if your panel types use a different parameter name.
type_material_param_name = "Material"
transparency_override = 75 # Transparency percentage (0=opaque, 100=fully transparent)
override_color = Color(0, 255, 0) # Green (R, G, B)

# --- Script Core Logic ---

active_view = doc.ActiveView
applied_count = 0
skipped_no_material_found = 0
skipped_no_types_found = 0
skipped_no_panels_in_view = 0
skipped_panel_wrong_type = 0
error_count = 0

# 1. Validate Active View
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
else:
    try:
        # 2. Find the target Material ElementId
        target_material_id = ElementId.InvalidElementId
        material_collector = FilteredElementCollector(doc).OfClass(Material)
        # Case-insensitive comparison might be safer, but sticking to exact match as requested
        for mat in material_collector:
            if mat.Name == target_material_name:
                target_material_id = mat.Id
                break

        if target_material_id == ElementId.InvalidElementId:
            print("# Error: Material named '{}' not found in the project.".format(target_material_name))
            skipped_no_material_found = 1 # Indicate the reason for stopping
        else:
            # 3. Find PanelType ElementIds that use the target material
            matching_panel_type_ids = set() # Use a set for faster lookups
            panel_type_collector = FilteredElementCollector(doc).OfClass(PanelType)
            for panel_type in panel_type_collector:
                if isinstance(panel_type, PanelType):
                    try:
                        # Look for the type parameter by name
                        material_param = panel_type.LookupParameter(type_material_param_name)
                        if material_param and material_param.StorageType == StorageType.ElementId:
                            mat_id = material_param.AsElementId()
                            if mat_id == target_material_id:
                                matching_panel_type_ids.add(panel_type.Id)
                        # Optional: Add checks for BuiltInParameters if LookupParameter is not reliable
                    except System.Exception as e:
                        # Silently ignore types that cause errors during parameter lookup
                        # print("# Debug: Error checking material for PanelType {}: {}".format(panel_type.Id, e))
                        pass

            if not matching_panel_type_ids:
                print("# Info: No Panel Types found using the '{}' material via the '{}' parameter.".format(target_material_name, type_material_param_name))
                skipped_no_types_found = 1 # Indicate the reason for stopping
            else:
                # 4. Find the Solid Fill Pattern ID
                solid_fill_pattern_id = ElementId.InvalidElementId
                fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
                for fp in fill_pattern_collector:
                    fill_pattern = fp.GetFillPattern()
                    # Check if it's a drafting or model pattern, and if it's solid fill
                    if fill_pattern.IsSolidFill:
                         # Check target (prefer drafting, but accept model if drafting not found first)
                         if fill_pattern.Target == FillPatternTarget.Drafting:
                             solid_fill_pattern_id = fp.Id
                             break # Found solid drafting pattern, prefer this
                         elif fill_pattern.Target == FillPatternTarget.Model and solid_fill_pattern_id == ElementId.InvalidElementId:
                             solid_fill_pattern_id = fp.Id # Found solid model pattern, use if no drafting solid found

                if solid_fill_pattern_id == ElementId.InvalidElementId:
                     print("# Warning: Could not find a Solid Fill pattern. Surface pattern override will be skipped.")
                     # Proceed without pattern override if Solid Fill isn't found


                # 5. Define Override Graphic Settings
                override_settings = OverrideGraphicSettings()
                try:
                    override_settings.SetSurfaceTransparency(transparency_override)
                except System.ArgumentException as trans_ex:
                    print("# Error setting transparency ({}): {}. Using default.".format(transparency_override, trans_ex.Message))
                    override_settings = OverrideGraphicSettings() # Reset

                # Apply green surface pattern if Solid Fill was found
                if solid_fill_pattern_id != ElementId.InvalidElementId:
                    override_settings.SetSurfaceForegroundPatternVisible(True)
                    override_settings.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
                    override_settings.SetSurfaceForegroundPatternColor(override_color)
                # else: # Already printed warning above
                #    print("# Skipping surface pattern override as Solid Fill pattern was not found.")

                # 6. Collect Curtain Panel Instances in the Active View
                panel_collector = FilteredElementCollector(doc, active_view.Id)\
                                    .OfCategory(BuiltInCategory.OST_CurtainWallPanels)\
                                    .WhereElementIsNotElementType()\
                                    .ToElements() # Get actual elements

                if not panel_collector:
                     print("# Info: No curtain panel instances found in the active view.")
                     skipped_no_panels_in_view = 1
                else:
                    # 7. Apply Overrides to matching panels
                    for panel in panel_collector:
                        if isinstance(panel, FamilyInstance):
                            try:
                                panel_type_id = panel.GetTypeId()
                                if panel_type_id in matching_panel_type_ids:
                                    # Apply the override (Transaction handled externally)
                                    active_view.SetElementOverrides(panel.Id, override_settings)
                                    applied_count += 1
                                else:
                                    skipped_panel_wrong_type += 1
                            except System.Exception as apply_ex:
                                print("# Error applying override to Panel ID {}: {}".format(panel.Id, apply_ex.Message))
                                error_count += 1
                        #else:
                            # Should not happen with this collector, but good practice
                            # print("# Debug: Skipping non-FamilyInstance element ID {}".format(panel.Id))
                            # pass

    except System.Exception as general_ex:
        print("# Error during script execution: {}".format(general_ex))
        error_count += 1

# Final summary printing is disabled per requirements.
# if applied_count > 0:
#     print("# Successfully applied overrides to {} curtain panels.".format(applied_count))
# if skipped_no_material_found:
#     print("# Skipped processing: Target material '{}' not found.".format(target_material_name))
# elif skipped_no_types_found:
#     print("# Skipped processing: No Panel Types found using the target material.")
# elif skipped_no_panels_in_view:
#      print("# No overrides applied: No curtain panels found in the active view.")
# elif applied_count == 0 and error_count == 0: # Only print if no errors and no applies happened AFTER finding types/material
#      print("# No applicable curtain panels found in the active view matching the specified type criteria.")

# if error_count > 0:
#     print("# Encountered {} errors during processing.".format(error_count))