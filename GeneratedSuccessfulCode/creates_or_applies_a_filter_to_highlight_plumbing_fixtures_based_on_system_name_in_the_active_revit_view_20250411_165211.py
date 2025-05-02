# Purpose: This script creates or applies a filter to highlight plumbing fixtures based on system name in the active Revit view.

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
    FilterRule,
    FilterStringRule, # Used for string comparisons
    FilterStringEquals, # Specific evaluator for string equality
    ElementParameterFilter,
    LogicalOrFilter,
    OverrideGraphicSettings,
    Color,
    View,
    FillPatternElement,
    FillPatternTarget,
    ElementFilter # Base class for filters used in LogicalOrFilter
)
from System.Collections.Generic import List, ICollection
from System import String # Required for certain API method signatures like CreateEqualsRule

# --- Helper function to find the Solid Fill pattern ---
def find_solid_fill_pattern(doc):
    """Finds the first solid fill drafting pattern element."""
    fill_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    for pattern_element in fill_patterns:
        if pattern_element is not None:
            try:
                pattern = pattern_element.GetFillPattern()
                # Check if pattern is valid, IsSolidFill is True, and target is Drafting
                if pattern and pattern.IsSolidFill and pattern.Target == FillPatternTarget.Drafting:
                    return pattern_element.Id
            except Exception:
                # Handle potential errors getting pattern details
                continue
    return ElementId.InvalidElementId

# --- Configuration ---
filter_name = "Plumbing Fixtures - Domestic Water"
target_category_bic = BuiltInCategory.OST_PlumbingFixtures
# Parameter assumption: Using 'System Name' parameter.
param_bip = BuiltInParameter.RBS_SYSTEM_NAME_PARAM
system_name_1 = "Domestic Cold Water" # Case-sensitive system name
system_name_2 = "Domestic Hot Water" # Case-sensitive system name
override_color = Color(0, 0, 255) # Blue

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View):
    print("# Error: Active document context is not a View.")
elif not active_view.AreGraphicsOverridesAllowed():
    print("# Error: Filters and overrides are not allowed in the current view type: {{}}".format(active_view.ViewType))
