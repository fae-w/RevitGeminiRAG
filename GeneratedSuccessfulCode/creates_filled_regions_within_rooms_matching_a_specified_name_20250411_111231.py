# Purpose: This script creates filled regions within rooms matching a specified name.

# Purpose: This script creates filled regions in rooms with a specific name (TARGET_ROOM_NAME) using a specified FilledRegionType, handling various boundary conditions and potential errors.

﻿# Import necessary .NET assemblies
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often useful, even if not directly used by uidoc here
clr.AddReference('System.Collections')

# Import specific classes/namespaces
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, FilledRegion, FilledRegionType,
    SpatialElementBoundaryOptions, BoundarySegment,
    CurveLoop, Curve, ElementId, ViewPlan, XYZ,
    BuiltInParameter
)
# Import Architecture namespace specifically for Room and RoomTag
import Autodesk.Revit.DB.Architecture as Arch
from Autodesk.Revit.DB.Architecture import Room, RoomTag

import Autodesk.Revit.Exceptions as RevitExceptions

# --- Configuration ---
TARGET_ROOM_NAME = "WC" # The exact name of the rooms to target
FILLED_REGION_TYPE_NAME = "Solid Blue" # The exact name of the FilledRegionType to use

# --- Helper function to find FilledRegionType ---
def find_filled_region_type(doc_param, type_name):
    """Finds the FilledRegionType by name."""
    collector = FilteredElementCollector(doc_param).OfClass(FilledRegionType)
    # Case-sensitive comparison, adjust if case-insensitivity is needed
    for fr_type in collector:
        if fr_type.Name == type_name:
            return fr_type.Id
    return ElementId.InvalidElementId

# --- Main Script ---
# Assume 'doc' and 'uidoc' are pre-defined and valid
if doc is None:
    print("# Error: Revit document object ('doc') not found.")
