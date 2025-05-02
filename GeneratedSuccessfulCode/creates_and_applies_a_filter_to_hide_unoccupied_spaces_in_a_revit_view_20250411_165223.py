# Purpose: This script creates and applies a filter to hide unoccupied spaces in a Revit view.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('System.Collections')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Keep if potentially needed downstream, though not strictly required here

# Use explicit import for DB namespace
import Autodesk.Revit.DB as DB

from System.Collections.Generic import List
# Removed specific imports that are now accessed via DB.*

# --- Configuration ---
filter_name = "Unused Spaces"
target_bic = DB.BuiltInCategory.OST_MEPSpaces
occupancy_param_name = "Occupancy" # Find parameter by name
unoccupied_value = "Unoccupied" # Case-sensitive
empty_value = "" # Represents an empty string value

# --- Get Space Category and Occupancy Parameter ID ---
parameter_filter = None # Initialize to None
occupancy_param_id = DB.ElementId.InvalidElementId # Use InvalidElementId for initialization
space_category = DB.Category.GetCategory(doc, target_bic)

if space_category is not None:
    # Find the parameter ID using the parameter name "Occupancy"
    # An element instance is needed to look up the parameter reliably
    example_space = DB.FilteredElementCollector(doc).OfCategory(target_bic).WhereElementIsNotElementType().FirstElement()
    if example_space:
        param = example_space.LookupParameter(occupancy_param_name)
        if param:
            occupancy_param_id = param.Id
        else:
            # Fallback: Iterate through parameters if LookupParameter fails (e.g., shared param loaded differently)
            for p in example_space.Parameters:
                if p.Definition.Name == occupancy_param_name:
                    occupancy_param_id = p.Id
                    break

# --- Proceed only if parameter was found ---
if occupancy_param_id != DB.ElementId.InvalidElementId and space_category is not None:
    space_category_id = space_category.Id

    # --- Find or Create Filter Element ---
    collector = DB.FilteredElementCollector(doc).OfClass(DB.ParameterFilterElement)
    existing_filter = None # Initialize specific variable for clarity
    for pf_elem in collector:
        if pf_elem.Name == filter_name:
            existing_filter = pf_elem
            break

    if existing_filter is not None:
         parameter_filter = existing_filter
    else:
        # Define the categories the filter applies to
        categories_for_filter = List[DB.ElementId]()
        categories_for_filter.Add(space_category_id)

        # Create filter rules
        # Rule 1: Occupancy parameter equals empty_value ("")
        # Rule 2: Occupancy parameter equals unoccupied_value ("Unoccupied") - Case Sensitive
        try:
            # Use CreateEqualsRule for case-sensitive string comparison.
            # Note: For truly empty parameters, checking for existence might be needed,
            # but CreateEqualsRule with "" often works for string parameters.
            # Consider ParameterFilterRuleFactory.CreateEqualsRule(paramId, "", False) if case-insensitivity needed for empty string check (usually not)
            rule1 = DB.ParameterFilterRuleFactory.CreateEqualsRule(occupancy_param_id, empty_value, True)
            rule2 = DB.ParameterFilterRuleFactory.CreateEqualsRule(occupancy_param_id, unoccupied_value, True)

            # Create ElementParameterFilter instances from each rule
            element_filter1 = DB.ElementParameterFilter(rule1)
            element_filter2 = DB.ElementParameterFilter(rule2)

            # Combine the filters with a LogicalOrFilter
            filters_list = List[DB.ElementFilter]()
            filters_list.Add(element_filter1)
            filters_list.Add(element_filter2)
            combined_filter = DB.LogicalOrFilter(filters_list)

            # Create the ParameterFilterElement (Transaction managed externally)
            parameter_filter = DB.ParameterFilterElement.Create(
                doc,
                filter_name,
                categories_for_filter,
                combined_filter
            )
        except Exception as create_ex:
            # Silently fail creation (no print)
            parameter_filter = None # Ensure filter_element is None if creation failed

    # --- Apply Filter to Active View ---
    if parameter_filter is not None:
        filter_id = parameter_filter.Id
        active_view = doc.ActiveView

        # Check if active_view is valid and supports overrides
        if active_view is not None and active_view.IsValidObject and active_view.AreGraphicsOverridesAllowed():
             # Check if the filter can be applied (category must be visible in view etc.)
            if active_view.IsFilterApplicable(filter_id):
                try:
                    # Check if the filter is already added to the view
                    applied_filter_ids = active_view.GetFilters()
                    if filter_id not in applied_filter_ids:
                        # Add the filter to the view (Transaction managed externally)
                        active_view.AddFilter(filter_id)

                    # Define the graphic overrides (set visibility to False)
                    override_settings = DB.OverrideGraphicSettings()
                    # Use SetVisible instead of SetVisibility (older API?) - check API doc if issue persists
                    override_settings.SetHalftone(False) # Ensure not just halftone
                    override_settings.SetSurfaceTransparency(0) # Ensure not just transparent
                    override_settings.SetDetailLevel(active_view.DetailLevel) # Maintain detail level
                    # Ensure other overrides are not unintentionally set, start clean
                    # Correct method to hide: Set visibility to False
                    override_settings.SetVisible(False)


                    # Apply the overrides to the filter in the view (Transaction managed externally)
                    active_view.SetFilterOverrides(filter_id, override_settings)

                except Exception as view_ex:
                    # Silently fail if view application fails (no print)
                    pass
            # else: # Filter not applicable
                # pass # Silently ignore
        # else: # View invalid or doesn't support overrides
            # pass # Silently ignore

# Implicitly do nothing if category/parameter not found or filter creation/application fails.