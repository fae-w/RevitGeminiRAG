# Purpose: This script applies a specified filter to the active Revit view if it's not already applied.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections') # Required for List/ICollection handling if needed

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    View
)
# Import necessary .NET types if directly used (like List<T>), though often not needed for simple iteration/checking
# from System.Collections.Generic import List

# --- Configuration ---
target_filter_name = "Fire Rated Walls - 1hr"

# --- Main Script ---
active_view = doc.ActiveView

# Validate active view
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Requires an active, non-template graphical view.")
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: Graphics overrides are not allowed in the active view '{}' (Type: {}).".format(active_view.Name, active_view.ViewType))
else:
    # Find the existing filter by name
    filter_to_apply = None
    filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    for f in filter_collector:
        if f.Name == target_filter_name:
            filter_to_apply = f
            break # Found the filter

    if filter_to_apply is None:
        print("# Error: Filter named '{}' not found in the project.".format(target_filter_name))
    else:
        filter_id = filter_to_apply.Id

        # Check if the filter is already applied to the view
        try:
            applied_filters = active_view.GetFilters() # Returns ICollection<ElementId>
            is_already_applied = filter_id in applied_filters

            if is_already_applied:
                print("# Filter '{}' is already applied to the view '{}'.".format(target_filter_name, active_view.Name))
                # Optional: Ensure it's enabled if it was somehow disabled while applied
                # if not active_view.IsFilterEnabled(filter_id):
                #     active_view.SetIsFilterEnabled(filter_id, True)
                #     print("# Ensured filter '{}' is enabled in the view.".format(target_filter_name))
            else:
                # Apply the filter (Transaction handled externally)
                try:
                    active_view.AddFilter(filter_id)
                    # By default, AddFilter adds the filter enabled and visible with default overrides.
                    # Explicitly setting visibility/enablement might be needed if default behavior changes or specific state is desired.
                    # active_view.SetFilterVisibility(filter_id, True) # Ensure visible
                    # active_view.SetIsFilterEnabled(filter_id, True)   # Ensure overrides are enabled
                    print("# Successfully applied filter '{}' to the view '{}'.".format(target_filter_name, active_view.Name))
                except Exception as add_err:
                    print("# Error applying filter '{}' to view '{}': {}".format(target_filter_name, active_view.Name, add_err))

        except Exception as e:
            print("# An error occurred while checking or applying the filter: {}".format(e))