else:
    active_view = doc.ActiveView
    if not isinstance(active_view, ViewPlan):
        print("# Error: Active view is not a Plan View.")
    else:
        # Find the specified FilledRegionType ID
        filled_region_type_id = find_filled_region_type(doc, FILLED_REGION_TYPE_NAME)

        if filled_region_type_id == ElementId.InvalidElementId:
            print("# Error: FilledRegionType '{{}}' not found.".format(FILLED_REGION_TYPE_NAME))
        else:
            # Collect Room Tags visible in the active view
            room_tag_collector = FilteredElementCollector(doc, active_view.Id)\
                                 .OfCategory(BuiltInCategory.OST_RoomTags)\
                                 .WhereElementIsNotElementType()

            rooms_to_process = []
            processed_room_ids = set() # Keep track of processed rooms to avoid duplicates

            for tag in room_tag_collector:
                # Check if the tag actually has a room associated with it
                try:
                    # Using RoomTag.GetTaggedRoom() is often more reliable than .Room
                    room = tag.GetTaggedRoom() # Now RoomTag should be correctly imported
                    if room is not None and room.Id not in processed_room_ids:
                        # Check if the Room Name matches the target name
                        room_name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
                        if room_name_param and room_name_param.AsString() == TARGET_ROOM_NAME:
                            rooms_to_process.append(room) # Now Room should be correctly imported
                            processed_room_ids.add(room.Id)
                except Exception as e:
                    # Handle potential errors accessing tag/room properties
                     print("# Warning: Error checking room for tag {{}}: {{}}".format(tag.Id, e))

            if not rooms_to_process:
                print("# No rooms named '{{}}' found with tags in the current view.".format(TARGET_ROOM_NAME))
            else:
                # Boundary options
                boundary_options = SpatialElementBoundaryOptions()
                # Use default options (Finish boundary, usually appropriate for filled regions)
                # Optional: Set other properties if needed, e.g.,
                # from Autodesk.Revit.DB import SpatialElementBoundaryLocation
                # boundary_options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Center

                created_count = 0
                skipped_count = 0

                # IMPORTANT: This script assumes an active Transaction is managed externally (e.g., by a C# wrapper)
                # as per the requirements (no Transaction management here).

                for room in rooms_to_process:
                    room_id_str = room.Id.ToString() # For clearer logging
                    try:
                        # Get boundary segments (returns IList<IList<BoundarySegment>>)
                        boundary_segment_loops = room.GetBoundarySegments(boundary_options)

                        if not boundary_segment_loops or boundary_segment_loops.Count == 0:
                            print("# Warning: Room {{}} ('{{}}') has no boundary segments or failed to retrieve them.".format(room_id_str, TARGET_ROOM_NAME))
                            skipped_count += 1
                            continue

                        all_curve_loops = List[CurveLoop]()
                        has_valid_loops = False # Track if at least one valid CurveLoop is formed for this room

                        for i, segment_list in enumerate(boundary_segment_loops):
                            curves = List[Curve]()
                            valid_segment_loop = True
                            if segment_list is None or segment_list.Count == 0:
                                print("# Warning: Empty or null boundary segment list found for room {{}} (Loop Index {{}}).".format(room_id_str, i))
                                continue # Skip this empty list

                            for segment in segment_list:
                                curve = segment.GetCurve()
                                # Check for null curves or very short curves which might cause issues
                                if curve is None or curve.Length < 1e-6:
                                    print("# Warning: Found null or zero-length curve in boundary segment for room {{}}.".format(room_id_str))
                                    valid_segment_loop = False
                                    break
                                curves.Add(curve)

                            if not valid_segment_loop or curves.Count == 0:
                                print("# Warning: Skipping invalid or empty boundary loop for room {{}} (Loop Index {{}}).".format(room_id_str, i))
                                continue # Skip this specific loop, try others

                            try:
                                # Attempt to create a CurveLoop from the collected curves
                                curve_loop = CurveLoop.Create(curves)
                                all_curve_loops.Add(curve_loop)
                                has_valid_loops = True # Mark that we have something potentially usable
                            except RevitExceptions.InvalidOperationException as cle_ioe:
                                # CurveLoop creation can fail (e.g., non-contiguous, self-intersecting within loop)
                                print("# Warning: Could not create CurveLoop for a boundary of room {{}}. Revit API Error: {{}}".format(room_id_str, cle_ioe.Message))
                            except Exception as cle:
                                print("# Warning: Could not create CurveLoop for a boundary of room {{}}. Error: {{}}".format(room_id_str, cle))
                                # Continue to try processing other loops for the same room

                        # Only attempt to create FilledRegion if valid loops were formed
                        if has_valid_loops and all_curve_loops.Count > 0:
                            try:
                                # Create the Filled Region using the collected CurveLoops
                                # The API requires a List[CurveLoop] or IList<CurveLoop>
                                FilledRegion.Create(doc,
                                                    filled_region_type_id,
                                                    active_view.Id,
                                                    all_curve_loops) # Pass the generic List
                                created_count += 1
                                # Optional: print("# Successfully created FilledRegion for room {{}}.".format(room_id_str))
                            except RevitExceptions.InvalidOperationException as fre_ioe:
                                print("# Error: Failed to create FilledRegion for room {{}} (InvalidOperationException). API Error: {{}}".format(room_id_str, fre_ioe.Message))
                                skipped_count += 1
                            except Exception as fre:
                                print("# Error: Failed to create FilledRegion for room {{}}. Error: {{}}".format(room_id_str, fre))
                                skipped_count += 1
                        elif has_valid_loops and all_curve_loops.Count == 0:
                             # This case indicates CurveLoop.Create failed for all loops that had valid segments
                             print("# Warning: All potentially valid boundary loops failed CurveLoop creation for room {{}}.".format(room_id_str))
                             skipped_count += 1
                        elif not has_valid_loops:
                             # This case indicates no valid segments were found to even attempt CurveLoop creation
                             print("# Warning: No valid boundary loops could be processed for room {{}}.".format(room_id_str))
                             skipped_count += 1

                    except Autodesk.Revit.Exceptions.InvalidOperationException as ioe_room:
                         # Catch errors during GetBoundarySegments etc.
                         print("# Error processing room {{}} (InvalidOperationException): {{}}".format(room_id_str, ioe_room.Message))
                         skipped_count += 1
                    except Exception as e:
                        # Catch other unexpected errors during room processing
                        print("# Error processing room {{}}: {{}}".format(room_id_str, e))
                        skipped_count += 1

                # --- Optional Summary ---
                # These print statements can be useful for debugging in RevitPythonShell/pyRevit
                # but might be redundant if the C# wrapper handles logging.
                # print("# --- Script Summary ---")
                # print("# Processed {{}} rooms named '{{}}'.".format(len(rooms_to_process), TARGET_ROOM_NAME))
                # print("# Successfully created {{}} Filled Regions.".format(created_count))
                # if skipped_count > 0:
                #    print("# Skipped creating Filled Regions for {{}} rooms due to errors or boundary issues.".format(skipped_count))

# --- Final message (optional) ---
# print("# Script execution finished.")