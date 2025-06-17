# Purpose: This script halftones structural columns with concrete materials in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    Element,
    ElementId,
    BuiltInParameter,
    Material
)

# --- Configuration ---
concrete_keyword = "concrete" # Case-insensitive check below

# --- Get Active View ---
active_view = doc.ActiveView
if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or active view is invalid.")
elif not active_view.AreGraphicsOverridesAllowed():
    print("# Error: The active view '{{}}' (Type: {{}}) does not support graphic overrides.".format(active_view.Name, active_view.ViewType))
else:
    # --- Prepare Override Settings ---
    override_settings = OverrideGraphicSettings()
    override_settings.SetHalftone(True)

    # --- Collect Structural Columns in the Active View ---
    collector = FilteredElementCollector(doc, active_view.Id)\
                .OfCategory(BuiltInCategory.OST_StructuralColumns)\
                .WhereElementIsNotElementType()

    columns_to_override = []
    processed_count = 0
    overridden_count = 0

    # --- Iterate and Filter Columns ---
    for column in collector:
        processed_count += 1
        try:
            # Get the structural material parameter (often ElementId)
            material_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)

            if material_param is not None and material_param.HasValue:
                material_id = material_param.AsElementId()

                if material_id != ElementId.InvalidElementId:
                    material_element = doc.GetElement(material_id)

                    if isinstance(material_element, Material):
                        material_name = Element.Name.GetValue(material_element)
                        # Check if material name contains the keyword (case-insensitive)
                        if concrete_keyword.lower() in material_name.lower():
                            columns_to_override.append(column.Id)
                            # Apply override immediately (Transaction managed externally)
                            active_view.SetElementOverrides(column.Id, override_settings)
                            overridden_count += 1
                            # print("# Applying override to Column ID: {}".format(column.Id)) # Debug
        except Exception as e:
            # print("# Warning: Could not process Column ID: {{}}. Error: {{}}".format(column.Id, e)) # Debug
            pass # Ignore columns that cause errors

    # Optional: Print summary
    # print("--- Summary ---")
    # print("Processed Structural Columns in view '{}': {}".format(active_view.Name, processed_count))
    # print("Columns halftoned (Material contains '{}'): {}".format(concrete_keyword, overridden_count))

    if overridden_count == 0 and processed_count > 0:
        print("# No structural columns found in the active view with a material containing '{{}}'.".format(concrete_keyword))
    elif processed_count == 0:
        print("# No structural columns found in the active view.")