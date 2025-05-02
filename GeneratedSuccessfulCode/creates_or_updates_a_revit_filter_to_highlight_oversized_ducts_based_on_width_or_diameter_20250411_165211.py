# Purpose: This script creates or updates a Revit filter to highlight oversized ducts based on width or diameter.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String etc.
clr.AddReference('System.Collections') # Required for List<T>

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    BuiltInParameter,
    ParameterFilterRuleFactory,
    FilterRule, # Base class for rule list
    ElementParameterFilter,
    LogicalOrFilter, # Needed for OR condition between Width and Diameter
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
filter_name = "Oversized Ducts" # Single filter name
target_category_bic = BuiltInCategory.OST_DuctCurves
# Correct BuiltInParameter enumerations for Duct Width and Diameter
param_width_bip = BuiltInParameter.RBS_CURVE_WIDTH_PARAM
param_diameter_bip = BuiltInParameter.RBS_CURVE_DIAMETER_PARAM
threshold_mm = 1000.0
override_color = Color(255, 0, 0) # Red

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are available from the execution context
active_view = doc.ActiveView
if not active_view:
    raise ValueError("No active view found. Cannot apply filter overrides.")
if not isinstance(active_view, View):
     raise TypeError("Active document context is not a View.")
# Check if view supports filters (avoids errors on schedules, etc.)
if not active_view.AreGraphicsOverridesAllowed():
     raise TypeError("Filters and overrides are not allowed in the current view type: {}".format(active_view.ViewType))

# --- Convert Threshold Value ---
try:
    # Use ForgeTypeId (Revit 2021+ API) for unit conversion
    threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
except AttributeError:
    # Fallback for older Revit versions using DisplayUnitType
    from Autodesk.Revit.DB import DisplayUnitType
    try:
        threshold_internal_units = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
    except Exception as e_unit_old:
         raise RuntimeError("Failed to convert threshold value {}mm to internal units using older API. Error: {}".format(threshold_mm, e_unit_old))
except Exception as e_unit:
    raise RuntimeError("Failed to convert threshold value {}mm to internal units. Error: {}".format(threshold_mm, e_unit))

# --- Define Categories ---
categories = List[ElementId]()
target_category_id = ElementId(target_category_bic)
if target_category_id == ElementId.InvalidElementId:
    raise ValueError("Could not find ElementId for BuiltInCategory: {}".format(target_category_bic))
categories.Add(target_category_id)

# --- Define Override Settings ---
ogs = OverrideGraphicSettings()
# Set projection lines (visible when not cut)
ogs.SetProjectionLineColor(override_color)
# Set cut lines to the same color for consistency if elements are cut
ogs.SetCutLineColor(override_color)
# Optional: Set patterns if desired
# from Autodesk.Revit.DB import FillPatternElement # Needs import if used
# ogs.SetSurfaceForegroundPatternVisible(True)
# ogs.SetSurfaceForegroundPatternColor(override_color)
# solid_fill_pattern_id = FillPatternElement.GetSolidFillPatternId(doc)
# if solid_fill_pattern_id != ElementId.InvalidElementId:
#    ogs.SetSurfaceForegroundPatternId(solid_fill_pattern_id)

