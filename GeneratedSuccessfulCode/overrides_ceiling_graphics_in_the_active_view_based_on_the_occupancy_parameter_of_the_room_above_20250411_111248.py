# Purpose: This script overrides ceiling graphics in the active view based on the occupancy parameter of the room above.

# Purpose: This script overrides the graphics of ceilings in the active view based on the occupancy of the room above them.

﻿# Import necessary .NET assemblies
import clr
clr.AddReference('System') # For Byte

# Import specific classes/namespaces
from System import Byte
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Ceiling, ElementId,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    BuiltInParameter, XYZ, View, Phase, Element, Parameter, StorageType
)
# Import Room class from Architecture namespace
import Autodesk.Revit.DB.Architecture as Arch


# --- Helper function to find the Solid Fill pattern ---
def find_solid_fill_pattern(doc_param):
    """Finds the first solid fill pattern element suitable for surface patterns."""
    collector = FilteredElementCollector(doc_param).OfClass(FillPatternElement)
    for pattern_element in collector:
        if pattern_element is not None:
            pattern = pattern_element.GetFillPattern()
            # Check if pattern is not null and is solid fill
            if pattern is not None and pattern.IsSolidFill:
                # Check if the pattern is suitable for overrides (Drafting or Model)
                # Solid fill usually works in overrides regardless of target.
                return pattern_element.Id
    # If no solid fill found, return invalid ID
    return ElementId.InvalidElementId

# --- Configuration ---
TARGET_OCCUPANCY_VALUE = "Assembly" # Case-sensitive match for the Room's Occupancy parameter
OVERRIDE_COLOR = Color(255, 0, 0) # Red color for the override

# --- Main Script ---
# Assume 'doc' and 'uidoc' are pre-defined and valid
active_view = doc.ActiveView
if not isinstance(active_view, View):
    print("# Error: Active view is not valid or not found.")
