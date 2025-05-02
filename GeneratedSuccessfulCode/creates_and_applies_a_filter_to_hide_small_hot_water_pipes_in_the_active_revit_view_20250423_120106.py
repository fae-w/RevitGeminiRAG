# Purpose: This script creates and applies a filter to hide small hot water pipes in the active Revit view.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
clr.AddReference('System.Collections')

# Import necessary Revit API namespaces
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    BuiltInParameter,
    ParameterFilterRuleFactory,
    FilterRule,
    ElementParameterFilter,
    OverrideGraphicSettings,
    View,
    UnitUtils,
    ForgeTypeId, # Use ForgeTypeId for units (Revit 2021+)
    Element
)
# Import PipingSystemType from the correct namespace
from Autodesk.Revit.DB.Plumbing import PipingSystemType

# Import specific .NET types if needed
from System.Collections.Generic import List
from System import Double, Int64

# --- Configuration ---
filter_name = "Small Hot Water Pipes"
target_category_bic = BuiltInCategory.OST_PipeCurves
system_type_name_to_find = "Domestic Hot Water"
param_system_type_bip = BuiltInParameter.RBS_PIPING_SYSTEM_TYPE_PARAM
param_pipe_diameter_bip = BuiltInParameter.RBS_PIPE_DIAMETER_PARAM
threshold_mm = 20.0
# Override: Visibility Off is handled by SetFilterVisibility

# --- Get Active View ---
# Assume 'doc' is pre-defined
active_view = doc.ActiveView

if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View):
    print("# Error: Active document context is not a View.")
elif not active_view.AreGraphicsOverridesAllowed():
    print("# Error: Filters and overrides are not allowed in the current view type: {}".format(active_view.ViewType))
