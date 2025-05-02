# Purpose: This script applies graphic overrides to elements within a specified Design Option in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    ElementDesignOptionFilter, # Filter for elements in a specific Design Option
    DesignOption,              # To find the Design Option by name
    OverrideGraphicSettings,
    Color,
    View,
    ParameterFilterUtilities # To get filterable categories
)
# Import .NET List
from System.Collections.Generic import List

# --- Configuration ---
filter_name = "Design Option B - Orange"
target_design_option_name = "Option B" # Case-sensitive name of the Design Option
override_color = Color(255, 165, 0) # Orange color

# --- Find the target Design Option ElementId ---
target_design_option_id = ElementId.InvalidElementId
design_option_collector = FilteredElementCollector(doc).OfClass(DesignOption)
for do in design_option_collector:
    if do.Name == target_design_option_name:
        target_design_option_id = do.Id
        break

if target_design_option_id == ElementId.InvalidElementId:
    print("# Error: Design Option named '{}' not found in the document.".format(target_design_option_name))
else:
    # --- Get Active View ---
    active_view = doc.ActiveView

    # Validate active view
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
        print("# Error: Requires an active, non-template graphical view.")
    elif not active_view.AreGraphicsOverridesAllowed():
         print("# Error: Graphics overrides are not allowed in the active view '{}'.".format(active_view.Name))
    else:
        # --- Define Categories ---
        # Get all categories that can be used in filters for robustness
        # This ensures the filter can apply to any element type within the design option
        try:
             categories = ParameterFilterUtilities.GetAllFilterableCategories()
        except Exception as cat_err:
             print("# Warning: Could not get all filterable categories, using a limited default set. Error: {}".format(cat_err))
             # Fallback: Use a broad set if the utility method fails (less ideal)
             from Autodesk.Revit.DB import BuiltInCategory
             categories = List[ElementId]()
             categories.Add(ElementId(BuiltInCategory.OST_Walls))
             categories.Add(ElementId(BuiltInCategory.OST_Floors))
             categories.Add(ElementId(BuiltInCategory.OST_Roofs))
             categories.Add(ElementId(BuiltInCategory.OST_GenericModel))
             # Add more common categories if needed

        # --- Define the Element Filter Logic ---
        # Filter for elements belonging ONLY to the specified Design Option
        # False = Do not invert (i.e., match elements IN the design option)
        element_filter = ElementDesignOptionFilter(target_design_option_id, False)

        # --- Check for Existing Filter ---
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        parameter_filter = None
        if existing_filter:
            parameter_filter = existing_filter
            # Optional: Update existing filter's categories and rules if needed (requires transaction)
            # try:
            #     # Verify categories are up-to-date
            #     current_cats = existing_filter.GetCategories()
            #     if not all(cat_id in current_cats for cat_id in categories) or len(current_cats) != len(categories):
            #          existing_filter.SetCategories(categories)
            #     # Verify filter logic is correct (Can't directly compare ElementDesignOptionFilter, recreating might be safer if needed)
            #     # existing_filter.SetElementFilter(element_filter) # May need recreating if logic needs update
            #     # print("# Updated existing filter: {}".format(filter_name)) # Optional
            # except Exception as update_err:
            #     print("# Warning: Failed to update existing filter '{}': {}".format(filter_name, update_err))
        else:
            # --- Create New Filter ---
            # IMPORTANT: This creation requires a Transaction, which is assumed to be handled externally.
            try:
                if ParameterFilterElement.IsNameUnique(doc, filter_name):
                    parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                    # print("# Created new filter: {}".format(filter_name)) # Optional
                else:
                    # This case should ideally be caught by the existence check, but added for safety
                    print("# Error: Filter name '{}' is already in use (but wasn't found directly).".format(filter_name))
            except Exception as e:
                print("# Error creating filter '{}': {}".format(filter_name, e))

        # --- Apply Filter and Overrides to View ---
        if parameter_filter:
            # Define Override Graphic Settings
            override_settings = OverrideGraphicSettings()
            override_settings.SetProjectionLineColor(override_color)
            # Optional: Set other overrides if needed
            # override_settings.SetSurfaceForegroundPatternColor(override_color)
            # override_settings.SetSurfaceForegroundPatternId(solid_fill_pattern_id) # Need to get Solid Fill Pattern ID

            # Apply the filter to the active view
            # IMPORTANT: Adding/modifying filters requires a Transaction, assumed to be handled externally.
            try:
                # Check if the filter is already applied to the view
                applied_filters = active_view.GetFilters()
                if parameter_filter.Id not in applied_filters:
                    active_view.AddFilter(parameter_filter.Id)
                    # print("# Added filter '{}' to view '{}'".format(filter_name, active_view.Name)) # Optional

                # Set the overrides for the filter in the view
                active_view.SetFilterOverrides(parameter_filter.Id, override_settings)

                # Ensure the filter is enabled (might be added but disabled)
                # Note: SetFilterVisibility controls hide/show elements MATCHING the filter, not the override application.
                # We want the elements visible, so ensure visibility is True (or leave as default)
                # if not active_view.GetFilterVisibility(parameter_filter.Id):
                #      active_view.SetFilterVisibility(parameter_filter.Id, True)

                # Ensure the filter's graphic overrides are *enabled*
                if not active_view.IsFilterEnabled(parameter_filter.Id):
                     active_view.SetIsFilterEnabled(parameter_filter.Id, True) # Enable filter overrides

                # print("# Applied overrides for filter '{}' in view '{}'".format(filter_name, active_view.Name)) # Optional

            except Exception as e:
                print("# Error applying filter or overrides to the view '{}': {}".format(active_view.Name, e))
        elif not existing_filter:
            # This case means creation failed and it didn't exist before
            print("# Filter '{}' could not be found or created.".format(filter_name))