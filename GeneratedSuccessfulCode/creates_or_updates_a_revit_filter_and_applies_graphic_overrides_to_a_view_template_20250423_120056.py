# Purpose: This script creates or updates a Revit filter and applies graphic overrides to a view template.

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
filter_name = "Duct System - Return"
target_category_bic = BuiltInCategory.OST_DuctCurves
# Assumption: Filtering based on the 'System Classification' parameter.
param_bip = BuiltInParameter.RBS_SYSTEM_CLASSIFICATION_PARAM
system_classification_value = "Return Air" # Case-sensitive value
override_color = Color(128, 128, 128) # Grey
view_template_name = "Mechanical RCP"

# --- Find the View Template ---
view_template = None
collector_views = FilteredElementCollector(doc).OfClass(View)
for v in collector_views:
    if v.IsTemplate and v.Name == view_template_name:
        view_template = v
        break

if not view_template:
    print("# Error: View Template named '{}' not found.".format(view_template_name))
elif not isinstance(view_template, View):
     print("# Error: Found element named '{}' but it is not a View Template.".format(view_template_name))
elif not view_template.AreGraphicsOverridesAllowed():
    # This check might be less relevant for templates but good practice
    print("# Error: Filters and overrides are not allowed in the view template type: {}".format(view_template.ViewType))
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
        ogs.SetCutLineColor(override_color) # Apply to cut lines as well for consistency

        # --- Check if Filter Already Exists ---
        existing_filter_id = ElementId.InvalidElementId
        collector_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for pfe in collector_filters:
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
                    # Rule: System Classification == "Return Air" (Case-sensitive)
                    str_evaluator = FilterStringEquals()
                    # Need to pass System.String for the value, True for case-sensitivity
                    rule = ParameterFilterRuleFactory.CreateRule(param_id, str_evaluator, String(system_classification_value), True)

                    if not rule:
                        print("# Error: Failed to create filter rule.")
                    else:
                        # --- Wrap Rule in ElementParameterFilter ---
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

        # --- Apply Filter to the View Template ---
        if filter_id_to_apply != ElementId.InvalidElementId:
            try:
                # Check if the filter is already added to the view template
                applied_filters = view_template.GetFilters()
                if filter_id_to_apply not in applied_filters:
                    view_template.AddFilter(filter_id_to_apply)
                    print("# Added filter '{}' to view template '{}'.".format(filter_name, view_template_name))
                else:
                     print("# Filter '{}' was already present in view template '{}'.".format(filter_name, view_template_name))

                # Apply the overrides (this will update overrides if filter was already present)
                view_template.SetFilterOverrides(filter_id_to_apply, ogs)

                # Ensure the filter is enabled (visible) in the view template
                view_template.SetFilterVisibility(filter_id_to_apply, True)
                print("# Applied graphic overrides for filter '{}' in view template '{}'.".format(filter_name, view_template_name))

            except Exception as e_apply:
                # Verify filter element still exists before blaming apply
                test_filter = doc.GetElement(filter_id_to_apply)
                if not test_filter:
                     print("# Error: Filter ID {} became invalid before applying to view template '{}'. Filter may have been deleted.".format(filter_id_to_apply, view_template_name))
                else:
                     print("# Error applying filter '{}' (ID: {}) or setting overrides in view template '{}': {}".format(filter_name, filter_id_to_apply, view_template_name, e_apply))
        elif existing_filter_id == ElementId.InvalidElementId:
             # This path means filter creation failed and no existing one was found
             print("# Filter was not created and could not be applied.")

    # Final status message check
    if filter_id_to_apply == ElementId.InvalidElementId and existing_filter_id == ElementId.InvalidElementId:
        print("# Failed to create or find the filter '{}'.".format(filter_name))
    elif filter_id_to_apply != ElementId.InvalidElementId:
        # Check if overrides were actually set
        try:
            current_overrides = view_template.GetFilterOverrides(filter_id_to_apply)
            # Comparing colors directly can sometimes be tricky, check projection line color
            if current_overrides and current_overrides.ProjectionLineColor.IsValid and \
               current_overrides.ProjectionLineColor.Red == override_color.Red and \
               current_overrides.ProjectionLineColor.Green == override_color.Green and \
               current_overrides.ProjectionLineColor.Blue == override_color.Blue:
                print("# Script finished. Filter '{}' should be configured and applied with grey lines to view template '{}'.".format(filter_name, view_template_name))
            else:
                 print("# Script finished, but verification of overrides failed for filter '{}' in view template '{}'.".format(filter_name, view_template_name))
        except Exception as e_verify:
             print("# Script finished, but could not verify overrides for filter '{}' in view template '{}' due to error: {}".format(filter_name, view_template_name, e_verify))