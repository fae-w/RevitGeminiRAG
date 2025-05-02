# Purpose: This script hides Revit levels with negative elevations in the active view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ElementId,
    View,
    ViewType
)

# --- Main Script ---

# Get the active view
active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid project view or is a view template.")
else:
    # Check if the view type typically shows levels or supports hiding elements
    # Common views showing levels: Elevations, Sections, 3D.
    # Other views might list levels in properties but not display the datum itself.
    if active_view.ViewType not in [ViewType.Elevation, ViewType.Section, ViewType.ThreeD]:
         print("# Warning: Active view type ('{}') might not display Level datums visually. Hiding will affect elements associated with these levels in schedules or filters, but maybe not the visual datum.".format(active_view.ViewType))

    # Collect Level elements potentially visible or relevant in the active view
    # Note: Using FilteredElementCollector(doc, active_view.Id) might not capture all levels
    # if they aren't directly "visible" geometry in the view's primary space (e.g., Levels in a Plan view).
    # It's generally better to collect all Levels from the document and then hide them in the specific view.
    level_collector = FilteredElementCollector(doc).OfClass(Level)

    levels_to_hide = List[ElementId]()
    processed_count = 0
    hidden_count = 0

    for level in level_collector:
        if isinstance(level, Level):
            processed_count += 1
            try:
                # Using Level.Elevation which respects the project's Elevation Base setting.
                # Use level.ProjectElevation for elevation relative to Project Base Point always.
                elevation = level.Elevation

                # Check if elevation is below 0 (Revit internal units are feet)
                if elevation < 0.0:
                    # Check if the level is already hidden in the view (optional but good practice)
                    try:
                        # Need to check if the element itself can be hidden, not just if it's currently hidden
                        # Level datums might have specific rules. HideElements should handle it.
                        if not level.IsHidden(active_view):
                             levels_to_hide.Add(level.Id)
                             hidden_count += 1
                    except Exception as check_hide_e:
                         # If checking IsHidden fails, attempt to add anyway
                         # print("# Warning: Could not check if Level {} is hidden: {}".format(level.Id, check_hide_e)) # Debug
                         levels_to_hide.Add(level.Id)
                         hidden_count += 1 # Assume it wasn't hidden for counting

            except Exception as e:
                print("# Error processing Level ID {}: {}".format(level.Id, e))

    # --- Hide Collected Levels ---
    if levels_to_hide.Count > 0:
        try:
            # Hide the elements (Transaction managed externally)
            active_view.HideElements(levels_to_hide)
            print("# Attempted to hide {} Levels with Elevation below 0 in view '{}' (out of {} Levels processed).".format(hidden_count, active_view.Name, processed_count))
        except Exception as hide_e:
             # Check for specific errors related to hiding elements in the view
            if "Element cannot be hidden" in str(hide_e) or \
               "One or more of the elements cannot be hidden in the view" in str(hide_e):
                 print("# Warning: Some Levels could not be hidden in view '{}'. This might be due to view settings, element pinning, or other constraints.".format(active_view.Name))
            elif "View type does not support element hiding" in str(hide_e): # Check view type support
                 print("# Error: The current view ('{}', type: {}) does not support hiding elements.".format(active_view.Name, active_view.ViewType))
            else:
                print("# Error occurred while hiding Levels in view '{}': {}".format(active_view.Name, hide_e))
    else:
        print("# No Levels found with Elevation below 0 to hide in view '{}' ({} Levels processed).".format(active_view.Name, processed_count))