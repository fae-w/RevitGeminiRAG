# Purpose: This script creates filled regions representing external function floors in the active Revit view.

﻿# Purpose: Create a solid filled region graphically representing the boundary of each 'External' function floor in the active view.
# Note: This script assumes 'External' floors are defined by the 'Function' parameter set to 'Exterior'.
# It uses the first available FilledRegionType found in the document. The appearance depends on that type's settings.

import clr
clr.AddReference('System.Collections') # Required for List<T>
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Floor,
    FilledRegion,
    FilledRegionType,
    CurveLoop,
    Curve,
    Line,
    Arc,
    Ellipse,
    NurbSpline,
    ElementId,
    BuiltInParameter,
    View,
    Sketch,
    CurveArrArray,
    XYZ
)

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view or active view is not a valid View element.")
    # Use raise Exception() for better error handling in RevitPythonShell/pyRevit
    raise ValueError("No active view or active view is not a valid View element.")

view_id = active_view.Id

# --- Find the first available FilledRegionType ---
filled_region_type_id = ElementId.InvalidElementId
collector_frt = FilteredElementCollector(doc).OfClass(FilledRegionType)
first_frt = collector_frt.FirstElement()

if first_frt:
    filled_region_type_id = first_frt.Id
else:
    print("# Error: No FilledRegionType found in the document. Cannot create FilledRegions.")
    # Use raise Exception() instead of returning/exiting silently
    raise ValueError("No FilledRegionType found in the document.")

# --- Collect Floors in the Active View ---
collector_floors = FilteredElementCollector(doc, view_id).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType()

# --- Process External Floors ---
created_regions_count = 0
skipped_floors_count = 0
processed_floors_count = 0

for floor in collector_floors:
    if isinstance(floor, Floor):
        processed_floors_count += 1
        is_external = False
        try:
            # Check the Function parameter (1 typically corresponds to Exterior)
            function_param = floor.get_Parameter(BuiltInParameter.FUNCTION_PARAM)
            if function_param and function_param.HasValue:
                # Compare integer value; Exterior is enum value 1
                if function_param.AsInteger() == 1:
                    is_external = True
        except Exception as e:
            print("# Warning: Could not check 'Function' parameter for Floor {}: {}".format(floor.Id, e))
            # Continue processing other floors

        if is_external:
            floor_sketch = None
            try:
                floor_sketch = floor.GetSketch()
            except Exception as e:
                 print("# Warning: Could not retrieve sketch for Floor {}. Skipping. Error: {}".format(floor.Id, e))
                 skipped_floors_count += 1
                 continue # Skip this floor if sketch cannot be retrieved

            if floor_sketch:
                try:
                    profile_loops = floor_sketch.Profile # This is CurveArrArray
                    if profile_loops is None or profile_loops.IsEmpty:
                        print("# Warning: Floor {} has a sketch but no profile loops. Skipping.".format(floor.Id))
                        skipped_floors_count += 1
                        continue

                    curve_loops_list = List[CurveLoop]()
                    for curve_array in profile_loops:
                        if curve_array is None or curve_array.IsEmpty:
                            continue # Skip empty inner arrays

                        curves_for_loop = List[Curve]()
                        for curve in curve_array:
                            if curve: # Check if curve is valid
                                curves_for_loop.Add(curve)
                        
                        if curves_for_loop.Count > 0:
                            try:
                                # Attempt to create a CurveLoop
                                curve_loop = CurveLoop.Create(curves_for_loop)
                                # Basic check: Ensure curve loop is planar (Filled Regions require this)
                                # This is usually true for sketch profiles, but good to be aware
                                # if not curve_loop.IsPlane(active_view.ViewDirection): # More complex check, maybe unnecessary
                                #    print("# Warning: Curve loop for floor {} is not planar in view direction. Skipping loop.".format(floor.Id))
                                #    continue
                                curve_loops_list.Add(curve_loop)
                            except Exception as loop_ex:
                                print("# Warning: Could not create CurveLoop from curves for Floor {}. Skipping loop. Error: {}".format(floor.Id, loop_ex))


                    if curve_loops_list.Count > 0:
                        # Create the FilledRegion in the active view using the sketch loops
                        FilledRegion.Create(doc, filled_region_type_id, view_id, curve_loops_list)
                        created_regions_count += 1
                    else:
                        print("# Warning: No valid CurveLoops could be created from the profile of Floor {}. Skipping.".format(floor.Id))
                        skipped_floors_count += 1

                except Exception as e:
                    print("# Error processing Floor {}: {}. Skipping.".format(floor.Id, e))
                    skipped_floors_count += 1
            else:
                 # This case might happen if GetSketch() returns None without an exception
                 print("# Warning: Sketch not found for Floor {}. Skipping.".format(floor.Id))
                 skipped_floors_count += 1
        # else: # Floor is not external, just continue
        #    pass

# --- Final Report ---
if created_regions_count > 0:
    print("# Successfully created {} FilledRegions for external floors.".format(created_regions_count))
if skipped_floors_count > 0:
    print("# Skipped {} external floors due to errors or missing geometry.".format(skipped_floors_count))
if created_regions_count == 0 and skipped_floors_count == 0 and processed_floors_count > 0:
    print("# No floors with 'Function' set to 'Exterior' were found in the active view.")
elif processed_floors_count == 0:
    print("# No floor elements found in the active view.")