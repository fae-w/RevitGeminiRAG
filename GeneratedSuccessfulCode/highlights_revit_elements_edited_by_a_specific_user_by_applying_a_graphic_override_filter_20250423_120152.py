# Purpose: This script highlights Revit elements edited by a specific user by applying a graphic override filter.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInParameter,
    ParameterFilterRuleFactory,
    FilterStringRule,
    FilterStringEquals, # Although RuleFactory is used, import for clarity if needed elsewhere
    ElementParameterFilter, # Filter based on parameters
    OverrideGraphicSettings,
    Color,
    View,
    ParameterFilterUtilities # To get filterable categories
)
# Import .NET List
from System.Collections.Generic import List, ICollection

# --- Configuration ---
filter_name = "Edited By User X"
target_username = "SpecificUserName" # Case-sensitive username
override_color = Color(0, 255, 255) # Cyan color

# --- Get Active View ---
active_view = doc.ActiveView

# Validate active view
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Requires an active, non-template graphical view.")
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: Graphics overrides are not allowed in the active view '{{}}'.".format(active_view.Name))
else:
    # --- Define Categories ---
    # Get all categories that can be used in filters for robustness
    # This ensures the filter can apply to any element type potentially edited by the user
    try:
         categories = ParameterFilterUtilities.GetAllFilterableCategories()
         if not categories or categories.Count == 0:
              raise ValueError("No filterable categories found.")
         # Convert ICollection to List for ParameterFilterElement.Create
         category_list = List[ElementId](categories)
    except Exception as cat_err:
         print("# Error: Could not get filterable categories: {{}}. Cannot create filter.".format(cat_err))
         category_list = None # Ensure script doesn't proceed without categories

    if category_list:
        # --- Define the Element Filter Logic ---
        # Get the ElementId for the 'Edited By' parameter
        edited_by_param_id = ElementId(BuiltInParameter.EDITED_BY)

        # Check if the parameter is valid (might not exist in non-workshared models or very old versions)
        param_element = doc.GetElement(edited_by_param_id)
        if not param_element:
             print("# Warning: BuiltInParameter.EDITED_BY ({{}}) not found in this document version/type.".format(edited_by_param_id.IntegerValue))
             # Attempt to proceed, filter might fail to match elements
        
        # Create the filter rule: 'Edited By' equals 'SpecificUserName'
        # Use ParameterFilterRuleFactory for creating rules
        try:
            # The evaluator needs to match the parameter type (String)
            filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(edited_by_param_id, target_username)
            # Create a list of rules (even if just one) for ElementParameterFilter
            filter_rules = List[FilterRule]()
            filter_rules.Add(filter_rule)
            # Create the ElementParameterFilter
            element_filter = ElementParameterFilter(filter_rules)
            filter_creation_success = True
        except Exception as rule_err:
             print("# Error creating filter rule or ElementParameterFilter: {{}}".format(rule_err))
             element_filter = None
             filter_creation_success = False

        if filter_creation_success and element_filter:
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
                # Optional: Update existing filter's categories and rules if needed
                # Note: This requires a transaction, assumed external.
                try:
                    # Update categories if they differ significantly
                    current_cats = existing_filter.GetCategories()
                    # Simple check if counts differ; more complex comparison might be needed
                    if len(current_cats) != len(category_list):
                         existing_filter.SetCategories(category_list)

                    # Update the filter rules (potentially more complex than just setting)
                    # For simplicity, we assume setting the new filter is sufficient if rules need change
                    # Re-creating the filter might be safer if logic changes substantially
                    existing_filter.SetElementFilter(element_filter)
                    # print("# Updated existing filter: {{}}".format(filter_name)) # Optional
                except Exception as update_err:
                    print("# Warning: Failed to update existing filter '{{}}': {{}}".format(filter_name, update_err))
            else:
                # --- Create New Filter ---
                # IMPORTANT: This creation requires a Transaction, which is assumed to be handled externally.
                try:
                    if ParameterFilterElement.IsNameUnique(doc, filter_name):
                        parameter_filter = ParameterFilterElement.Create(doc, filter_name, category_list, element_filter)
                        # print("# Created new filter: {{}}".format(filter_name)) # Optional
                    else:
                        # Should be caught by existence check, but added for safety
                        print("# Error: Filter name '{{}}' is already in use (but wasn't found directly).".format(filter_name))
                except Exception as e:
                    print("# Error creating filter '{{}}': {{}}".format(filter_name, e))

            # --- Apply Filter and Overrides to View ---
            if parameter_filter:
                # Define Override Graphic Settings
                override_settings = OverrideGraphicSettings()
                override_settings.SetProjectionLineColor(override_color)
                # Optional: Set other overrides like patterns, cut colors etc.
                # override_settings.SetSurfaceForegroundPatternColor(override_color)
                # override_settings.SetCutLineColor(override_color)

                # Apply the filter to the active view
                # IMPORTANT: Adding/modifying filters requires a Transaction, assumed external.
                try:
                    # Check if the filter is already applied to the view
                    applied_filters = active_view.GetFilters()
                    if parameter_filter.Id not in applied_filters:
                        active_view.AddFilter(parameter_filter.Id)
                        # print("# Added filter '{{}}' to view '{{}}'".format(filter_name, active_view.Name)) # Optional

                    # Set the overrides for the filter in the view
                    active_view.SetFilterOverrides(parameter_filter.Id, override_settings)

                    # Ensure the filter's graphic overrides are *enabled*
                    if not active_view.IsFilterEnabled(parameter_filter.Id):
                         active_view.SetIsFilterEnabled(parameter_filter.Id, True) # Enable filter overrides

                    # Ensure the filter doesn't hide the elements (Visibility = True)
                    if not active_view.GetFilterVisibility(parameter_filter.Id):
                         active_view.SetFilterVisibility(parameter_filter.Id, True)

                    # print("# Applied overrides for filter '{{}}' in view '{{}}'".format(filter_name, active_view.Name)) # Optional

                except Exception as e:
                    print("# Error applying filter or overrides to the view '{{}}': {{}}".format(active_view.Name, e))
            elif not existing_filter:
                # This case means creation failed and it didn't exist before
                print("# Filter '{{}}' could not be found or created.".format(filter_name))

# elif category_list was None:
    # Error already printed above if categories could not be retrieved.
    # pass