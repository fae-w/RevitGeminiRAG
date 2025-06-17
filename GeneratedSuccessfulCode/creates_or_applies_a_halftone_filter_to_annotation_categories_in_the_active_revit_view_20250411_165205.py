# Purpose: This script creates or applies a halftone filter to annotation categories in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    Category,
    CategoryType,
    OverrideGraphicSettings,
    View,
    ParameterFilterUtilities # To check if category is filterable
)

# --- Configuration ---
filter_name = "Halftone All Annotations Filter"

# --- Get Active View ---
active_view = doc.ActiveView
if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or the active view is invalid.")
    # Stop processing if no valid active view
    active_view = None
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: View '{}' (Type: {}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
     # Stop processing if view doesn't support overrides
     active_view = None

# Proceed only if the view is valid and supports overrides
if active_view:

    # --- Get Filterable Annotation Categories relevant to the Active View ---
    all_categories = doc.Settings.Categories
    filterable_category_ids = ParameterFilterUtilities.GetAllFilterableCategories()
    annotation_category_ids = List[ElementId]()
    annotation_category_names = [] # For potential debug/error messages

    for cat in all_categories:
        # Check if it's an Annotation category
        is_annotation = cat.CategoryType == CategoryType.Annotation
        # Check if it's generally filterable
        is_filterable = cat.Id in filterable_category_ids
        # Check if its visibility/graphics can be controlled in this specific view
        is_controllable_in_view = False
        try:
            # AllowsVisibilityControl checks if the category appears in V/G dialog for the view
            # CanCategoryBeHidden checks if the category can be hidden/overridden via filters/V/G
            is_controllable_in_view = cat.AllowsVisibilityControl(active_view) and active_view.CanCategoryBeHidden(cat.Id)
        except Exception as check_ex:
            # Some categories might throw errors on these checks, treat them as not controllable
            # print("# Debug: Exception checking controllability for category '{}': {}".format(cat.Name, check_ex)) # Optional debug
            pass

        if is_annotation and is_filterable and is_controllable_in_view:
            annotation_category_ids.Add(cat.Id)
            annotation_category_names.append(cat.Name)

    if annotation_category_ids.Count == 0:
        print("# Error: No filterable annotation categories found that can be controlled in the active view '{}'.".format(active_view.Name))
        # Stop processing if no suitable categories found
        filter_element = None
    else:
        # --- Find or Create Filter Element ---
        filter_element = None
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for existing_filter in collector:
            if existing_filter.Name == filter_name:
                filter_element = existing_filter
                # print("# Using existing filter: '{}'".format(filter_name)) # Debug
                # Update categories for the existing filter to ensure it matches the current list
                try:
                    current_cats = set(existing_filter.GetCategories())
                    new_cats = set(annotation_category_ids)
                    if current_cats != new_cats:
                         # print("# Updating categories for existing filter '{}'".format(filter_name)) # Debug
                         existing_filter.SetCategories(annotation_category_ids)
                except Exception as update_ex:
                    print("# Warning: Failed to update categories for existing filter '{}': {}".format(filter_name, update_ex))
                    # Proceeding with existing filter, but categories might be outdated.
                break

        # If the filter doesn't exist, create it
        if filter_element is None:
            # print("# Creating new filter: '{}'".format(filter_name)) # Debug
            # print("# Categories included ({}): {}".format(len(annotation_category_names), ", ".join(annotation_category_names))) # Debug: List categories
            try:
                # Create the ParameterFilterElement (Transaction managed externally)
                # No rules needed to select all elements of the specified categories.
                # The overload without rules implies filtering based on the categories themselves.
                filter_element = ParameterFilterElement.Create(
                    doc,
                    filter_name,
                    annotation_category_ids
                )
                # print("# Filter '{}' created successfully.".format(filter_name)) # Debug
            except Exception as create_ex:
                print("# Error creating filter '{}': {}".format(filter_name, create_ex))
                # Print details about categories if creation fails, can be very long
                # print("# Attempted Categories: {}".format(", ".join(annotation_category_names)))
                filter_element = None # Ensure filter_element is None if creation failed

    # --- Apply Filter to Active View ---
    if filter_element is not None:
        filter_id = filter_element.Id
        try:
            # Check if the filter is already added to the view
            applied_filter_ids = active_view.GetFilters()
            if filter_id not in applied_filter_ids:
                # Add the filter to the view (Transaction managed externally)
                active_view.AddFilter(filter_id)
                # print("# Filter '{}' added to view '{}'.".format(filter_name, active_view.Name)) # Debug

            # Define the graphic overrides (set halftone to True)
            override_settings = OverrideGraphicSettings()
            override_settings.SetHalftone(True)

            # Apply the overrides to the filter in the view (Transaction managed externally)
            active_view.SetFilterOverrides(filter_id, override_settings)
            # print("# Halftone override applied for filter '{}' in view '{}'.".format(filter_name, active_view.Name)) # Debug

        except Exception as view_ex:
            print("# Error applying filter/overrides to view '{}': {}".format(active_view.Name, view_ex))

    elif annotation_category_ids.Count > 0: # Only print if categories existed but filter failed creation/finding
        print("# Filter '{}' could not be found or created. Cannot apply to view.".format(filter_name))

# else: handled by initial view check prints