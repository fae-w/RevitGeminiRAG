# Purpose: This script sets the transparency of specific pipe fittings in the active Revit view based on their system type.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List

# Import base DB classes needed
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    OverrideGraphicSettings,
    View,
    StorageType,
    BuiltInParameter,
    Element # Keep Element import for potential future use or checks if needed
)
# Import the Plumbing namespace to resolve the import error
import Autodesk.Revit.DB.Plumbing as Plumbing

# --- Configuration ---
target_system_type_name = "Vent"
transparency_level = 50 # Percentage (0-100)
target_category = BuiltInCategory.OST_PipeFitting
# Parameter that usually holds the ElementId of the PipingSystemType
system_type_param_bip = BuiltInParameter.RBS_PIPING_SYSTEM_TYPE_PARAM

# --- Helper function to find a PipingSystemType by name ---
def find_piping_system_type_by_name(doc, name):
    """Finds the first PipingSystemType element by name (case-insensitive)."""
    # Use the imported Plumbing namespace and PipingSystemType class
    collector = FilteredElementCollector(doc).OfClass(Plumbing.PipingSystemType)
    name_lower = name.lower()
    for pst in collector:
        try:
            # Access the Name property directly
            element_name = pst.Name
            if element_name is not None and isinstance(element_name, str) and element_name.lower() == name_lower:
                return pst.Id
        except Exception:
            pass # Ignore elements where name cannot be retrieved
    return ElementId.InvalidElementId

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined and available
active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View):
    print("# Error: No active valid view found or accessible.")
elif not active_view.AreGraphicsOverridesAllowed():
     # Access the Name property directly
     print("# Error: Graphics Overrides are not allowed in the active view '{}'.".format(active_view.Name))
else:
    # --- Find the Target System Type Element ID ---
    target_system_type_id = find_piping_system_type_by_name(doc, target_system_type_name)

    if target_system_type_id == ElementId.InvalidElementId:
        print("# Error: PipingSystemType named '{}' not found in the document.".format(target_system_type_name))
    else:
        # --- Collect Pipe Fittings in Active View ---
        collector = FilteredElementCollector(doc, active_view.Id)\
                    .OfCategory(target_category)\
                    .WhereElementIsNotElementType()

        fittings_to_modify = List[ElementId]()
        processed_count = 0
        matched_count = 0

        for fitting in collector:
            processed_count += 1
            param_found = False
            system_type_id_on_fitting = ElementId.InvalidElementId

            # Get the system type parameter from the fitting
            try:
                param = fitting.get_Parameter(system_type_param_bip)
                if param and param.HasValue and param.StorageType == StorageType.ElementId:
                    system_type_id_on_fitting = param.AsElementId()
                    param_found = True
            except Exception as e_param:
                pass # Continue

            # Check if the fitting's system type matches the target
            if param_found and system_type_id_on_fitting == target_system_type_id:
                fittings_to_modify.Add(fitting.Id)
                matched_count += 1

        # --- Define Override Settings ---
        ogs = OverrideGraphicSettings()
        try:
            # Set transparency (0=opaque, 100=fully transparent)
            ogs.SetSurfaceTransparency(transparency_level)
        except Exception as e_ogs:
             print("# Error setting transparency in OverrideGraphicSettings: {}. Value was: {}".format(e_ogs, transparency_level))
             ogs = None # Invalidate ogs if setting failed

        # --- Apply Overrides ---
        if ogs and fittings_to_modify.Count > 0:
            applied_count = 0
            error_count = 0
            # Transaction is handled externally by the caller
            for fitting_id in fittings_to_modify:
                try:
                    active_view.SetElementOverrides(fitting_id, ogs)
                    applied_count += 1
                except Exception as e_apply:
                    # print("# Warning: Could not apply overrides to element {}: {}".format(fitting_id, e_apply))
                    error_count += 1

            # Access the Name property directly
            print("# Processed {} pipe fittings in view '{}'.".format(processed_count, active_view.Name))
            print("# Found {} fittings with system type '{}'.".format(matched_count, target_system_type_name))
            if applied_count > 0:
                 print("# Successfully applied {}% transparency override to {} fittings.".format(transparency_level, applied_count))
            if error_count > 0:
                 print("# Failed to apply overrides to {} fittings.".format(error_count))

        elif ogs is None:
            print("# Cannot apply overrides because OverrideGraphicSettings could not be configured.")
        elif fittings_to_modify.Count == 0:
            # Access the Name property directly
            print("# Processed {} pipe fittings in view '{}'. No fittings found with system type '{}'.".format(processed_count, active_view.Name, target_system_type_name))
        else:
            print("# No overrides applied.")