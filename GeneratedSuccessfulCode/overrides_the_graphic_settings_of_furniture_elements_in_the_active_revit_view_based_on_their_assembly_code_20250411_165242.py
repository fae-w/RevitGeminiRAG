# Purpose: This script overrides the graphic settings of furniture elements in the active Revit view based on their assembly code.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    ElementId,
    BuiltInParameter,
    FamilyInstance, # Furniture are often Family Instances
    Element,
    ElementType # To access type parameters like Assembly Code
)

# --- Configuration ---
target_assembly_code_prefix = "F10"
new_projection_line_weight = 1

# --- Get Active View ---
try:
    active_view = doc.ActiveView
    if not active_view:
        # print("# Error: No active view found.") # Debug removed
        active_view = None # Ensure it's None if not found
    elif not isinstance(active_view, View) or active_view.IsTemplate or not active_view.AreGraphicsOverridesAllowed():
        # print("# Error: Active view is not suitable for overrides (e.g., template, non-graphical).") # Debug removed
        active_view = None
except AttributeError:
    # print("# Error: Could not get active view.") # Debug removed
    active_view = None

if active_view:
    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set the projection line weight
    # Line weights must be between 1 and 16.
    if 1 <= new_projection_line_weight <= 16:
        try:
            override_settings.SetProjectionLineWeight(new_projection_line_weight)
        except Exception as e:
            # print("# Error setting projection line weight in OverrideGraphicSettings: {}".format(e)) # Debug removed
            override_settings = None # Invalidate settings if failed
    else:
        # print("# Error: Line weight {} is invalid. Must be between 1 and 16.".format(new_projection_line_weight)) # Debug removed
        override_settings = None

    if override_settings:
        # --- Collect Furniture Elements in the active view ---
        collector = FilteredElementCollector(doc, active_view.Id)
        furniture_collector = collector.OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsNotElementType()

        elements_overridden_count = 0
        elements_checked_count = 0
        elements_skipped_count = 0
        elements_error_count = 0

        # --- Apply Overrides ---
        for element in furniture_collector:
            elements_checked_count += 1
            try:
                # Get the element's type
                element_type_id = element.GetTypeId()
                if element_type_id == ElementId.InvalidElementId:
                    elements_skipped_count += 1
                    continue

                element_type = doc.GetElement(element_type_id)
                if not isinstance(element_type, ElementType):
                    elements_skipped_count += 1
                    continue

                # Get the 'Assembly Code' parameter from the type
                assembly_code_param = element_type.get_Parameter(BuiltInParameter.UNIFORMAT_CODE)

                # Check if the parameter exists, has a value, and starts with the target prefix
                if assembly_code_param and assembly_code_param.HasValue:
                    param_value = assembly_code_param.AsString()
                    if param_value and param_value.startswith(target_assembly_code_prefix):
                        # Apply the override
                        try:
                            active_view.SetElementOverrides(element.Id, override_settings)
                            elements_overridden_count += 1
                        except Exception as override_err:
                            # print("# Debug: Failed to override element {}: {}".format(element.Id, override_err)) # Debug removed
                            elements_error_count += 1
                    else:
                        # Assembly code does not match or is empty
                        elements_skipped_count += 1
                else:
                    # Parameter doesn't exist or has no value
                    elements_skipped_count += 1

            except Exception as e:
                # print("# Debug: Error processing element {}: {}".format(element.Id, e)) # Debug removed
                elements_error_count += 1

        # Optional: Print a summary message (will appear in RevitPythonShell output if uncommented)
        # print("# Summary: Checked: {}, Overridden: {}, Skipped: {}, Errors: {}".format(elements_checked_count, elements_overridden_count, elements_skipped_count, elements_error_count))
    # else:
        # print("# Script did not run because OverrideGraphicSettings could not be configured.") # Debug removed
        # pass # Error already printed above

# else:
    # print("# Script did not run because there is no suitable active view.") # Debug removed
    # pass