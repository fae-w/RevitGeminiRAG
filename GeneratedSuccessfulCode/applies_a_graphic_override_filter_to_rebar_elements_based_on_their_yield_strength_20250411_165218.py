# Purpose: This script applies a graphic override filter to rebar elements based on their yield strength.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, ParameterFilterRuleFactory,
    OverrideGraphicSettings, Color, View, Element, SharedParameterElement,
    StorageType, ParameterElement
)
# Import necessary .NET classes
from System.Collections.Generic import List

# --- Configuration ---
filter_name = "Rebar - High Strength"
target_category_id = ElementId(BuiltInCategory.OST_Rebar)
# IMPORTANT ASSUMPTION: Assumes a numeric parameter named 'Yield Strength (MPa)' exists
# for Rebar elements (either instance or type parameter).
# This parameter must store the strength value directly in MPa as a number (Double or Integer).
# If the parameter name or units are different, update 'parameter_name' and 'strength_threshold_mpa'.
parameter_name = "Yield Strength (MPa)"
strength_threshold_mpa = 460.0 # The value to compare against (must be float/double)
override_color = Color(128, 0, 128) # Purple

# --- Function to Find Parameter ID ---
def find_numeric_parameter_id_by_name(doc, category_id, param_name):
    """
    Tries to find a numeric (Double/Integer) parameter ID by name,
    checking instance and type parameters of a sample element.
    Falls back to checking ParameterElements (less reliable binding check).
    Returns ElementId or None.
    """
    param_elem_id = None
    # Check a sample element of the category
    sample_element = FilteredElementCollector(doc).OfCategoryId(category_id).WhereElementIsNotElementType().FirstElement()

    if sample_element:
        # Check instance parameters
        for param in sample_element.GetOrderedParameters():
            if param.Definition.Name == param_name:
                 if param.StorageType == StorageType.Double or param.StorageType == StorageType.Integer:
                    return param.Id # Found numeric instance parameter
        # Check type parameters
        elem_type = doc.GetElement(sample_element.GetTypeId())
        if elem_type:
            for param in elem_type.GetOrderedParameters():
                 if param.Definition.Name == param_name:
                     if param.StorageType == StorageType.Double or param.StorageType == StorageType.Integer:
                        return param.Id # Found numeric type parameter

    # Fallback: Iterate through all ParameterElements if not found on sample
    # This is less reliable as it doesn't guarantee the param applies to the target category
    param_collector = FilteredElementCollector(doc).OfClass(ParameterElement)
    for p_elem in param_collector:
        # Check if parameter element itself has the name
        if p_elem.Name == param_name: # Check Name property of ParameterElement
            # Get the actual ParameterDefinition (might be internal or shared)
            try:
                 # InternalDefinition check might be needed for project params
                 internal_def = p_elem.GetDefinition()
                 if internal_def and internal_def.Name == param_name:
                     # Simplistic check: Assume it's numeric - further checks needed in reality
                     # e.g. internal_def.ParameterType or GetDataType()
                     return p_elem.Id
            except: # Handles cases like SharedParameterElement
                pass
        # Check if it's a SharedParameterElement with the matching name
        if isinstance(p_elem, SharedParameterElement):
             shared_def = p_elem.GetDefinition()
             if shared_def and shared_def.Name == param_name:
                 # Assume numeric - further checks needed for robustness
                  # e.g. shared_def.ParameterType or GetDataType()
                 return p_elem.Id

    # If parameter not found after checks
    return None

# --- Main Script Logic ---
parameter_id = find_numeric_parameter_id_by_name(doc, target_category_id, parameter_name)

if not parameter_id:
    print("# Error: Could not find a numeric parameter named '{}' applicable to Rebar.".format(parameter_name))
    print("# Please ensure a project or shared parameter with this exact name and numeric type (Double/Integer) exists and is applied to the Rebar category.")
