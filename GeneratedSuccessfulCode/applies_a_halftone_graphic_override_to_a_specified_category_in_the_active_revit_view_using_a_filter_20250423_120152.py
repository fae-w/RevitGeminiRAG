# Purpose: This script applies a halftone graphic override to a specified category in the active Revit view using a filter.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    Category,
    OverrideGraphicSettings,
    View
)
import System # For exception handling

# --- Configuration ---
filter_name = "Halftone Furniture"
target_category_bic = BuiltInCategory.OST_Furniture

# --- Get Active View ---
active_view = doc.ActiveView
if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or the active view is invalid.")
    active_view = None # Ensure it's None to prevent further processing
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: View '{{}}' (Type: {{}}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
     active_view = None # Ensure it's None

# Proceed only if the view is valid and supports overrides
if active_view:
    # --- Get Category ID ---
    category = Category.GetCategory(doc, target_category_bic)
    if category is None:
        print("# Error: Category 'Furniture' (OST_Furniture) not found in the document.")
        filter_element = None # Mark as None to prevent further processing
    else:
        category_id = category.Id
        category_ids = List[ElementId]()
        category_ids.Add(category_id)

        # --- Find or Create Filter Element ---
        filter_element = None
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for existing_filter in collector:
            if existing_filter.Name == filter_name:
                filter_element = existing_filter
                # print("# Using existing filter: '{{}}'".format(filter_name)) # Debug
                # Ensure the categories are correct
                try:
                    current_cats = set(existing_filter.GetCategories())
                    if category_id not in current_cats or len(current_cats) != 1:
                        # print("# Updating categories for existing filter '{{}}'".format(filter_name)) # Debug
                        existing_filter.SetCategories(category_ids)
                except Exception as update_ex:
                    print("# Warning: Failed to verify/update categories for existing filter '{{}}': {{}}".format(filter_name, update_ex))
                    # Proceeding with existing filter, but categories might be incorrect.
                break

        # If the filter doesn't exist, create it
        if filter_element is None:
            # print("# Creating new filter: '{{}}'".format(filter_name)) # Debug
            try:
                # Create the ParameterFilterElement (Transaction managed externally)
                # No rules needed to select all elements of the specified categories.
                filter_element = ParameterFilterElement.Create(
                    doc,
                    filter_name,
                    category_ids
                )
                # print("# Filter '{{}}' created successfully.".format(filter_name)) # Debug
            except System.Exception as create_ex:
                print("# Error creating filter '{{}}': {{}}".format(filter_name, create_ex))
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
                # print("# Filter '{{}}' added to view '{{}}'.".format(filter_name, active_view.Name)) # Debug

            # Define the graphic overrides (set halftone to True)
            override_settings = OverrideGraphicSettings()
            override_settings.SetHalftone(True)

            # Apply the overrides to the filter in the view (Transaction managed externally)
            active_view.SetFilterOverrides(filter_id, override_settings)
            # print("# Halftone override applied for filter '{{}}' in view '{{}}'.".format(filter_name, active_view.Name)) # Debug

        except System.Exception as view_ex:
            print("# Error applying filter/overrides to view '{{}}': {{}}".format(active_view.Name, view_ex))

    elif category is not None: # Only print if category existed but filter failed creation/finding
        print("# Filter '{{}}' could not be found or created. Cannot apply to view.".format(filter_name))

# else: handled by initial view check prints