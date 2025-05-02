# Purpose: This script applies a halftone override to generic models in the active Revit view using a filter.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    ElementCategoryFilter,
    Category,
    ViewType,
    ParameterFilterUtilities # To check if category is filterable
)

# --- Configuration ---
filter_name = "Halftone Generic Models Filter"
target_bic = BuiltInCategory.OST_GenericModel

# --- Get Generic Models Category ---
generic_models_category = Category.GetCategory(doc, target_bic)
if generic_models_category is None:
    print("# Error: Generic Models category (OST_GenericModel) not found in the document.")
    # Stop execution if the category doesn't exist
    filter_element = None
else:
    generic_models_category_id = generic_models_category.Id

    # Check if the category is filterable (recommended practice)
    filterable_categories = ParameterFilterUtilities.GetAllFilterableCategories()
    if generic_models_category_id not in filterable_categories:
        print("# Error: The 'Generic Models' category (OST_GenericModel) is not filterable in this Revit version or context.")
        filter_element = None
    else:
        filter_element = None

        # --- Find or Create Filter Element ---
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for existing_filter in collector:
            if existing_filter.Name == filter_name:
                filter_element = existing_filter
                # print("# Using existing filter: '{}'".format(filter_name)) # Debug
                break

        # If the filter doesn't exist, create it
        if filter_element is None:
            # print("# Creating new filter: '{}'".format(filter_name)) # Debug
            # Define the categories the filter applies to (needed for filter creation)
            categories_for_filter = List[ElementId]()
            categories_for_filter.Add(generic_models_category_id)

            # Create the filter rule: select elements of the Generic Models category
            element_category_filter_rule = ElementCategoryFilter(target_bic)

            try:
                # Create the ParameterFilterElement (Transaction managed externally)
                filter_element = ParameterFilterElement.Create(
                    doc,
                    filter_name,
                    categories_for_filter,
                    element_category_filter_rule
                )
                # print("# Filter '{}' created successfully.".format(filter_name)) # Debug
            except Exception as create_ex:
                print("# Error creating filter '{}': {}".format(filter_name, create_ex))
                filter_element = None # Ensure filter_element is None if creation failed

# --- Apply Filter to Active View ---
if filter_element is not None:
    filter_id = filter_element.Id
    active_view = doc.ActiveView

    if active_view is not None and active_view.IsValidObject:
        # Check if the view is a section view as requested
        if active_view.ViewType != ViewType.Section:
             print("# Warning: The active view '{}' is not a Section View, but attempting to apply filter anyway.".format(active_view.Name))

        # Check if the view type supports filters/overrides
        if active_view.AreGraphicsOverridesAllowed():
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
        else:
            print("# Error: View '{}' (Type: {}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
    else:
        print("# Error: No active view found or the active view is invalid.")
elif generic_models_category is not None: # Only print if category existed but filter failed creation/finding
   print("# Filter '{}' could not be found or created. Cannot apply to view.".format(filter_name))