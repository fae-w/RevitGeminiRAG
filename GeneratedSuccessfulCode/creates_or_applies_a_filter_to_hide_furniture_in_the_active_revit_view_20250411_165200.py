# Purpose: This script creates or applies a filter to hide furniture in the active Revit view.

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
    Category
)

# --- Configuration ---
filter_name = "Hide Furniture Filter"
target_bic = BuiltInCategory.OST_Furniture

# --- Get Furniture Category ---
furniture_category = Category.GetCategory(doc, target_bic)
if furniture_category is None:
    print("# Error: Furniture category (OST_Furniture) not found in the document.")
    # Stop execution if the category doesn't exist
    filter_element = None
else:
    furniture_category_id = furniture_category.Id
    filter_element = None

    # --- Find or Create Filter Element ---
    # Check if a filter with the specified name already exists
    collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    for existing_filter in collector:
        if existing_filter.Name == filter_name:
            filter_element = existing_filter
            # print(f"# Using existing filter: '{filter_name}'") # Optional debug message
            break

    # If the filter doesn't exist, create it
    if filter_element is None:
        # print(f"# Creating new filter: '{filter_name}'") # Optional debug message
        # Define the categories the filter applies to (needed for filter creation)
        # Even though the rule targets Furniture, the filter needs associated categories.
        categories_for_filter = List[ElementId]()
        categories_for_filter.Add(furniture_category_id)

        # Create the filter rule: select elements of the Furniture category
        element_category_filter_rule = ElementCategoryFilter(target_bic)

        try:
            # Create the ParameterFilterElement (Transaction managed externally)
            filter_element = ParameterFilterElement.Create(
                doc,
                filter_name,
                categories_for_filter,
                element_category_filter_rule
            )
            # print(f"# Filter '{filter_name}' created successfully.") # Optional debug message
        except Exception as create_ex:
            print(f"# Error creating filter '{filter_name}': {{create_ex}}") # Escaped f-string
            filter_element = None # Ensure filter_element is None if creation failed

# --- Apply Filter to Active View ---
if filter_element is not None:
    filter_id = filter_element.Id
    active_view = doc.ActiveView

    if active_view is not None and active_view.IsValidObject:
        # Check if the view type supports filters/overrides
        if active_view.AreGraphicsOverridesAllowed():
            try:
                # Check if the filter is already added to the view
                applied_filter_ids = active_view.GetFilters()
                if filter_id not in applied_filter_ids:
                    # Add the filter to the view (Transaction managed externally)
                    active_view.AddFilter(filter_id)
                    # print(f"# Filter '{filter_name}' added to view '{active_view.Name}'.") # Optional debug message

                # Define the graphic overrides (set visibility to False)
                override_settings = OverrideGraphicSettings()
                override_settings.SetVisibility(False)

                # Apply the overrides to the filter in the view (Transaction managed externally)
                active_view.SetFilterOverrides(filter_id, override_settings)
                # print(f"# 'Hide' override applied for filter '{filter_name}' in view '{active_view.Name}'.") # Optional debug message

            except Exception as view_ex:
                print(f"# Error applying filter/overrides to view '{active_view.Name}': {{view_ex}}") # Escaped f-string
        else:
            print(f"# Error: View '{active_view.Name}' (Type: {{active_view.ViewType}}) does not support graphic overrides/filters.") # Escaped f-string
    else:
        print("# Error: No active view found or the active view is invalid.")
# elif furniture_category is not None: # Only print if category existed but filter failed
#     print(f"# Filter '{filter_name}' could not be found or created. Cannot apply to view.") # Optional message