else:
    # Find the solid fill pattern ID
    solid_fill_pattern_id = find_solid_fill_pattern(doc)
    if solid_fill_pattern_id == ElementId.InvalidElementId:
        print("# Error: Could not find a Solid Fill pattern in the document. Cannot apply overrides.")
    else:
        # Get the phase of the active view for room lookup
        view_phase_param = active_view.get_Parameter(BuiltInParameter.VIEW_PHASE)
        current_phase = None
        if view_phase_param and view_phase_param.AsElementId() != ElementId.InvalidElementId:
             phase_element = doc.GetElement(view_phase_param.AsElementId())
             if isinstance(phase_element, Phase):
                  current_phase = phase_element

        if current_phase is None:
             print("# Warning: Could not determine the active view's phase. Room lookup might be affected or use default project phase.")
             # GetRoomAtPoint might default to the last phase if None is passed,
             # or the overload without phase parameter might be used implicitly.

        # Collect Ceilings visible in the active view
        ceiling_collector = FilteredElementCollector(doc, active_view.Id)\
                            .OfCategory(BuiltInCategory.OST_Ceilings)\
                            .WhereElementIsNotElementType()

        ceilings_to_override_ids = []
        processed_count = 0
        skipped_no_room = 0
        skipped_wrong_occupancy = 0
        error_count = 0

        for ceiling in ceiling_collector:
            # Ensure it's actually a Ceiling element
            if not isinstance(ceiling, Ceiling):
                continue

            processed_count += 1
            room_above = None
            try:
                # Get the ceiling's bounding box in model coordinates for location test
                bbox = ceiling.get_BoundingBox(None) # Using None gives model coordinates
                if bbox is not None and bbox.Min is not None and bbox.Max is not None:
                    # Calculate a test point slightly above the ceiling's top surface center
                    center_xy = (bbox.Min + bbox.Max) / 2.0
                    # Ensure Z coordinates are valid before proceeding
                    if bbox.Max.Z is not None:
                        test_z = bbox.Max.Z + 0.1 # Point slightly above the ceiling (0.1 feet)
                        test_point = XYZ(center_xy.X, center_xy.Y, test_z)

                        # Find the room at the test point using the view's phase if available
                        if current_phase:
                            room_above = doc.GetRoomAtPoint(test_point, current_phase)
                        else:
                            # Try the overload without phase if phase determination failed
                            room_above = doc.GetRoomAtPoint(test_point)

                        if room_above is not None and isinstance(room_above, Arch.Room):
                            # Found a room, now check its "Occupancy" parameter
                            occupancy_param = room_above.get_Parameter(BuiltInParameter.ROOM_OCCUPANCY)

                            # Fallback: Try lookup by name if BuiltInParameter is invalid or not set
                            if occupancy_param is None or not occupancy_param.HasValue:
                                occupancy_param = room_above.LookupParameter("Occupancy")

                            if occupancy_param and occupancy_param.HasValue:
                                occupancy_value = ""
                                # Extract value based on storage type
                                if occupancy_param.StorageType == StorageType.String:
                                    occupancy_value = occupancy_param.AsString()
                                elif occupancy_param.StorageType == StorageType.ElementId:
                                    # Handle cases where Occupancy might be set by a Key Schedule
                                    key_id = occupancy_param.AsElementId()
                                    if key_id != ElementId.InvalidElementId:
                                        key_elem = doc.GetElement(key_id)
                                        if key_elem and hasattr(key_elem, 'Name'):
                                            occupancy_value = key_elem.Name # Assume key name is the value
                                        else:
                                             occupancy_value = "[Invalid Key ID]"
                                elif occupancy_param.StorageType in [StorageType.Integer, StorageType.Double]:
                                     occupancy_value = occupancy_param.AsValueString() # Get display value if numerical
                                else:
                                     occupancy_value = "[Unsupported Storage Type]"


                                # Compare the found value with the target value (case-sensitive)
                                if occupancy_value == TARGET_OCCUPANCY_VALUE:
                                    ceilings_to_override_ids.append(ceiling.Id)
                                    # print("# Debug: Found matching ceiling {0} below room {1}".format(ceiling.Id, room_above.Id))
                                else:
                                    skipped_wrong_occupancy += 1
                            else:
                                # Room found, but no usable "Occupancy" parameter found
                                skipped_wrong_occupancy += 1
                                # print("# Debug: Room {0} found above ceiling {1}, but no 'Occupancy' parameter.".format(room_above.Id, ceiling.Id))
                        else:
                            # No room found directly above the test point for this ceiling
                            skipped_no_room += 1
                            # print("# Debug: No room found above ceiling {0}.".format(ceiling.Id))
                    else:
                        # Invalid Z coordinate in bounding box
                        skipped_no_room += 1

                else:
                     # Could not get bounding box for the ceiling
                     print("# Warning: Could not get bounding box for ceiling {0}. Skipping.".format(ceiling.Id))
                     skipped_no_room += 1

            except Exception as e:
                print("# Error processing ceiling {0}: {1}".format(ceiling.Id, str(e)))
                error_count += 1

        # Apply overrides if any ceilings were identified
        if ceilings_to_override_ids:
            # Create the override settings
            ogs = OverrideGraphicSettings()
            ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
            ogs.SetSurfaceForegroundPatternColor(OVERRIDE_COLOR)
            ogs.SetSurfaceForegroundPatternVisible(True)
            # Optional: Reset other potentially interfering overrides if needed
            # ogs.SetSurfaceTransparency(0) # Ensure not transparent
            # ogs.SetHalftone(False) # Ensure not halftone

            applied_count = 0
            # Apply the overrides to the identified elements in the active view
            # IMPORTANT: Assumes an external Transaction is active
            for ceiling_id in ceilings_to_override_ids:
                try:
                    active_view.SetElementOverrides(ceiling_id, ogs)
                    applied_count += 1
                except Exception as e:
                    print("# Error applying override to ceiling {0}: {1}".format(ceiling_id, str(e)))
                    error_count += 1

            print("# Successfully applied overrides to {0} ceilings.".format(applied_count))
            if applied_count != len(ceilings_to_override_ids):
                 print("# Note: {0} ceilings were identified but overrides could not be applied to all.".format(len(ceilings_to_override_ids) - applied_count))

        else:
            print("# No ceilings found in the current view that are located below rooms with 'Occupancy' set to '{0}'.".format(TARGET_OCCUPANCY_VALUE))

        # Optional detailed summary (uncomment for debugging)
        # print("# --- Summary ---")
        # print("# Ceilings processed: {0}".format(processed_count))
        # print("# Ceilings where no room was found above: {0}".format(skipped_no_room))
        # print("# Ceilings where room occupancy did not match or parameter missing: {0}".format(skipped_wrong_occupancy))
        # print("# Ceilings identified for override: {0}".format(len(ceilings_to_override_ids)))
        # print("# Errors encountered during processing: {0}".format(error_count))

# Final message indicating completion (optional)
# print("# Script finished.")