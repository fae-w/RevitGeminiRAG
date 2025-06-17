# Purpose: This script overrides the color of dimension lines based on the phase of the referenced elements in the active Revit view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Dimension,
    Element,
    Phase,
    BuiltInParameter,
    Color,
    Parameter,
    ElementId,
    View,
    OverrideGraphicSettings,
    Reference,
    ElementType # Added for completeness, though not strictly used here
)
from System.Collections.Generic import List # Might be needed if creating lists of ElementIds

# --- Configuration ---
# Target Phase Name
target_phase_name = "New Construction"
# Override color (Blue)
override_color = Color(0, 0, 255)
# Assumption: Overriding dimension *lines* color, as text color override per instance isn't directly available via standard API.
# If text color modification is strictly required, it usually involves changing the DimensionType, affecting all instances.

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view found or the active 'view' is not a valid View element.")
    # Cannot proceed without a valid view
else:
    # --- Find Target Phase ---
    phase_collector = FilteredElementCollector(doc).OfClass(Phase)
    target_phase = None
    for phase in phase_collector:
        if phase.Name == target_phase_name:
            target_phase = phase
            break

    if not target_phase:
        print("# Error: Phase '{}' not found in the document.".format(target_phase_name))
    else:
        target_phase_id = target_phase.Id

        # --- Create Override Settings for Dimension Lines ---
        override_settings = OverrideGraphicSettings()
        try:
            # Overriding projection lines, which represent the dimension lines themselves
            override_settings.SetProjectionLineColor(override_color)
        except Exception as e:
            print("# Error setting projection line color in OverrideGraphicSettings: {}".format(e))
            override_settings = None # Invalidate settings if failed

        if override_settings:
            # --- Collect Dimensions in the Active View ---
            dimension_collector = FilteredElementCollector(doc, active_view.Id)\
                                    .OfClass(Dimension)\
                                    .WhereElementIsNotElementType()

            dimensions_overridden_count = 0
            dimensions_checked_count = 0
            dimensions_skipped_no_refs = 0
            dimensions_skipped_no_match = 0
            dimensions_error_processing = 0

            # --- Process Dimensions ---
            for dim in dimension_collector:
                dimensions_checked_count += 1
                apply_override = False
                try:
                    if dim.References and dim.References.Size > 0:
                        for ref in dim.References:
                            # Ensure reference is to an element, not just geometry
                            if ref.ElementId != ElementId.InvalidElementId:
                                referenced_elem = doc.GetElement(ref.ElementId)
                                if referenced_elem:
                                    # Check the Phase Created parameter
                                    phase_created_param = referenced_elem.get_Parameter(BuiltInParameter.PHASE_CREATED)
                                    if phase_created_param and phase_created_param.HasValue:
                                        ref_phase_id = phase_created_param.AsElementId()
                                        if ref_phase_id == target_phase_id:
                                            apply_override = True
                                            break # Found a matching reference, no need to check others for this dimension
                    else:
                        dimensions_skipped_no_refs += 1

                    if apply_override:
                        try:
                            active_view.SetElementOverrides(dim.Id, override_settings)
                            dimensions_overridden_count += 1
                        except Exception as override_err:
                            # print("# Debug: Failed to override dimension {}: {}".format(dim.Id, override_err))
                            dimensions_error_processing += 1 # Count as processing error
                    elif not apply_override and dim.References.Size > 0:
                         dimensions_skipped_no_match += 1

                except Exception as e:
                    # print("# Debug: Error processing dimension {}: {}".format(dim.Id, e))
                    dimensions_error_processing += 1

            # Provide feedback
            if dimensions_overridden_count > 0:
                print("# Applied blue line color override to {} Dimension(s) referencing elements on phase '{}'.".format(dimensions_overridden_count, target_phase_name))
            elif dimensions_checked_count > 0:
                print("# No Dimensions found referencing elements on phase '{}' in the active view.".format(target_phase_name))
            else:
                print("# No Dimensions found in the active view.")

            # Optional detailed summary (uncomment if needed)
            # print("# Summary: Checked: {}, Overridden: {}, Skipped (No Refs): {}, Skipped (No Match): {}, Errors: {}".format(
            #     dimensions_checked_count, dimensions_overridden_count, dimensions_skipped_no_refs,
            #     dimensions_skipped_no_match, dimensions_error_processing))
        else:
            print("# Script did not run because OverrideGraphicSettings could not be configured.")