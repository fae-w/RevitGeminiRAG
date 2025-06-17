# Purpose: This script crops a Revit view using the boundary defined by selected walls.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewPlan,
    View,
    Wall,
    CurveLoop,
    Line,
    Arc,
    LocationCurve,
    ViewCropRegionShapeManager,
    ElementId,
    BuiltInCategory # Although not used for filtering, useful for understanding
)
from System.Collections.Generic import List, IList
import System # For exception handling

# --- Configuration ---
target_view_name = "Parking" # Name of the target Floor Plan view

# --- Step 1: Find the Target View ---
target_view = None
view_collector = FilteredElementCollector(doc).OfClass(ViewPlan) # Look for ViewPlan specifically
for view in view_collector:
    if view.IsTemplate:
        continue # Skip view templates
    if view.Name == target_view_name:
        target_view = view
        break

if not target_view:
    print("# Error: ViewPlan named '{}' not found.".format(target_view_name))
else:
    # --- Step 2: Get Selected Walls ---
    selected_ids = uidoc.Selection.GetElementIds()
    selected_walls = []
    if not selected_ids or selected_ids.Count == 0:
        print("# Error: No elements selected. Please select walls defining the desired crop boundary.")
    else:
        for element_id in selected_ids:
            element = doc.GetElement(element_id)
            if isinstance(element, Wall):
                selected_walls.append(element)

        if not selected_walls:
            print("# Error: No walls found among the selected elements.")
        else:
            # --- Step 3: Extract Wall Location Curves ---
            wall_curves = List[Autodesk.Revit.DB.Curve]()
            valid_curves = True
            for wall in selected_walls:
                loc_curve = wall.Location
                if isinstance(loc_curve, LocationCurve) and loc_curve.Curve:
                    # Check if curve is bound (has start/end points)
                    if loc_curve.Curve.IsBound:
                         wall_curves.Add(loc_curve.Curve)
                    else:
                         print("# Warning: Wall ID {} has an unbound location curve. Skipping.".format(wall.Id))
                         # valid_curves = False # Optionally treat this as a failure
                         # break
                else:
                    print("# Error: Could not get valid LocationCurve for Wall ID {}. Cannot proceed.".format(wall.Id))
                    valid_curves = False
                    break

            if valid_curves and wall_curves.Count > 0:
                # --- Step 4: Attempt to Create CurveLoop ---
                # Note: This assumes the selected wall curves *can* form a single closed loop.
                # Revit's CurveLoop.Create requires the curves to be contiguous and ordered correctly.
                # This simple approach might fail if walls are selected out of order or have gaps.
                # A more robust implementation would involve sorting/connecting curves.
                try:
                    # Ensure curves are added in a specific order if possible (though not guaranteed here)
                    # A simple list creation might not preserve order needed by CurveLoop.Create
                    # If this fails, manual sorting/connecting logic is needed.
                    curve_loop = CurveLoop.Create(wall_curves)

                    # --- Step 5: Get View Crop Manager ---
                    try:
                        crop_manager = target_view.GetCropRegionShapeManager()

                        # --- Step 6: Check View Compatibility ---
                        if not crop_manager.CanHaveShape:
                            print("# Error: The target view '{}' (Type: {}) does not support non-rectangular crop shapes.".format(target_view_name, target_view.ViewType))
                        else:
                            # --- Step 7: Validate the CurveLoop ---
                            # Note: The CurveLoop needs to be planar and parallel to the view's plane.
                            # Location curves from walls in a plan view *should* satisfy this.
                            is_valid_shape = crop_manager.IsCropRegionShapeValid(curve_loop)

                            if is_valid_shape:
                                # --- Step 8: Apply the Crop Shape ---
                                try:
                                    crop_manager.SetCropShape(curve_loop)
                                    # Ensure the view's Crop Region Visible and Crop View properties are enabled
                                    if not target_view.CropBoxVisible:
                                        target_view.CropBoxVisible = True
                                    if not target_view.CropBoxActive:
                                        target_view.CropBoxActive = True # Crop View property
                                    print("# Successfully set crop shape for view '{}' based on {} selected walls.".format(target_view_name, len(selected_walls)))
                                except System.ArgumentException as arg_ex:
                                    print("# Error applying crop shape: ArgumentException - {}. Boundary might be invalid (e.g., self-intersecting, not closed, not planar).".format(arg_ex.Message))
                                except Autodesk.Revit.Exceptions.InvalidOperationException as op_ex:
                                     print("# Error applying crop shape: InvalidOperationException - {}. Crop may already be split or view incompatible.".format(op_ex.Message))
                                except Exception as set_ex:
                                    print("# Error applying crop shape: Unexpected error - {}".format(set_ex))
                            else:
                                print("# Error: The boundary formed by the selected walls is not valid for a crop shape (may not be closed, may self-intersect, or not contain straight lines parallel to the view plane).")

                    except Autodesk.Revit.Exceptions.InvalidOperationException as crop_mgr_ex:
                        print("# Error getting Crop Manager: View might not support crop regions or have other issues. Details: {}".format(crop_mgr_ex.Message))
                    except Exception as e_crop_mgr:
                        print("# Error accessing Crop Manager for view '{}'. Details: {}".format(target_view_name, e_crop_mgr))

                except System.ArgumentException as cl_ex:
                    print("# Error creating CurveLoop: {}. Ensure selected walls form a single, closed, non-self-intersecting loop and are selected in order.".format(cl_ex.Message))
                except Exception as e_cl:
                    print("# Error creating CurveLoop from wall curves: {}".format(e_cl))

            elif wall_curves.Count == 0 and valid_curves:
                 print("# Error: No valid location curves could be extracted from the selected walls.")
            # else: Error message printed in loop