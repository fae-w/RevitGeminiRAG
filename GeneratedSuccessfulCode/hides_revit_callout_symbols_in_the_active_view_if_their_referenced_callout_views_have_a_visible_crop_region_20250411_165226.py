# Purpose: This script hides Revit callout symbols in the active view if their referenced callout views have a visible crop region.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewSection,
    ElevationMarker,
    ViewType,
    ElementId,
    BuiltInParameter
)

# --- Main Script ---

# Get the active view
active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid project view or is a view template.")
else:
    elements_to_hide = List[ElementId]()
    processed_callout_symbols = 0
    target_callouts_found = 0

    # --- Process ViewSection based Callouts ---
    # These represent section callouts and potentially rectangular plan callouts
    try:
        collector_vs = FilteredElementCollector(doc, active_view.Id).OfClass(ViewSection).WhereElementIsNotElementType()
        for vs in collector_vs:
            processed_callout_symbols += 1
            try:
                # Get the ID of the view this ViewSection element creates/references
                ref_view_id = vs.ViewId
                if ref_view_id != ElementId.InvalidElementId:
                    ref_view = doc.GetElement(ref_view_id)
                    # Check if the referenced view is actually a Callout view
                    if ref_view and isinstance(ref_view, View) and ref_view.ViewType == ViewType.Callout:
                        # Check the 'Crop Region Visible' property (CropBoxVisible) of the Callout view
                        if ref_view.CropBoxVisible:
                            target_callouts_found += 1
                            # Check if the callout symbol (ViewSection) is not already hidden in the active view
                            if not vs.IsHidden(active_view):
                                if vs.Id not in elements_to_hide: # Ensure unique IDs
                                     elements_to_hide.Add(vs.Id)
            except Exception as e_vs:
                # print("# Warning: Could not process ViewSection {}: {}".format(vs.Id, e_vs)) # Optional Debug
                pass # Continue processing other elements
    except Exception as e_coll_vs:
        print("# Error collecting/processing ViewSections: {}".format(e_coll_vs))

    # --- Process ElevationMarker based Callouts ---
    # These represent elevation callouts
    try:
        collector_em = FilteredElementCollector(doc, active_view.Id).OfClass(ElevationMarker).WhereElementIsNotElementType()
        for marker in collector_em:
            processed_callout_symbols += 1
            try:
                # Check if this marker specifically creates Callout views
                if marker.IsCallout():
                    callout_view_ids = marker.GetCalloutViewIds()
                    marker_needs_hiding = False
                    for ref_view_id in callout_view_ids:
                         if ref_view_id != ElementId.InvalidElementId:
                            ref_view = doc.GetElement(ref_view_id)
                            # Check if the referenced view is a Callout and its CropBox is visible
                            if ref_view and isinstance(ref_view, View) and ref_view.ViewType == ViewType.Callout:
                                if ref_view.CropBoxVisible:
                                    target_callouts_found += 1 # Count each qualifying target view
                                    marker_needs_hiding = True
                                    break # Found one qualifying callout view, no need to check others for this marker

                    # If any associated callout view met the criteria, hide the marker
                    if marker_needs_hiding:
                         # Check if the marker symbol itself is not already hidden
                         if not marker.IsHidden(active_view):
                            if marker.Id not in elements_to_hide: # Ensure unique IDs
                                 elements_to_hide.Add(marker.Id)

            except Exception as e_em:
                 # print("# Warning: Could not process ElevationMarker {}: {}".format(marker.Id, e_em)) # Optional Debug
                 pass # Continue processing other elements
    except Exception as e_coll_em:
         print("# Error collecting/processing ElevationMarkers: {}".format(e_coll_em))


    # --- Hide Collected Elements ---
    if elements_to_hide.Count > 0:
        initial_hide_count = elements_to_hide.Count
        try:
            # Attempt to hide the collected callout symbols (Transaction managed externally)
            active_view.HideElements(elements_to_hide)
            # Assuming HideElements doesn't throw an error means it succeeded for the elements it could hide.
            print("# Attempted to hide {} Callout symbols in view '{}'. These symbols link to Callout views where 'Crop Region Visible' is True. (Processed {} potential symbols, found {} matching target views).".format(initial_hide_count, active_view.Name, processed_callout_symbols, target_callouts_found))
        except Exception as hide_e:
            # Report errors during the hiding process
            if "One or more of the elements cannot be hidden in the view" in str(hide_e):
                 print("# Warning: Could not hide {} callout symbols (some might be pinned, already hidden, or disallowed by view settings). Processed {} potential symbols.".format(initial_hide_count, processed_callout_symbols))
            else:
                print("# Error occurred while hiding elements in view '{}': {}".format(active_view.Name, hide_e))
    else:
        # No elements were added to the hide list
        print("# No visible Callout symbols found in view '{}' that link to Callout views with 'Crop Region Visible' = True. (Processed {} potential symbols, found {} matching target views).".format(active_view.Name, processed_callout_symbols, target_callouts_found))