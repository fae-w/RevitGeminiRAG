# Purpose: This script creates or applies a transparency filter to a Revit view template for the topography category.

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
    ParameterFilterUtilities # To check if category is filterable
)

# --- Configuration ---
filter_name = "Transparent Topography Filter"
target_bic = BuiltInCategory.OST_Topography
transparency_level = 70 # Transparency percentage (0-100)

# --- Get Active View and Check for Template ---
active_view = doc.ActiveView
target_view = None # This will be the view template if it exists

if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or the active view is invalid.")
else:
    template_id = active_view.ViewTemplateId
    if template_id is None or template_id == ElementId.InvalidElementId:
        print("# Info: The active view '{}' does not have a view template applied. No changes made.".format(active_view.Name))
    else:
        template_view = doc.GetElement(template_id)
        if isinstance(template_view, View):
            target_view = template_view
            # print("# Found view template: '{}'".format(target_view.Name)) # Debug info
        else:
            print("# Error: Could not retrieve a valid view template from the active view (ID: {}).".format(template_id))

# --- Proceed only if a valid view template was found ---
if target_view is not None:

    # --- Get Topography Category ---
    topography_category = Category.GetCategory(doc, target_bic)
    if topography_category is None:
        print("# Error: Topography category (OST_Topography) not found in the document.")
        filter_element = None
    else:
        topography_category_id = topography_category.Id

        # --- Check if the category is filterable ---
        filterable_categories = ParameterFilterUtilities.GetAllFilterableCategories()
        if topography_category_id not in filterable_categories:
            print("# Error: The 'Topography' category (OST_Topography) is not filterable in this Revit version or context.")
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
                # Define the categories the filter applies to
                categories_for_filter = List[ElementId]()
                categories_for_filter.Add(topography_category_id)

                # Create the filter rule: select elements of the Topography category
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

    # --- Apply Filter to View Template ---
    if filter_element is not None:
        filter_id = filter_element.Id

        # Check if the view template supports filters/overrides
        if target_view.AreGraphicsOverridesAllowed():
            try:
                # Check if the filter is already added to the view template
                applied_filter_ids = target_view.GetFilters()
                if filter_id not in applied_filter_ids:
                    # Add the filter to the view template (Transaction managed externally)
                    target_view.AddFilter(filter_id)
                    # print("# Filter '{}' added to view template '{}'.".format(filter_name, target_view.Name)) # Debug

                # Define the graphic overrides (set transparency)
                override_settings = OverrideGraphicSettings()
                override_settings.SetSurfaceTransparency(transparency_level)

                # Apply the overrides to the filter in the view template (Transaction managed externally)
                target_view.SetFilterOverrides(filter_id, override_settings)
                # print("# Transparency override ({}%) applied for filter '{}' in view template '{}'.".format(transparency_level, filter_name, target_view.Name)) # Debug

            except Exception as view_ex:
                print("# Error applying filter/overrides to view template '{}': {}".format(target_view.Name, view_ex))
        else:
            print("# Error: View template '{}' (Type: {}) does not support graphic overrides/filters.".format(target_view.Name, target_view.ViewType))
    elif topography_category is not None: # Only print if category existed but filter failed creation/finding
       print("# Filter '{}' could not be found or created. Cannot apply to view template '{}'.".format(filter_name, target_view.Name))

# else: # Case where no template was found was handled earlier
#    pass