# --- Helper function to create or get filter and apply to view ---
def create_or_get_filter_and_apply(doc, view, filter_name, categories, param_width_bip, param_diameter_bip, threshold_value, override_settings):
    """Creates or gets a filter by name (Width > X OR Diameter > X), applies it to the view with overrides."""
    existing_filter_id = ElementId.InvalidElementId
    collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    for pfe in collector:
        if pfe.Name == filter_name:
            existing_filter_id = pfe.Id
            # Optional: Update existing filter rules/categories if needed.
            # Requires careful handling of LogicalOrFilter structure.
            # For simplicity, we'll use the existing one as is or create a new one.
            # print("Found existing filter: {}".format(filter_name)) # Debug
            break

    filter_id_to_apply = ElementId.InvalidElementId

    if existing_filter_id != ElementId.InvalidElementId:
        filter_id_to_apply = existing_filter_id
        # print("Using existing filter: {}".format(filter_name)) # Debug
    else:
        # --- Create Filter Rules ---
        param_width_id = ElementId(param_width_bip)
        param_diameter_id = ElementId(param_diameter_bip)

        if param_width_id == ElementId.InvalidElementId:
             raise ValueError("Could not find ElementId for Width BuiltInParameter: {}".format(param_width_bip))
        if param_diameter_id == ElementId.InvalidElementId:
             raise ValueError("Could not find ElementId for Diameter BuiltInParameter: {}".format(param_diameter_bip))

        # Create the rules: Parameter > threshold_value
        try:
            width_rule = ParameterFilterRuleFactory.CreateGreaterRule(param_width_id, Double(threshold_value))
            diameter_rule = ParameterFilterRuleFactory.CreateGreaterRule(param_diameter_id, Double(threshold_value))
        except Exception as e_rule:
            raise RuntimeError("Failed to create filter rule for parameters Width/Diameter and value {}. Error: {}".format(threshold_value, e_rule))

        if not width_rule or not diameter_rule:
            raise RuntimeError("Filter rule creation returned None.")

        # --- Create Element Filters for each rule (needed for LogicalOrFilter) ---
        width_rules_list = List[FilterRule]()
        width_rules_list.Add(width_rule)
        width_element_filter = ElementParameterFilter(width_rules_list)

        diameter_rules_list = List[FilterRule]()
        diameter_rules_list.Add(diameter_rule)
        diameter_element_filter = ElementParameterFilter(diameter_rules_list)

        # --- Combine rules with Logical OR ---
        # LogicalOrFilter combines two ElementFilter objects
        combined_or_filter = LogicalOrFilter(width_element_filter, diameter_element_filter)

        # --- Create the Parameter Filter Element ---
        try:
            # ParameterFilterElement.Create takes the combined ElementFilter
            new_filter = ParameterFilterElement.Create(doc, filter_name, categories, combined_or_filter)
            filter_id_to_apply = new_filter.Id
            # print("Created new filter: {}".format(filter_name)) # Debug
        except Exception as e_create:
             # Handle potential race condition or pre-existing filter not found initially
            if "name is already in use" in str(e_create).lower():
                 collector_retry = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                 for pfe_retry in collector_retry:
                     if pfe_retry.Name == filter_name:
                         filter_id_to_apply = pfe_retry.Id
                         break
                 if filter_id_to_apply == ElementId.InvalidElementId:
                     raise RuntimeError("Filter creation failed for duplicate name '{}', but could not find existing filter on retry.".format(filter_name))
                 # print("Using existing filter found after creation attempt: {}".format(filter_name)) # Debug
            else:
                 raise RuntimeError("Failed to create ParameterFilterElement '{}'. Error: {}".format(filter_name, e_create))

    # --- Apply Filter to Active View ---
    if filter_id_to_apply != ElementId.InvalidElementId:
        try:
            applied_filters = view.GetFilters()
            if filter_id_to_apply not in applied_filters:
                 view.AddFilter(filter_id_to_apply)

            # Apply the overrides (this will update overrides if filter was already present)
            view.SetFilterOverrides(filter_id_to_apply, override_settings)
            # Ensure filter is visible
            view.SetFilterVisibility(filter_id_to_apply, True)
            # print("Applied filter '{}' to view '{}'.".format(filter_name, view.Name)) # Debug

        except Exception as e_apply:
            # Check if the filter actually exists in the document before blaming apply
            test_filter = doc.GetElement(filter_id_to_apply)
            if not test_filter:
                 raise RuntimeError("Filter ID {} became invalid before applying to view '{}'. Filter may have been deleted.".format(filter_id_to_apply, view.Name))
            else:
                 raise RuntimeError("Failed to apply filter '{}' (ID: {}) or set overrides in view '{}'. Error: {}".format(filter_name, filter_id_to_apply, view.Name, e_apply))
    else:
         raise RuntimeError("Filter ID to apply is invalid for '{}' after creation/check phase.".format(filter_name))

# --- Process the combined filter ---
try:
    create_or_get_filter_and_apply(
        doc,
        active_view,
        filter_name,
        categories,
        param_width_bip,
        param_diameter_bip,
        threshold_internal_units,
        ogs
    )
    # print("Oversized duct filter '{}' processed for view '{}'.".format(filter_name, active_view.Name)) # Debug
except Exception as e:
    # Print a more user-friendly error message if something goes wrong
    import sys
    exception_type, exception_value, exception_traceback = sys.exc_info()
    print("Error processing filter '{}': {} at line {}".format(filter_name, exception_value, exception_traceback.tb_lineno))