# Purpose: This script creates or updates a Revit filter based on a parameter value and applies graphic overrides to elements matching the filter in the active view.

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
    # LogicalAndFilter, # Not needed for a single rule filter
    OverrideGraphicSettings,
    Color,
    View
)
from System.Collections.Generic import List
from System import String # Explicitly import String for rule creation value

# --- Configuration ---
filter_name = "Mechanical Ducts - Supply"
target_category_bic = BuiltInCategory.OST_DuctCurves
param_bip = BuiltInParameter.RBS_SYSTEM_CLASSIFICATION_PARAM
param_value = "Supply Air" # The string value to match
override_color = Color(0, 0, 255) # Blue

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view:
    raise ValueError("No active view found. Cannot apply filter overrides.")
if not isinstance(active_view, View):
     raise TypeError("Active document context is not a View.")
# Check if view supports filters (avoids errors on schedules, etc.)
if not active_view.AreGraphicsOverridesAllowed():
     raise TypeError("Filters and overrides are not allowed in the current view type: {}".format(active_view.ViewType))

# --- Check if Filter Already Exists ---
existing_filter_id = ElementId.InvalidElementId
collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
for pfe in collector:
    # ParameterFilterElement names are case-sensitive
    if pfe.Name == filter_name:
        existing_filter_id = pfe.Id
        break

filter_id_to_apply = ElementId.InvalidElementId

if existing_filter_id != ElementId.InvalidElementId:
    filter_id_to_apply = existing_filter_id
    # If filter exists, we will just apply it to the view (or update its overrides)
else:
    # --- Create Filter Rule ---
    param_id = ElementId(param_bip)
    if param_id == ElementId.InvalidElementId:
         raise ValueError("Could not find ElementId for BuiltInParameter: {}".format(param_bip))

    # Create the rule: System Classification == "Supply Air"
    # ParameterFilterRuleFactory.CreateEqualsRule supports strings.
    # Use System.String for the value argument for robustness.
    try:
        filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(param_id, String(param_value))
    except Exception as e_rule:
        raise RuntimeError("Failed to create filter rule for parameter ID {} and value '{}'. Error: {}".format(param_id, param_value, e_rule))

    if not filter_rule:
        raise RuntimeError("Filter rule creation returned None.")

    # --- Create Element Parameter Filter ---
    # The ElementParameterFilter constructor expects an IList<FilterRule>
    rules = List[FilterRule]()
    rules.Add(filter_rule)

    # Create the ElementParameterFilter using the list of rules.
    # This IS the ElementFilter required by ParameterFilterElement.Create
    element_filter = ElementParameterFilter(rules)


    # --- Define Categories ---
    categories = List[ElementId]()
    target_category_id = ElementId(target_category_bic)
    if target_category_id == ElementId.InvalidElementId:
        raise ValueError("Could not find ElementId for BuiltInCategory: {}".format(target_category_bic))
    categories.Add(target_category_id)

    # --- Create the Parameter Filter Element ---
    # Note: The C# wrapper handles the transaction for element creation.
    try:
        # Pass the ElementParameterFilter directly
        new_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
        filter_id_to_apply = new_filter.Id
    except Exception as e_create:
        # Check if error is due to duplicate name which might occur in race conditions
        # or if check above somehow missed it.
        if "name is already in use" in str(e_create).lower():
             # Re-query to be absolutely sure and get the ID
             collector_retry = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
             for pfe_retry in collector_retry:
                 if pfe_retry.Name == filter_name:
                     filter_id_to_apply = pfe_retry.Id
                     break
             if filter_id_to_apply == ElementId.InvalidElementId:
                 # This indicates a more serious issue if creation failed for duplicate name but query fails too
                 raise RuntimeError("Filter creation failed for duplicate name '{}', but could not find existing filter.".format(filter_name))
        else:
             raise RuntimeError("Failed to create ParameterFilterElement '{}'. Error: {}".format(filter_name, e_create))


# --- Apply Filter to Active View ---
if filter_id_to_apply != ElementId.InvalidElementId:
    # --- Define Override Settings ---
    ogs = OverrideGraphicSettings()
    # Set projection lines (visible when not cut)
    ogs.SetProjectionLineColor(override_color)
    # Set cut lines to the same color for consistency if elements are cut
    ogs.SetCutLineColor(override_color)
    # Optionally ensure lines are visible and not using a pattern that makes them invisible
    # ogs.SetProjectionLinePatternId(ElementId.InvalidElementId) # Use default solid pattern
    # ogs.SetCutLinePatternId(ElementId.InvalidElementId)       # Use default solid pattern

    # Note: The C# wrapper handles the transaction for view modifications.
    try:
        # Check if the filter is already added to the view
        applied_filters = active_view.GetFilters()
        if filter_id_to_apply not in applied_filters:
             active_view.AddFilter(filter_id_to_apply)

        # Apply the overrides (this will update overrides if filter was already present)
        active_view.SetFilterOverrides(filter_id_to_apply, ogs)

        # Set filter visibility in the view (optional, defaults to visible usually)
        # active_view.SetFilterVisibility(filter_id_to_apply, True)

    except Exception as e_apply:
        raise RuntimeError("Failed to apply filter '{}' (ID: {}) or set overrides in view '{}'. Error: {}".format(filter_name, filter_id_to_apply, active_view.Name, e_apply))
else:
     # This path indicates an issue either finding or creating the filter.
     raise RuntimeError("Filter ID to apply is invalid after creation/check phase.")

# Ensure output for any potential caller waiting for a result (optional)
# print("Filter '{}' applied/updated successfully in view '{}'.".format(filter_name, active_view.Name))