else:
    # --- Check if Filter Already Exists ---
    existing_filter_id = ElementId.InvalidElementId
    collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    for pfe in collector:
        if pfe.Name == filter_name:
            existing_filter_id = pfe.Id
            print("# Filter named '{{}}' already exists. Using existing filter.".format(filter_name))
            break

    filter_id_to_apply = ElementId.InvalidElementId

    if existing_filter_id != ElementId.InvalidElementId:
        filter_id_to_apply = existing_filter_id
        # Assume the existing filter is correctly defined for this script's purpose.
    else:
        # --- Create Filter Rules ---
        param_id = ElementId(param_bip)
        if param_id == ElementId.InvalidElementId:
             print("# Error: Could not find ElementId for BuiltInParameter: {{}}".format(param_bip))
        else:
            try:
                # Rule 1: System Name == "Domestic Cold Water"
                str_evaluator = FilterStringEquals()
                # Using System.String for value, True for case-sensitivity
                rule1 = ParameterFilterRuleFactory.CreateRule(param_id, str_evaluator, String(system_name_1), True)

                # Rule 2: System Name == "Domestic Hot Water"
                rule2 = ParameterFilterRuleFactory.CreateRule(param_id, str_evaluator, String(system_name_2), True)

                # --- Combine Rules with LogicalOrFilter ---
                # LogicalOrFilter requires a list of ElementFilters, not FilterRules directly.
                # Wrap each rule in an ElementParameterFilter.
                element_filter1 = ElementParameterFilter(rule1)
                element_filter2 = ElementParameterFilter(rule2)
                or_filter_elements = List[ElementFilter]()
                or_filter_elements.Add(element_filter1)
                or_filter_elements.Add(element_filter2)
                logical_or_filter = LogicalOrFilter(or_filter_elements)

                # --- Define Categories ---
                categories = List[ElementId]()
                target_category_id = ElementId(target_category_bic)
                if target_category_id == ElementId.InvalidElementId:
                    print("# Error: Could not find ElementId for BuiltInCategory: {{}}".format(target_category_bic))
                else:
                    categories.Add(target_category_id)

                    # --- Create the Parameter Filter Element ---
                    try:
                        # Pass the LogicalOrFilter containing the ElementParameterFilters
                        new_filter = ParameterFilterElement.Create(doc, filter_name, categories, logical_or_filter)
                        filter_id_to_apply = new_filter.Id
                        print("# Created new filter: '{{}}'".format(filter_name))
                    except Exception as e_create:
                        # Handle potential duplicate name error more gracefully
                        if "name is already in use" in str(e_create).lower():
                            print("# Warning: Filter creation failed for duplicate name '{{}}', attempting to find existing.".format(filter_name))
                            collector_retry = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                            for pfe_retry in collector_retry:
                                if pfe_retry.Name == filter_name:
                                    filter_id_to_apply = pfe_retry.Id
                                    break
                            if filter_id_to_apply != ElementId.InvalidElementId:
                                print("# Found existing filter with duplicate name: '{{}}'".format(filter_name))
                            else:
                                print("# Error: Filter creation failed for duplicate name '{{}}', and could not find existing filter.".format(filter_name))
                        else:
                            print("# Error creating ParameterFilterElement '{{}}': {{}}".format(filter_name, e_create))

            except Exception as e_rule:
                print("# Error creating filter rules or logical filter: {{}}".format(e_rule))
                print("# Ensure the parameter '{{}}' exists and is applicable to '{{}}'.".format(param_bip, target_category_bic))

    # --- Apply Filter to Active View ---
    if filter_id_to_apply != ElementId.InvalidElementId:
        # Find solid fill pattern
        solid_fill_id = find_solid_fill_pattern(doc)
        if solid_fill_id == ElementId.InvalidElementId:
            print("# Warning: Could not find a 'Solid fill' drafting pattern. Color override might not be fully visible without a pattern.")

        # --- Define Override Settings ---
        ogs = OverrideGraphicSettings()
        # Apply color to projection/surface lines
        ogs.SetProjectionLineColor(override_color)
        # Apply color to projection/surface fill
        ogs.SetSurfaceForegroundPatternColor(override_color)
        if solid_fill_id != ElementId.InvalidElementId:
             ogs.SetSurfaceForegroundPatternVisible(True)
             ogs.SetSurfaceForegroundPatternId(solid_fill_id)
        else:
             ogs.SetSurfaceForegroundPatternVisible(False) # Hide if no pattern found

        # Apply color to cut lines
        ogs.SetCutLineColor(override_color)
        # Apply color to cut fill
        ogs.SetCutForegroundPatternColor(override_color)
        if solid_fill_id != ElementId.InvalidElementId:
            ogs.SetCutForegroundPatternVisible(True)
            ogs.SetCutForegroundPatternId(solid_fill_id)
        else:
            ogs.SetCutForegroundPatternVisible(False) # Hide if no pattern found

        # Apply to view
        try:
            # Check if the filter is already added to the view
            applied_filters = active_view.GetFilters()
            if filter_id_to_apply not in applied_filters:
                active_view.AddFilter(filter_id_to_apply)
                print("# Added filter '{{}}' to view '{{}}'.".format(filter_name, active_view.Name))
            else:
                 print("# Filter '{{}}' was already present in view '{{}}'.".format(filter_name, active_view.Name))

            # Apply the overrides (this will update overrides if filter was already present)
            active_view.SetFilterOverrides(filter_id_to_apply, ogs)

            # Ensure the filter is enabled (visible) in the view
            active_view.SetFilterVisibility(filter_id_to_apply, True)
            print("# Applied graphic overrides for filter '{{}}' in view '{{}}'.".format(filter_name, active_view.Name))

        except Exception as e_apply:
            print("# Error applying filter '{{}}' (ID: {{}}) or setting overrides in view '{{}}': {{}}".format(filter_name, filter_id_to_apply, active_view.Name, e_apply))
    elif existing_filter_id == ElementId.InvalidElementId:
         # This path means filter creation failed and no existing one was found
         print("# Filter was not created and could not be applied.")

# Final status message
if filter_id_to_apply == ElementId.InvalidElementId and existing_filter_id == ElementId.InvalidElementId:
    print("# Failed to create or find the filter '{{}}'.".format(filter_name))
elif filter_id_to_apply != ElementId.InvalidElementId:
    print("# Script finished. Filter '{{}}' should be configured and applied to view '{{}}'.".format(filter_name, active_view.Name))