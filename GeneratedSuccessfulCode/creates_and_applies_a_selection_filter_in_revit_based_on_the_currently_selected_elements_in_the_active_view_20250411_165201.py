# Purpose: This script creates and applies a selection filter in Revit based on the currently selected elements in the active view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List, ICollection
from Autodesk.Revit.DB import (
    ElementId,
    OverrideGraphicSettings, # Although not used for overrides, good to have if modifying behavior later
    View,
    SelectionFilterElement,
    FilteredElementCollector
)

# --- Configuration ---
filter_name = "Show Only Selected Elements"

# --- Get Active View and Selection ---
active_view = doc.ActiveView
if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or active view is invalid.")
else:
    # Check if the view supports filters
    if not active_view.AreGraphicsOverridesAllowed():
        print("# Error: The active view '{{}}' (Type: {{}}) does not support filters.".format(active_view.Name, active_view.ViewType))
    else:
        selected_ids = uidoc.Selection.GetElementIds()

        if not selected_ids or selected_ids.Count == 0:
            print("# No elements selected. Cannot create filter.")
        else:
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
                        # print("# Removed existing filter '{{}}'.".format(filter_name)) # Debug
                    except Exception as ex_remove:
                        print("# Warning: Could not remove existing filter '{{}}': {{}}".format(filter_name, ex_remove))
                    break # Assume only one filter with this name should exist

            # --- Create New Selection Filter Element ---
            new_filter = None
            try:
                # Create the filter using the current selection (Transaction handled externally)
                new_filter = SelectionFilterElement.Create(doc, filter_name, selected_ids)
                # print("# Created new filter '{{}}' with {{}} elements.".format(filter_name, selected_ids.Count)) # Debug
            except Exception as ex_create:
                print("# Error creating filter '{{}}': {{}}".format(filter_name, ex_create))

            # --- Apply Filter to View ---
            if new_filter is not None and new_filter.IsValidObject:
                new_filter_id = new_filter.Id
                try:
                    # Add the filter to the active view (Transaction handled externally)
                    if new_filter_id not in active_view.GetFilters():
                         active_view.AddFilter(new_filter_id)

                    # --- Visibility Settings ---
                    # To "show only" selected elements using THIS filter, we ensure the filter is enabled
                    # and set to make matching elements VISIBLE.
                    # NOTE: This filter *by itself* does not hide other elements.
                    # Hiding non-selected elements typically requires hiding categories
                    # or using additional filters, which is beyond the scope of simply
                    # applying *this* selection filter. This script ensures the selected
                    # elements are targeted by an active filter set to 'Visible'.

                    # Ensure the filter is VISIBLE (i.e., elements matching it are shown)
                    active_view.SetFilterVisibility(new_filter_id, True)

                    # Ensure the filter is ENABLED in the view's V/G settings
                    active_view.SetIsFilterEnabled(new_filter_id, True)

                    # Optional: Apply overrides if needed (e.g., highlight)
                    # override_settings = OverrideGraphicSettings()
                    # override_settings.SetProjectionLineColor(Color(0,0,255)) # Example: Blue lines
                    # active_view.SetFilterOverrides(new_filter_id, override_settings)

                    print("# Applied filter '{{}}' targeting {{}} selected elements in view '{{}}'. Filter set to 'Visible'.".format(filter_name, selected_ids.Count, active_view.Name))
                except Exception as ex_apply:
                    # Attempt to remove partially added filter components if apply fails
                    try:
                         if new_filter_id in active_view.GetFilters():
                              active_view.RemoveFilter(new_filter_id)
                    except:
                         pass # Ignore errors during cleanup
                    print("# Error applying filter '{{}}' to view '{{}}': {{}}".format(filter_name, active_view.Name, ex_apply))
            elif new_filter is None:
                 print("# Filter could not be created. Cannot apply filter.")