else:
    # --- Find the 'Domestic Hot Water' PipingSystemType ElementId ---
    dhw_system_type_id = ElementId.InvalidElementId
    system_type_collector = FilteredElementCollector(doc).OfClass(PipingSystemType)
    for sys_type in system_type_collector:
        # Case-insensitive comparison might be safer depending on project standards
        if sys_type.Name.lower() == system_type_name_to_find.lower():
            dhw_system_type_id = sys_type.Id
            break

    if dhw_system_type_id == ElementId.InvalidElementId:
        print("# Error: PipingSystemType named '{}' not found.".format(system_type_name_to_find))
    else:
        # --- Convert Threshold Value ---
        threshold_internal_units = -1.0 # Default to indicate failure
        units_converted = False
        # Try Revit 2021+ Unit API first
        try:
            from Autodesk.Revit.DB import UnitTypeId
            millimeters_type_id = UnitTypeId.Millimeters
            threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, millimeters_type_id)
            units_converted = True
            # print("# Debug: Converted threshold using Revit 2021+ API: {} mm -> {}".format(threshold_mm, threshold_internal_units))
        except ImportError:
            # Fallback for Revit versions prior to 2021
            try:
                from Autodesk.Revit.DB import DisplayUnitType
                threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
                units_converted = True
                # print("# Debug: Converted threshold using older API: {} mm -> {}".format(threshold_mm, threshold_internal_units))
            except Exception as e_unit_old:
                print("# Error converting threshold value {}mm to internal units using older API: {}".format(threshold_mm, e_unit_old))
        except Exception as e_unit:
            print("# Error converting threshold value {}mm to internal units: {}".format(threshold_mm, e_unit))

        if units_converted and threshold_internal_units >= 0:
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
                # --- Get Parameter ElementIds ---
                # Use ElementId constructor directly for BuiltInParameters
                param_system_type_id = ElementId(param_system_type_bip)
                param_pipe_diameter_id = ElementId(param_pipe_diameter_bip)

                if param_system_type_id == ElementId.InvalidElementId or param_pipe_diameter_id == ElementId.InvalidElementId:
                     print("# Error: Could not find ElementId for one or more BuiltInParameters (System Type: {}, Diameter: {})".format(param_system_type_id, param_pipe_diameter_id))
                else:
                    try:
                        # --- Create Filter Rules ---
                        # Rule 1: System Type == 'Domestic Hot Water' (using its ElementId)
                        rule_system_type = ParameterFilterRuleFactory.CreateEqualsRule(param_system_type_id, dhw_system_type_id)

                        # Rule 2: Diameter < threshold
                        # Explicitly cast to Double for safety, though IronPython might handle it
                        rule_diameter = ParameterFilterRuleFactory.CreateLessRule(param_pipe_diameter_id, Double(threshold_internal_units))

                        if not rule_system_type or not rule_diameter:
                             print("# Error: Failed to create one or more filter rules.")
                        else:
                             # --- Combine Rules with AND ---
                             rules_list = List[FilterRule]()
                             rules_list.Add(rule_system_type)
                             rules_list.Add(rule_diameter)
                             # ElementParameterFilter constructor takes the list of rules directly (implicit AND)
                             element_filter = ElementParameterFilter(rules_list)

                             # --- Check if Filter Already Exists ---
                             existing_filter = None
                             collector_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                             for pfe in collector_filters:
                                 if pfe.Name == filter_name:
                                     existing_filter = pfe
                                     print("# Filter named '{}' already exists. Using existing filter.".format(filter_name))
                                     break

                             filter_to_apply = None

                             if existing_filter:
                                 # Optionally: Check if existing filter settings match desired settings (categories, rules)
                                 # For simplicity here, we just use the existing one if found by name.
                                 filter_to_apply = existing_filter
                             else:
                                 # --- Create the Parameter Filter Element ---
                                 # Note: Transaction handling is assumed to be external
                                 try:
                                     new_filter = ParameterFilterElement.Create(doc, filter_name, category_ids, element_filter)
                                     filter_to_apply = new_filter
                                     print("# Created new filter: '{}'".format(filter_name))
                                 except Exception as e_create:
                                     # Handle potential race condition or pre-existing filter missed by collector
                                     if "name is already in use" in str(e_create).lower():
                                         print("# Warning: Filter creation failed for duplicate name '{}', attempting to find existing again.".format(filter_name))
                                         collector_retry = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                                         for pfe_retry in collector_retry:
                                             if pfe_retry.Name == filter_name:
                                                 filter_to_apply = pfe_retry
                                                 break
                                         if filter_to_apply:
                                             print("# Found existing filter with duplicate name: '{}'".format(filter_name))
                                         else:
                                             print("# Error: Filter creation failed for duplicate name '{}', and could not find existing filter.".format(filter_name))
                                     else:
                                         print("# Error creating ParameterFilterElement '{}': {}".format(filter_name, e_create))

                             # --- Apply Filter to Active View ---
                             if filter_to_apply and filter_to_apply.Id != ElementId.InvalidElementId:
                                 filter_id_to_apply = filter_to_apply.Id
                                 try:
                                     # Note: Transaction handling is assumed to be external
                                     applied_filters = active_view.GetFilters()
                                     if filter_id_to_apply not in applied_filters:
                                         active_view.AddFilter(filter_id_to_apply)
                                         print("# Added filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                                     else:
                                         print("# Filter '{}' was already present in view '{}'.".format(filter_name, active_view.Name))

                                     # Set Visibility Off
                                     active_view.SetFilterVisibility(filter_id_to_apply, False)
                                     print("# Set visibility to OFF for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

                                     # Ensure overrides are set, even if just visibility (can prevent stale overrides)
                                     ogs = OverrideGraphicSettings() # Start with empty/default overrides
                                     # Visibility is handled by SetFilterVisibility, so OGS remains default unless other overrides needed.
                                     active_view.SetFilterOverrides(filter_id_to_apply, ogs)
                                     # print("# Applied default graphic overrides for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

                                 except Exception as e_apply:
                                     # Check if the filter element still exists before blaming application logic
                                     test_filter = doc.GetElement(filter_id_to_apply)
                                     if not test_filter:
                                         print("# Error: Filter ID {} became invalid before applying to view '{}'. Filter may have been deleted.".format(filter_id_to_apply, active_view.Name))
                                     else:
                                         print("# Error applying filter '{}' (ID: {}) or setting overrides/visibility in view '{}': {}".format(filter_name, filter_id_to_apply, active_view.Name, e_apply))
                             elif not existing_filter: # Only print error if we didn't find an existing one either
                                 print("# Filter was not created and could not be applied.")

                    except Exception as e_filter_logic:
                        print("# Error during filter logic (rule creation or combination): {}".format(e_filter_logic))

            else:
                print("# Filter creation skipped due to invalid categories.")
        elif not units_converted:
             print("# Filter creation skipped due to threshold conversion error (API specific).")
        else: # units_converted but threshold_internal_units < 0
             print("# Filter creation skipped due to negative internal unit threshold (conversion likely failed).")

# --- Final Output ---
# No data export requested, only actions within Revit.
# Status messages printed above indicate success or failure points.