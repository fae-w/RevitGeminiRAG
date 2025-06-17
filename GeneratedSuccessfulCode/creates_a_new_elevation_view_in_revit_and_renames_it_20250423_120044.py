# Purpose: This script creates a new elevation view in Revit and renames it.

﻿# Mandatory Imports
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewFamilyType,
    ViewType,
    ElementId,
    XYZ,
    ElevationMarker,
    ViewPlan,
    ViewSection,
    View
)

# --- Configuration ---
desired_view_name = "North Facade Elevation"
# Assuming index 1 corresponds to North (0=E, 1=N, 2=W, 3=S)
# This assumption might be incorrect depending on the specific marker type/template.
north_facing_index = 1
# Default scale (e.g., 1/8" = 1'-0" is 96)
default_scale = 96
# Marker origin point (using 0,0,0 for simplicity)
marker_origin = XYZ(0, 0, 0)

# --- Helper Functions ---
def find_elevation_vft(doc_param):
    """Finds the first available Elevation ViewFamilyType."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        if vft.ViewFamily == ViewType.Elevation:
            # Check if it's suitable for creating new elevations (not a subtype meant only for referencing etc.)
            # This basic check assumes the first one found is usable. More specific checks might be needed.
             return vft.Id
    print("# Error: No suitable Elevation View Family Type found.")
    return ElementId.InvalidElementId

def is_view_name_unique(doc_param, name):
    """Checks if a view name is unique in the document."""
    existing_views = FilteredElementCollector(doc_param).OfClass(View).ToElements()
    for v in existing_views:
        if v.Name == name:
            return False
    return True

def get_unique_view_name(doc_param, base_name):
     """Generates a unique view name by appending numbers if necessary."""
     final_name = base_name
     counter = 1
     while not is_view_name_unique(doc_param, final_name):
         final_name = "{}_{}".format(base_name, counter)
         counter += 1
     return final_name

# --- Main Logic ---

# 1. Get the active view and check if it's a Plan View (required for placing marker and creating elevation)
active_view = doc.ActiveView
active_view_plan_id = ElementId.InvalidElementId
if active_view and isinstance(active_view, ViewPlan) and not active_view.IsTemplate:
    active_view_plan_id = active_view.Id
else:
    # Try to find *any* suitable plan view if active view isn't one
    plan_views = FilteredElementCollector(doc).OfClass(ViewPlan).WhereElementIsNotElementType().ToElements()
    for vp in plan_views:
        if not vp.IsTemplate: # Find the first non-template plan view
             active_view_plan_id = vp.Id
             print("# Info: Active view is not a Plan View or is a template. Using plan view '{}' (ID: {}) instead.".format(vp.Name, vp.Id))
             break

if active_view_plan_id == ElementId.InvalidElementId:
    print("# Error: No suitable Plan View found in the document to host the elevation marker.")
else:
    # 2. Find a suitable Elevation ViewFamilyType
    elevation_vft_id = find_elevation_vft(doc)

    if elevation_vft_id != ElementId.InvalidElementId:
        new_marker = None
        new_elevation_view = None
        try:
            # 3. Create the Elevation Marker
            # Use CreateElevationMarker, which doesn't require a viewPlanId at creation, just scale.
            # The elevation itself will be created relative to a plan view later.
            new_marker = ElevationMarker.CreateElevationMarker(doc, elevation_vft_id, marker_origin, default_scale)
            doc.Regenerate() # Regenerate to ensure the marker is fully available

            # 4. Create the Elevation View using the marker
            # CreateElevation requires the plan view ID where the marker is *visible*.
            # We use the active_view_plan_id found earlier.
            if new_marker:
                new_elevation_view = new_marker.CreateElevation(doc, active_view_plan_id, north_facing_index)
                doc.Regenerate() # Regenerate to make the new view fully available

                if new_elevation_view:
                    # 5. Rename the newly created view
                    try:
                        unique_name = get_unique_view_name(doc, desired_view_name)
                        if new_elevation_view.Name != unique_name:
                             new_elevation_view.Name = unique_name
                        print("# Successfully created elevation view '{}' (ID: {}).".format(unique_name, new_elevation_view.Id))
                    except Exception as rename_ex:
                        print("# Warning: Created elevation view (ID: {}) but failed to rename it to '{}'. Error: {}".format(new_elevation_view.Id, desired_view_name, rename_ex))
                else:
                    print("# Error: Failed to create elevation view from the marker.")
            else:
                 print("# Error: Failed to create the elevation marker.")

        except Exception as create_ex:
            print("# Error during elevation creation process: {}".format(create_ex))
            # Clean up marker if view creation failed? Risky without transaction control. Assume wrapper handles rollback on error.
            # if new_marker and not new_elevation_view:
            #     try:
            #         doc.Delete(new_marker.Id)
            #         print("# Info: Cleaned up unused elevation marker.")
            #     except:
            #          print("# Warning: Failed to clean up unused elevation marker.")

    else:
        # Error message for VFT not found is handled in the helper function.
        print("# View creation aborted due to missing Elevation View Family Type.")