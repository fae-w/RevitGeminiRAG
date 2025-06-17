# Purpose: This script highlights selected elements in the active Revit view using a filter and graphic overrides.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List, ICollection
from Autodesk.Revit.DB import (
    ElementId,
    OverrideGraphicSettings,
    Color,
    View,
    SelectionFilterElement,
    FilteredElementCollector
)

# --- Configuration ---
filter_name = "Highlight Selected Elements"
highlight_color = Color(255, 255, 0) # Yellow

# --- Get Active View and Selection ---
active_view = doc.ActiveView
if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or active view is invalid.")
else:
    # Check if the view supports filters and overrides
    if not active_view.AreGraphicsOverridesAllowed():
        print("# Error: The active view '{}' (Type: {}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
    else:
        selected_ids = uidoc.Selection.GetElementIds()

        if not selected_ids or selected_ids.Count == 0:
            print("# No elements selected. Nothing to highlight.")
        else:
            # Convert ICollection<ElementId> to List<ElementId> for filter creation if needed by API version
            # However, SelectionFilterElement.Create takes ICollection, so direct use is fine.
            # selected_id_list = List[ElementId](selected_ids) # Keep for reference if needed

            # --- Define Override Settings ---
            override_settings = OverrideGraphicSettings()
            # Apply yellow override to surface patterns (foreground)
            override_settings.SetSurfaceForegroundPatternVisible(True)
            override_settings.SetSurfaceForegroundPatternColor(highlight_color)
            # Apply yellow override to cut patterns (foreground)
            override_settings.SetCutForegroundPatternVisible(True)
            override_settings.SetCutForegroundPatternColor(highlight_color)
            # Optional: Make lines solid yellow too
            override_settings.SetProjectionLineColor(highlight_color)
            override_settings.SetCutLineColor(highlight_color)

            # --- Find and Remove Existing Filter with the Same Name ---
            collector = FilteredElementCollector(doc).OfClass(SelectionFilterElement)
            existing_filter_id = ElementId.InvalidElementId
            for existing_filter in collector:
                if existing_filter.Name == filter_name:
                    existing_filter_id = existing_filter.Id
                    try:
                        # Remove from view first if it exists there
                        if existing_filter_id in active_view.GetFilters():
                            active_view.RemoveFilter(existing_filter_id)
                        # Delete the filter element itself (Transaction handled externally)
                        doc.Delete(existing_filter_id)
                        # print("# Removed existing filter '{}'.".format(filter_name)) # Debug
                    except Exception as ex_remove:
                        print("# Warning: Could not remove existing filter '{}': {}".format(filter_name, ex_remove))
                    break # Assume only one filter with this name should exist

            # --- Create New Selection Filter Element ---
            new_filter = None
            try:
                # Create the filter using the current selection (Transaction handled externally)
                # Pass the ICollection directly
                new_filter = SelectionFilterElement.Create(doc, filter_name, selected_ids)
                # print("# Created new filter '{}' with {} elements.".format(filter_name, selected_ids.Count)) # Debug
            except Exception as ex_create:
                print("# Error creating filter '{}': {}".format(filter_name, ex_create))

            # --- Apply Filter to View ---
            if new_filter is not None and new_filter.IsValidObject:
                new_filter_id = new_filter.Id
                try:
                    # Add the filter to the active view (Transaction handled externally)
                    if new_filter_id not in active_view.GetFilters():
                         active_view.AddFilter(new_filter_id)

                    # Apply the graphic overrides (Transaction handled externally)
                    active_view.SetFilterOverrides(new_filter_id, override_settings)

                    # Ensure the filter is visible and enabled (Transaction handled externally)
                    active_view.SetFilterVisibility(new_filter_id, True) # Make elements matching filter VISIBLE
                    active_view.SetIsFilterEnabled(new_filter_id, True)  # Ensure the filter itself is active

                    print("# Applied filter '{}' to highlight {} selected elements in view '{}'.".format(filter_name, selected_ids.Count, active_view.Name))
                except Exception as ex_apply:
                    print("# Error applying filter '{}' to view '{}': {}".format(filter_name, active_view.Name, ex_apply))
            elif new_filter is None:
                 print("# Filter could not be created. Cannot apply highlight.")