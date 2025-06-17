# Purpose: This script overrides the cut line weight of structural framing elements in the active Revit view based on their type comments.

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
    FamilyInstance, # Structural Framing are often Family Instances
    Element,
    ElementType
)

# --- Script Core Logic ---

# Define the target parameter value and the new line weight
target_type_comment = "Primary Beam"
new_cut_line_weight = 6

# Get the active view
try:
    active_view = doc.ActiveView
    if not active_view:
        print("# Error: No active view found.")
        active_view = None # Ensure it's None if not found
except AttributeError:
    print("# Error: Could not get active view.")
    active_view = None

if active_view:
    # Create OverrideGraphicSettings object
    override_settings = OverrideGraphicSettings()

    # Set the cut line weight
    # Line weights must be between 1 and 16.
    if 1 <= new_cut_line_weight <= 16:
        try:
            override_settings.SetCutLineWeight(new_cut_line_weight)
        except Exception as e:
            print("# Error setting cut line weight in OverrideGraphicSettings: {}".format(e)) # Using format for older IronPython
            override_settings = None # Invalidate settings if failed
    else:
        print("# Error: Line weight {} is invalid. Must be between 1 and 16.".format(new_cut_line_weight))
        override_settings = None

    if override_settings:
        # Collect all Structural Framing elements visible in the active view
        collector = FilteredElementCollector(doc, active_view.Id)
        framing_collector = collector.OfCategory(BuiltInCategory.OST_StructuralFraming).WhereElementIsNotElementType()

        elements_overridden_count = 0
        elements_checked_count = 0
        elements_skipped_count = 0
        elements_error_count = 0

        # Iterate through the collected elements
        for element in framing_collector:
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

                # Get the 'Type Comments' parameter from the type
                type_comments_param = element_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)

                # Check if the parameter exists and its value matches the target
                if type_comments_param and type_comments_param.HasValue:
                    param_value = type_comments_param.AsString()
                    if param_value == target_type_comment:
                        # Apply the override
                        try:
                            active_view.SetElementOverrides(element.Id, override_settings)
                            elements_overridden_count += 1
                        except Exception as override_err:
                            # print("# Debug: Failed to override element {}: {}".format(element.Id, override_err)) # Debug line
                            elements_error_count += 1
                    else:
                        # Type comment does not match
                        elements_skipped_count += 1
                else:
                    # Parameter doesn't exist or has no value
                    elements_skipped_count += 1

            except Exception as e:
                # print("# Debug: Error processing element {}: {}".format(element.Id, e)) # Debug line
                elements_error_count += 1

        # Optional: Print a summary message (will appear in RevitPythonShell output)
        # print("# Summary: Checked: {}, Overridden: {}, Skipped: {}, Errors: {}".format(elements_checked_count, elements_overridden_count, elements_skipped_count, elements_error_count)) # Use format for older IronPython
    else:
        # print("# Script did not run because OverrideGraphicSettings could not be configured.") # Use format for older IronPython
        pass # Error already printed above

else:
    # print("# Script did not run because there is no active view.") # Use format for older IronPython
    pass