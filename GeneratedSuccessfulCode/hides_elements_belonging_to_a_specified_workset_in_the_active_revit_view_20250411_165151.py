# Purpose: This script hides elements belonging to a specified workset in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FilteredWorksetCollector,
    WorksetKind,
    WorksetId,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    ElementWorksetFilter,
    Category,
    CategoryType
)

# --- Configuration ---
filter_name = "Hide FF&E Workset Elements"
target_workset_name = "FF&E"
# --- End Configuration ---

# Get Active View
active_view = doc.ActiveView

# Check if view is valid and can have filters applied
if not active_view or not isinstance(active_view, View) or not active_view.AreGraphicsOverridesAllowed():
    print("# Error: Active view is not valid or does not support filters/overrides.")
else:
    # Check if the document is workshared
    if not doc.IsWorkshared:
        print("# Error: Document is not workshared. Cannot filter by workset.")
    else:
        # Find the target workset
        target_workset_id = WorksetId.InvalidWorksetId
        found_workset = None
        # Consider only user-created worksets
        workset_collector = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
        for ws in workset_collector:
            if ws.Name == target_workset_name:
                found_workset = ws
                target_workset_id = ws.Id
                break

        if target_workset_id == WorksetId.InvalidWorksetId:
            print("# Error: User workset named '{}' not found in the document.".format(target_workset_name))
        else:
            # Create the specific element filter for the target workset
            # The constructor takes (WorksetId worksetId, bool inverted)
            # inverted=False means select elements *belonging* to this workset.
            workset_element_filter = ElementWorksetFilter(target_workset_id, False)

            # Define categories for the ParameterFilterElement creation (API requirement)
            # It's best practice to include categories relevant to the filter's purpose,
            # although the ElementWorksetFilter itself doesn't depend on them.
            # We'll include common categories often placed on FF&E worksets.
            # Alternatively, collect all Model categories that allow bound parameters.
            categories_for_filter_creation = List[ElementId]()
            all_categories = doc.Settings.Categories
            for cat in all_categories:
                # Include model categories that typically host user-placed elements
                if cat and cat.CategoryType == CategoryType.Model and cat.AllowsBoundParameters:
                     # Additional check if category can have workset assigned might be needed,
                     # but AllowsBoundParameters is usually a good indicator.
                     # Check if category is not a subcategory (optional, usually not needed)
                     # if cat.Parent is None:
                     categories_for_filter_creation.Add(cat.Id)

            # Ensure at least one category is provided, otherwise ParameterFilterElement.Create fails
            if categories_for_filter_creation.Count == 0:
                 print("# Error: Could not find any suitable model categories for filter creation.")
                 parameter_filter = None # Prevent further processing
            else:
                # --- Find or Create Filter Element ---
                parameter_filter = None
                # Search for an existing filter with the same name
                filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                for existing_filter in filter_collector:
                    if existing_filter.Name == filter_name:
                        parameter_filter = existing_filter
                        # Optional: Could verify if the existing filter uses the correct WorksetId/rule
                        # print("# Using existing filter: '{}'".format(filter_name))
                        break

                if parameter_filter is None:
                    # Create the ParameterFilterElement if it doesn't exist
                    # This operation requires an external Transaction (assumed handled by C# wrapper)
                    try:
                        # print("# Creating new filter: '{}'".format(filter_name))
                        parameter_filter = ParameterFilterElement.Create(
                            doc,
                            filter_name,
                            categories_for_filter_creation, # List of categories associated with the filter
                            workset_element_filter          # The actual filtering logic based on workset
                        )
                    except Exception as create_ex:
                        print("# Error creating filter '{}': {}".format(filter_name, create_ex))
                        parameter_filter = None # Ensure it's None if creation failed

            # --- Apply Filter to Active View ---
            if parameter_filter is not None:
                filter_id = parameter_filter.Id
                try:
                    # Check if the filter is already applied to the view
                    applied_filter_ids = active_view.GetFilters()
                    if filter_id not in applied_filter_ids:
                        # Add the filter to the view
                        # This operation requires an external Transaction (assumed handled by C# wrapper)
                        active_view.AddFilter(filter_id)
                        # print("# Filter '{}' added to view '{}'.".format(filter_name, active_view.Name))

                    # Define the graphic overrides to hide elements
                    override_settings = OverrideGraphicSettings()
                    override_settings.SetVisibility(False) # Hide elements matching the filter

                    # Apply the overrides to the filter in the current view
                    # This operation requires an external Transaction (assumed handled by C# wrapper)
                    active_view.SetFilterOverrides(filter_id, override_settings)
                    # print("# Hide override applied for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

                except Exception as view_ex:
                    print("# Error applying filter or overrides to view '{}': {}".format(active_view.Name, view_ex))
            # Only print error if workset was found but filter creation/finding failed
            elif found_workset:
                print("# Filter '{}' could not be found or created. Cannot apply to view.".format(filter_name))