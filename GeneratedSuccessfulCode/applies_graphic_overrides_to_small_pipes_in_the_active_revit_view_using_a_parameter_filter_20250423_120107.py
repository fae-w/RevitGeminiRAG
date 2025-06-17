# Purpose: This script applies graphic overrides to small pipes in the active Revit view using a parameter filter.

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
    OverrideGraphicSettings,
    Color,
    LinePatternElement,
    View,
    UnitUtils,
    ForgeTypeId, # Use ForgeTypeId for units (Revit 2021+)
    UnitTypeId # Required for UnitUtils in Revit 2021+
)
from System.Collections.Generic import List
from System import Double # Explicitly import Double for rule creation value

# --- Configuration ---
filter_name = "Small Pipes Dashed"
target_category_bic = BuiltInCategory.OST_PipeCurves
param_pipe_diameter_bip = BuiltInParameter.RBS_PIPE_DIAMETER_PARAM
threshold_mm = 50.0
override_color = Color(255, 0, 255) # Magenta
override_line_weight = 2
override_line_pattern_name = "Dash" # Case-sensitive name of the line pattern

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
    threshold_internal_units = -1.0 # Default to indicate failure
    try:
        # Revit 2021+ Unit API
        threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
    except AttributeError:
        # Older Revit Unit API
        from Autodesk.Revit.DB import DisplayUnitType
        try:
            threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
        except Exception as e_unit_old:
            print("# Error converting threshold value {}mm to internal units using older API: {}".format(threshold_mm, e_unit_old))
    except Exception as e_unit:
        print("# Error converting threshold value {}mm to internal units: {}".format(threshold_mm, e_unit))

    if threshold_internal_units >= 0:
        # --- Define Categories List for ParameterFilterElement ---
        category_ids = List[ElementId]()
        target_category_id = ElementId(target_category_bic)
        if target_category_id == ElementId.InvalidElementId:
            print("# Error: Could not find ElementId for BuiltInCategory: {}".format(target_category_bic))
            valid_categories = False
        else:
            category_ids.Add(target_category_id)
            valid_categories = True

        if valid_categories:
            # --- Find Line Pattern Element ---
            line_pattern_id = ElementId.InvalidElementId
            collector_patterns = FilteredElementCollector(doc).OfClass(LinePatternElement)
            for pattern in collector_patterns:
                if pattern.Name == override_line_pattern_name:
                    line_pattern_id = pattern.Id
                    break

            if line_pattern_id == ElementId.InvalidElementId:
                print("# Error: Line pattern named '{}' not found in the document.".format(override_line_pattern_name))
            else:
                # --- Define Override Settings ---
                ogs = OverrideGraphicSettings()
                # Assumption: 'Centerline' corresponds to Projection Lines for pipes
                ogs.SetProjectionLineColor(override_color)
                ogs.SetProjectionLineWeight(override_line_weight)
                ogs.SetProjectionLinePatternId(line_pattern_id)
                # Optional: Uncomment to also apply to cut lines if needed
                # ogs.SetCutLineColor(override_color)
                # ogs.SetCutLineWeight(override_line_weight)
                # ogs.SetCutLinePatternId(line_pattern_id)

                # --- Get Parameter ElementId ---
                param_pipe_diameter_id = ElementId(param_pipe_diameter_bip)
                if param_pipe_diameter_id == ElementId.InvalidElementId:
                    print("# Error: Could not find ElementId for BuiltInParameter: {}".format(param_pipe_diameter_bip))
                else:
                    try:
                        # --- Create Filter Rule ---
                        # Rule: Diameter < threshold
                        rule = ParameterFilterRuleFactory.CreateLessRule(param_pipe_diameter_id, Double(threshold_internal_units))

                        if not rule:
                            print("# Error: Failed to create filter rule.")
                        else:
                            # --- Wrap Rule in ElementParameterFilter ---
                            rules_list = List[FilterRule]()
                            rules_list.Add(rule)
                            element_filter = ElementParameterFilter(rules_list)

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
                            else:
                                # --- Create the Parameter Filter Element ---
                                try:
                                    new_filter = ParameterFilterElement.Create(doc, filter_name, category_ids, element_filter)
                                    filter_id_to_apply = new_filter.Id
                                    print("# Created new filter: '{}'".format(filter_name))
                                except Exception as e_create:
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
                                    applied_filters = active_view.GetFilters()
                                    if filter_id_to_apply not in applied_filters:
                                        active_view.AddFilter(filter_id_to_apply)
                                        print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                                    else:
                                        print("# Filter '{}' was already present in view '{}'.".format(filter_name, active_view.Name))

                                    active_view.SetFilterOverrides(filter_id_to_apply, ogs)
                                    active_view.SetFilterVisibility(filter_id_to_apply, True)
                                    print("# Applied graphic overrides for filter '{}' in view '{}'.".format(filter_name, active_view.Name))
                                except Exception as e_apply:
                                    test_filter = doc.GetElement(filter_id_to_apply)
                                    if not test_filter:
                                        print("# Error: Filter ID {} became invalid before applying to view '{}'. Filter may have been deleted.".format(filter_id_to_apply, active_view.Name))
                                    else:
                                        print("# Error applying filter '{}' (ID: {}) or setting overrides in view '{}': {}".format(filter_name, filter_id_to_apply, active_view.Name, e_apply))
                            elif existing_filter_id == ElementId.InvalidElementId:
                                print("# Filter was not created and could not be applied.")

                    except Exception as e_filter_logic:
                        print("# Error creating filter logic (rule or element filter): {}".format(e_filter_logic))

        else:
             print("# Filter creation skipped due to invalid categories.")
    else:
        print("# Filter creation skipped due to threshold conversion error.")