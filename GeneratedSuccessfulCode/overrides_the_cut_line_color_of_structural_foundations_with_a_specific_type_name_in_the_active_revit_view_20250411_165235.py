# Purpose: This script overrides the cut line color of Structural Foundations with a specific type name in the active Revit view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    Color,
    View,
    ElementId,
    ElementType
    # Removed StructuralFoundation import as it caused the error and is not needed for this logic
)

# --- Configuration ---
# Target substring in Structural Foundation Type Name
type_name_substring = "Pile Cap"
# Override color (Blue)
override_color = Color(0, 0, 255)

# --- Get Active View ---
# Assume 'doc' is pre-defined representing the current Revit Document
active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View):
    print("# Error: No active view found or the active 'view' is not a valid View element.")
    # Cannot proceed without a valid view
else:
    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()
    try:
        override_settings.SetCutLineColor(override_color)
    except Exception as e:
        print("# Error setting cut line color in OverrideGraphicSettings: {}".format(e))
        override_settings = None # Invalidate settings if failed

    if override_settings:
        # --- Collect and Filter Structural Foundations ---
        # Collect all Structural Foundation instances visible in the active view
        collector = FilteredElementCollector(doc, active_view.Id) # Filter by active view
        foundation_collector = collector.OfCategory(BuiltInCategory.OST_StructuralFoundation)\
                                        .WhereElementIsNotElementType()

        elements_overridden_count = 0
        elements_checked_count = 0
        elements_skipped_no_match = 0
        elements_skipped_invalid_type = 0
        elements_error_processing = 0
        elements_error_override = 0

        # --- Apply Overrides ---
        # Note: Assumes script runs within an existing transaction managed externally.
        for foundation in foundation_collector:
            elements_checked_count += 1
            try:
                foundation_type_id = foundation.GetTypeId()
                if foundation_type_id == ElementId.InvalidElementId:
                    elements_skipped_invalid_type += 1
                    continue # Skip elements with invalid type IDs

                foundation_type_elem = doc.GetElement(foundation_type_id)
                # Ensure the retrieved element is indeed an ElementType
                if isinstance(foundation_type_elem, ElementType):
                    # Use the Name property of the ElementType, which usually corresponds to 'Type Name'
                    type_name = foundation_type_elem.Name
                    # Case-insensitive check for the substring
                    if type_name_substring.lower() in type_name.lower():
                        # Apply the override to this specific foundation element in the active view
                        try:
                            active_view.SetElementOverrides(foundation.Id, override_settings)
                            elements_overridden_count += 1
                        except Exception as override_err:
                            # print("# Debug: Failed to override element {}: {}".format(foundation.Id, override_err)) # Debug line
                            elements_error_override += 1
                    else:
                        # Type name does not match
                        elements_skipped_no_match += 1
                else:
                     # Retrieved element is not an ElementType (shouldn't happen often for valid foundations)
                    elements_skipped_invalid_type += 1

            except Exception as e:
                # print("# Debug: Error processing element {}: {}".format(foundation.Id, e)) # Debug line
                elements_error_processing += 1

        # Provide feedback to the user
        if elements_overridden_count > 0:
            print("# Applied blue cut line color override to {} Structural Foundation(s) with 'Type Name' containing '{}' in the active view.".format(elements_overridden_count, type_name_substring))
        elif elements_checked_count > 0:
            print("# No Structural Foundation elements found/matched with 'Type Name' containing '{}' in the active view to apply overrides.".format(type_name_substring))
        else:
             print("# No Structural Foundation elements were found in the active view.")

        # Optional detailed summary (uncomment if needed)
        # total_skipped = elements_skipped_no_match + elements_skipped_invalid_type
        # total_errors = elements_error_processing + elements_error_override
        # print("# Summary: Checked: {}, Overridden: {}, Skipped (No Match): {}, Skipped (Invalid Type): {}, Errors (Processing): {}, Errors (Override): {}".format(
        #     elements_checked_count, elements_overridden_count, elements_skipped_no_match,
        #     elements_skipped_invalid_type, elements_error_processing, elements_error_override))

    else:
        print("# Script did not run because OverrideGraphicSettings could not be configured.")