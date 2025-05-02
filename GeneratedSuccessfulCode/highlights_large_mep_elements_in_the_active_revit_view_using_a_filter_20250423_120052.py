# Purpose: This script highlights large MEP elements in the active Revit view using a filter.

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
    FilterRule, # Base class for rule list
    ElementParameterFilter,
    LogicalOrFilter,
    LogicalAndFilter,
    ElementCategoryFilter,
    OverrideGraphicSettings,
    Color,
    View,
    UnitUtils,
    ForgeTypeId, # Use ForgeTypeId for units (Revit 2021+)
    UnitTypeId # Required for UnitUtils in Revit 2021+
)
from System.Collections.Generic import List
from System import Double # Explicitly import Double for rule creation value

# --- Configuration ---
filter_name = "Large MEP Elements"
categories_to_include = [
    BuiltInCategory.OST_DuctCurves,
    BuiltInCategory.OST_PipeCurves,
    BuiltInCategory.OST_CableTray
]
# Parameters for size checks
param_duct_width_bip = BuiltInParameter.RBS_CURVE_WIDTH_PARAM
param_duct_diameter_bip = BuiltInParameter.RBS_CURVE_DIAMETER_PARAM
param_pipe_diameter_bip = BuiltInParameter.RBS_PIPE_DIAMETER_PARAM
param_ct_width_bip = BuiltInParameter.RBS_CABLETRAY_WIDTH_PARAM

threshold_mm = 500.0
override_color = Color(255, 0, 0) # Red lines for highlighting

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View):
    print("# Error: Active document context is not a View.")
elif not active_view.AreGraphicsOverridesAllowed():
    print("# Error: Filters and overrides are not allowed in the current view type: {}".format(active_view.ViewType))
else:
    # --- Convert Threshold Value ---
    try:
        threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
    except AttributeError:
        from Autodesk.Revit.DB import DisplayUnitType
        try:
            threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
        except Exception as e_unit_old:
             print("# Error converting threshold value {}mm to internal units using older API: {}".format(threshold_mm, e_unit_old))
             threshold_internal_units = -1 # Indicate failure
    except Exception as e_unit:
        print("# Error converting threshold value {}mm to internal units: {}".format(threshold_mm, e_unit))
        threshold_internal_units = -1 # Indicate failure

    if threshold_internal_units >= 0:
        # --- Define Categories List for ParameterFilterElement ---
        category_ids = List[ElementId]()
        valid_categories = True
        for bic in categories_to_include:
            cat_id = ElementId(bic)
            if cat_id == ElementId.InvalidElementId:
                print("# Error: Could not find ElementId for BuiltInCategory: {}".format(bic))
                valid_categories = False
                break
            category_ids.Add(cat_id)

        if valid_categories:
            # --- Define Override Settings ---
            ogs = OverrideGraphicSettings()
            ogs.SetProjectionLineColor(override_color)
            ogs.SetCutLineColor(override_color) # Apply to cut lines as well

            # --- Get Parameter ElementIds ---
            param_duct_width_id = ElementId(param_duct_width_bip)
            param_duct_diameter_id = ElementId(param_duct_diameter_bip)
            param_pipe_diameter_id = ElementId(param_pipe_diameter_bip)
            param_ct_width_id = ElementId(param_ct_width_bip)

            # Check if parameter IDs are valid
            if ElementId.InvalidElementId in [param_duct_width_id, param_duct_diameter_id, param_pipe_diameter_id, param_ct_width_id]:
                 print("# Error: One or more BuiltInParameter IDs could not be resolved.")
                 print("# Duct Width: {}, Duct Diameter: {}, Pipe Diameter: {}, Cable Tray Width: {}".format(param_duct_width_id, param_duct_diameter_id, param_pipe_diameter_id, param_ct_width_id))
            else:
                try:
                    # --- Create Filter Rules ---
                    rule_duct_width = ParameterFilterRuleFactory.CreateGreaterRule(param_duct_width_id, Double(threshold_internal_units))
                    rule_duct_diameter = ParameterFilterRuleFactory.CreateGreaterRule(param_duct_diameter_id, Double(threshold_internal_units))
                    rule_pipe_diameter = ParameterFilterRuleFactory.CreateGreaterRule(param_pipe_diameter_id, Double(threshold_internal_units))
                    rule_ct_width = ParameterFilterRuleFactory.CreateGreaterRule(param_ct_width_id, Double(threshold_internal_units))

                    # --- Create ElementParameterFilters from Rules ---
                    filter_duct_width = ElementParameterFilter(List[FilterRule]([rule_duct_width]))
                    filter_duct_diameter = ElementParameterFilter(List[FilterRule]([rule_duct_diameter]))
                    filter_pipe_diameter = ElementParameterFilter(List[FilterRule]([rule_pipe_diameter]))
                    filter_ct_width = ElementParameterFilter(List[FilterRule]([rule_ct_width]))

                    # --- Combine Duct Width and Diameter rules ---
                    filter_duct_size = LogicalOrFilter(filter_duct_width, filter_duct_diameter)

                    # --- Create Category Filters ---
                    cat_filter_ducts = ElementCategoryFilter(BuiltInCategory.OST_DuctCurves)
                    cat_filter_pipes = ElementCategoryFilter(BuiltInCategory.OST_PipeCurves)
                    cat_filter_cabletrays = ElementCategoryFilter(BuiltInCategory.OST_CableTray)

                    # --- Combine Category and Size Filters using AND ---
                    filter_duct_final = LogicalAndFilter(cat_filter_ducts, filter_duct_size)
                    filter_pipe_final = LogicalAndFilter(cat_filter_pipes, filter_pipe_diameter)
                    filter_ct_final = LogicalAndFilter(cat_filter_cabletrays, filter_ct_width)

                    # --- Combine the Category-Specific Filters using OR ---
                    filter_duct_or_pipe = LogicalOrFilter(filter_duct_final, filter_pipe_final)
                    combined_element_filter = LogicalOrFilter(filter_duct_or_pipe, filter_ct_final)

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
                        # Assumption: If the filter exists, we use it as-is.
                        # Updating an existing filter's rules/categories/elementfilter is complex and not done here.
                    else:
                        # --- Create the Parameter Filter Element ---
                        try:
                            # Pass the combined filter and the list of all relevant categories
                            new_filter = ParameterFilterElement.Create(doc, filter_name, category_ids, combined_element_filter)
                            filter_id_to_apply = new_filter.Id
                            print("# Created new filter: '{}'".format(filter_name))
                        except Exception as e_create:
                            # Handle potential duplicate name error more gracefully
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

                            # Apply the overrides
                            active_view.SetFilterOverrides(filter_id_to_apply, ogs)

                            # Ensure the filter is enabled (visible)
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

                except Exception as e_filter_logic:
                    print("# Error creating filter logic (rules or combined filters): {}".format(e_filter_logic))

        else:
            print("# Filter creation skipped due to invalid categories.")
    else:
        print("# Filter creation skipped due to threshold conversion error.")