else:
    # Get the active view
    active_view = doc.ActiveView

    # Check if active_view is valid and not a template
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
        print("# Error: No active graphical view found or active view is a template.")
    else:
        # Define categories for the filter
        categories = List[ElementId]()
        categories.Add(target_category_id)

        # Define filter rule: Parameter > Threshold
        # NOTE: Assumes the parameter stores the value directly in MPa.
        # If it stores in Revit's internal units (e.g., ksi or Pa), conversion is needed here.
        # ParameterFilterRuleFactory.CreateGreaterRule requires ElementId, value (double), tolerance (double)
        epsilon = 0.00001 # Small tolerance for floating point comparison
        try:
             # Ensure threshold is a float for the rule factory
             rule = ParameterFilterRuleFactory.CreateGreaterRule(parameter_id, float(strength_threshold_mpa), epsilon)

             # Wrap the rule(s) in an ElementParameterFilter
             filter_rules_list = List[FilterRule]()
             filter_rules_list.Add(rule)
             element_filter = ElementParameterFilter(filter_rules_list)

             # Check if a filter with the same name already exists
             existing_filter = None
             filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
             for f in filter_collector:
                 if f.Name == filter_name:
                     existing_filter = f
                     break

             parameter_filter = None
             if existing_filter:
                  parameter_filter = existing_filter
                  # Update existing filter's definition (optional, safer to just use it)
                  # existing_filter.SetCategories(categories)
                  # existing_filter.SetElementFilter(element_filter)
                  # print("# Using and potentially updating existing filter: '{}'".format(filter_name))
             else:
                 # Create the Parameter Filter Element if it doesn't exist
                 try:
                     parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                     # print("# Created new filter: '{}'".format(filter_name))
                 except Exception as create_ex:
                     # Check if creation failed because it exists (race condition?)
                     current_filter = next((f for f in FilteredElementCollector(doc).OfClass(ParameterFilterElement) if f.Name == filter_name), None)
                     if current_filter:
                         parameter_filter = current_filter
                         # print("# Filter '{}' found after creation attempt failed. Using existing.".format(filter_name))
                     else:
                         print("# Error creating filter '{}': {}. Filter could not be created or found.".format(filter_name, create_ex))


             if parameter_filter:
                 # Define Override Graphic Settings
                 override_settings = OverrideGraphicSettings()
                 override_settings.SetProjectionLineColor(override_color)
                 override_settings.SetCutLineColor(override_color)
                 # Optional: Set surface/cut patterns solid/colored if desired
                 # fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
                 # solid_fill_id = None
                 # for fp in fill_pattern_collector:
                 #     if fp.GetFillPattern().IsSolidFill:
                 #         solid_fill_id = fp.Id
                 #         break
                 # if solid_fill_id:
                 #     override_settings.SetSurfaceForegroundPatternId(solid_fill_id)
                 #     override_settings.SetSurfaceForegroundPatternColor(override_color)
                 #     override_settings.SetCutForegroundPatternId(solid_fill_id)
                 #     override_settings.SetCutForegroundPatternColor(override_color)


                 # Apply the filter to the active view
                 try:
                     # Check if filter is already applied before adding
                     applied_filters = active_view.GetFilters()
                     if parameter_filter.Id not in applied_filters:
                          active_view.AddFilter(parameter_filter.Id)
                          # print("# Added filter '{}' to the view.".format(filter_name))

                     # Set the overrides for the filter in the view
                     active_view.SetFilterOverrides(parameter_filter.Id, override_settings)
                     # print("# Successfully applied filter '{}' with overrides to active view.".format(filter_name))
                 except Exception as apply_ex:
                     print("# Error applying filter or overrides to the view: {}".format(apply_ex))

             # This condition now only triggers if creation failed AND filter didn't exist before/after attempt
             elif not existing_filter:
                  pass # Error already printed during creation attempt

        except Exception as rule_ex:
             print("# Error creating filter rule for parameter '{}' (ID: {}): {}".format(parameter_name, parameter_id, rule_ex))
             print("# Check if the parameter type is correctly identified as numeric and the threshold value is valid.")