# Purpose: This script overrides the projection line color of casework elements in the active Revit view if their material name contains a specified substring.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory,
    OverrideGraphicSettings, Color, View,
    ElementId, Material, Parameter, StorageType,
    BuiltInParameter, Element
)

# --- Configuration ---
target_material_substring = "Wood" # Case-insensitive check will be performed
override_color = Color(165, 42, 42) # Brown

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined and available
active_view = doc.ActiveView

# Proceed only if active_view is valid and allows overrides
if active_view and isinstance(active_view, View) and not active_view.IsTemplate and active_view.AreGraphicsOverridesAllowed():

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()
    override_settings.SetProjectionLineColor(override_color)

    # --- Collect Casework instances in the active view ---
    casework_collector = FilteredElementCollector(doc, active_view.Id)\
                         .OfCategory(BuiltInCategory.OST_Casework)\
                         .WhereElementIsNotElementType()

    casework_overridden_count = 0
    # --- Apply Overrides ---
    # Note: The script runs inside an existing transaction provided by the external runner.
    for casework in casework_collector:
        material_found_and_matches = False
        try:
            material_id = ElementId.InvalidElementId

            # Attempt 1: Look for a parameter explicitly named "Material"
            material_param = casework.LookupParameter("Material")
            if material_param and material_param.HasValue and material_param.StorageType == StorageType.ElementId:
                material_id = material_param.AsElementId()

            # Attempt 2: If not found or not an ElementId, try the built-in parameter often used for materials
            if material_id == ElementId.InvalidElementId:
                 # Check common built-in parameters for material
                 param_bip_material = casework.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)
                 if param_bip_material and param_bip_material.HasValue and param_bip_material.StorageType == StorageType.ElementId:
                     material_id = param_bip_material.AsElementId()

                 # Optional: Check another common material parameter if the first fails
                 # elif casework.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM) and casework.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).HasValue and casework.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).StorageType == StorageType.ElementId:
                 #     material_id = casework.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM).AsElementId()

            # If a valid Material ID was found by either method, check its name
            if material_id != ElementId.InvalidElementId:
                material_element = doc.GetElement(material_id)
                if material_element and isinstance(material_element, Material):
                    material_name = Element.Name.__get__(material_element) # Use property getter
                    if material_name and target_material_substring.lower() in material_name.lower():
                         material_found_and_matches = True

            # Apply override if material matches
            if material_found_and_matches:
                active_view.SetElementOverrides(casework.Id, override_settings)
                casework_overridden_count += 1

        except Exception as e:
            # Silently ignore casework elements that might cause errors
            # print("Error processing casework {}: {}".format(casework.Id, e)) # Optional Debug
            pass

    # Optional: Print success message (commented out as per requirements)
    # print("# Applied brown projection line override to {} casework elements with '{}' in their material name in view '{}'.".format(casework_overridden_count, target_material_substring, active_view.Name))
# else:
    # Optional: Handle case where the view is not suitable (commented out)
    # print("# Error: Requires an active, non-template graphical view where overrides are allowed.")