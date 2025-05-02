# Purpose: This script creates or applies a filter to change the color of supply ducts in the active Revit view.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
clr.AddReference('System.Collections')

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    BuiltInParameter,
    ParameterFilterRuleFactory,
    FilterRule,         # Base class for rules list
    FilterStringRule,   # Specific rule type for strings
    FilterStringEquals, # Evaluator for string equality
    ElementParameterFilter,
    OverrideGraphicSettings,
    Color,
    View
)
# Import specific .NET types
from System.Collections.Generic import List
from System import String # Required for FilterStringRule value

# --- Configuration ---
filter_name = "Supply Ducts - Blue Lines"
target_category_bic = BuiltInCategory.OST_DuctCurves
# Assumption: Filtering based on the 'System Classification' parameter.
param_bip = BuiltInParameter.RBS_SYSTEM_CLASSIFICATION_PARAM
system_classification_value = "Supply Air" # Case-sensitive value
override_color = Color(0, 0, 255) # Blue

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View):
    print("# Error: Active document context is not a View.")
elif not active_view.AreGraphicsOverridesAllowed():
    print("# Error: Filters and overrides are not allowed in the current view type: {}".format(active_view.ViewType))
else:
    # --- Define Categories ---
    categories = List[ElementId]()
    target_category_id = ElementId(target_category_bic)
    if target_category_id == ElementId.InvalidElementId:
        print("# Error: Could not find ElementId for BuiltInCategory: {}".format(target_category_bic))
    else:
        categories.Add(target_category_id)

        # --- Define Override Settings ---
        ogs = OverrideGraphicSettings()
        ogs.SetProjectionLineColor(override_color)
        # Optional: Uncomment to also override cut lines if desired
        # ogs.SetCutLineColor(override_color)

        # --- Check if Filter Already Exists ---
        existing_filter_id = ElementId.InvalidElementId
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for pfe in collector:
            if pfe.Name == filter_name:
                existing_filter_id = pfe.Id
                print("# Filter named '{}' already exists. Using existing filter.".format(filter_name))
                break

        filter_id_to_apply = ElementId.InvalidElementId

        if existing_filter_id != ElementId.InvalidElementId:
            filter_id_to_apply = existing_filter_id
            # Assumption: If the filter exists, its rules and categories are correct.
            # If you need to *update* an existing filter's rules, that's more complex.
        else:
            # --- Create Filter Rule ---
            param_id = ElementId(param_bip)
            if param_id == ElementId.InvalidElementId:
                 print("# Error: Could not find ElementId for BuiltInParameter: {}".format(param_bip))
            else:
                try:
                    # Rule: System Classification == "Supply Air" (Case-sensitive)
                    str_evaluator = FilterStringEquals()
                    # Need to pass System.String for the value, True for case-sensitivity
                    rule = ParameterFilterRuleFactory.CreateRule(param_id, str_evaluator, String(system_classification_value), True)

                    if not rule:
                        print("# Error: Failed to create filter rule.")
                    else:
                        # --- Wrap Rule in ElementParameterFilter ---
                        # ParameterFilterElement.Create requires an ElementFilter
                        rules_list = List[FilterRule]()
                        rules_list.Add(rule)
                        element_filter = ElementParameterFilter(rules_list)

                        # --- Create the Parameter Filter Element ---
                        try:
                            new_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                            filter_id_to_apply = new_filter.Id
                            print("# Created new filter: '{}'".format(filter_name))
                        except Exception as e_create:
                            # Handle potential duplicate name error more gracefully if check failed somehow
                            if "name is already in use" in str(e_create).lower():
                                print("# Warning: Filter creation failed for duplicate name '{}', attempting to find existing.".format(filter_name))
                                collector_retry = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                                for pfe_retry in collector_retry:
                                    if pfe_retry.Name == filter_name:
                                        filter_id_to_apply = pfe_retry.Id
                                        break
                                if filter_id_to_apply != ElementId.InvalidElementId:
                                    print("# Found existing filter with duplicate name: '{}'".format(filter_name))
                                else:
                                    print("# Error: Filter creation failed for duplicate name '{}', and could not find existing filter.".format(filter_name))
                            else:
                                print("# Error creating ParameterFilterElement '{}': {}".format(filter_name, e_create))

                except Exception as e_rule:
                    print("# Error creating filter rule or element filter: {}".format(e_rule))
                    print("# Ensure the parameter '{}' exists and is applicable to '{}'.".format(param_bip, target_category_bic))

        # --- Apply Filter to Active View ---
        if filter_id_to_apply != ElementId.InvalidElementId:
            try:
                # Check if the filter is already added to the view
                applied_filters = active_view.GetFilters()
                if filter_id_to_apply not in applied_filters:
                    active_view.AddFilter(filter_id_to_apply)
                    print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                else:
                     print("# Filter '{}' was already present in view '{}'.".format(filter_name, active_view.Name))

                # Apply the overrides (this will update overrides if filter was already present)
                active_view.SetFilterOverrides(filter_id_to_apply, ogs)

                # Ensure the filter is enabled (visible) in the view
                active_view.SetFilterVisibility(filter_id_to_apply, True)
                print("# Applied graphic overrides for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

            except Exception as e_apply:
                # Verify filter element still exists before blaming apply
                test_filter = doc.GetElement(filter_id_to_apply)
                if not test_filter:
                     print("# Error: Filter ID {} became invalid before applying to view '{}'. Filter may have been deleted.".format(filter_id_to_apply, active_view.Name))
                else:
                     print("# Error applying filter '{}' (ID: {}) or setting overrides in view '{}': {}".format(filter_name, filter_id_to_apply, active_view.Name, e_apply))
        elif existing_filter_id == ElementId.InvalidElementId:
             # This path means filter creation failed and no existing one was found
             print("# Filter was not created and could not be applied.")

    # Final status message check
    if filter_id_to_apply == ElementId.InvalidElementId and existing_filter_id == ElementId.InvalidElementId:
        print("# Failed to create or find the filter '{}'.".format(filter_name))
    elif filter_id_to_apply != ElementId.InvalidElementId:
        # Check if overrides were actually set (GetFilterOverrides returns default if not set)
        try:
            current_overrides = active_view.GetFilterOverrides(filter_id_to_apply)
            if current_overrides and current_overrides.ProjectionLineColor == override_color:
                print("# Script finished. Filter '{}' should be configured and applied with blue projection lines to view '{}'.".format(filter_name, active_view.Name))
            else:
                 print("# Script finished, but verification of overrides failed for filter '{}' in view '{}'.".format(filter_name, active_view.Name))
        except Exception as e_verify:
             print("# Script finished, but could not verify overrides for filter '{}' in view '{}' due to error: {}".format(filter_name, active_view.Name, e_verify))