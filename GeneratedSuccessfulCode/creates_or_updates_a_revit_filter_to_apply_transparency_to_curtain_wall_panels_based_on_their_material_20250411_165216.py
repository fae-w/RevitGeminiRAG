# Purpose: This script creates or updates a Revit filter to apply transparency to curtain wall panels based on their material.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # For List

from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ParameterFilterElement,
    ElementId,
    ElementParameterFilter,
    FilterRule, # Base class
    ParameterFilterRuleFactory,
    OverrideGraphicSettings,
    View,
    Material,
    BuiltInParameter,
    ElementFilter, # Base class for ElementParameterFilter and LogicalFilter
    LogicalOrFilter,
    PanelType, # Need to collect PanelTypes
    Parameter,
    StorageType
)
import System # For exception handling

# --- Filter Configuration ---
filter_name = "Exterior Glazing"
target_category_id = ElementId(BuiltInCategory.OST_CurtainWallPanels)
target_material_name = "Glass" # Case-sensitive material name
# Assumption: The material of the PanelType is controlled by a type parameter named "Material".
# If your panel types use a different parameter name, update this variable.
type_material_param_name = "Material"
transparency_value = 50 # Percentage (0-100)

# --- Script Core Logic ---

active_view = doc.ActiveView
parameter_filter = None # Initialize variable

# Validate Active View
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
else:
    # 1. Find the 'Glass' Material ElementId
    glass_material_id = ElementId.InvalidElementId
    material_collector = FilteredElementCollector(doc).OfClass(Material)
    for mat in material_collector:
        # Case-insensitive comparison might be safer depending on project standards
        if mat.Name.lower() == target_material_name.lower():
            glass_material_id = mat.Id
            break

    if glass_material_id == ElementId.InvalidElementId:
        print("# Error: Material named '{}' not found in the project.".format(target_material_name))
    else:
        # 2. Find PanelType ElementIds that use the 'Glass' material via the specified parameter
        matching_panel_type_ids = List[ElementId]()
        panel_type_collector = FilteredElementCollector(doc).OfClass(PanelType)
        for panel_type in panel_type_collector:
            if isinstance(panel_type, PanelType):
                try:
                    # Look for the type parameter by name
                    material_param = panel_type.LookupParameter(type_material_param_name)
                    if material_param and material_param.StorageType == StorageType.ElementId:
                        mat_id = material_param.AsElementId()
                        if mat_id == glass_material_id:
                            matching_panel_type_ids.Add(panel_type.Id)
                    # Optional: Add checks for BuiltInParameters if LookupParameter is not reliable
                    # Example: elif panel_type.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)...
                except System.Exception as e:
                    # Silently ignore types that cause errors during parameter lookup
                    # print("# Debug: Error checking material for PanelType {}: {}".format(panel_type.Id, e))
                    pass

        if matching_panel_type_ids.Count == 0:
            print("# Error: No Panel Types found using the '{}' material via the '{}' parameter.".format(target_material_name, type_material_param_name))
        else:
            # 3. Define filter rules based on matching Type IDs
            element_filters = List[ElementFilter]()
            # Parameter representing the Element Type of an instance
            type_param_id = ElementId(BuiltInParameter.ELEM_TYPE_PARAM)

            for type_id in matching_panel_type_ids:
                rule = ParameterFilterRuleFactory.CreateEqualsRule(type_param_id, type_id)
                element_filters.Add(ElementParameterFilter(rule)) # Wrap rule in ElementParameterFilter

            # Combine rules with OR logic if multiple types match
            final_element_filter = None
            if element_filters.Count == 1:
                final_element_filter = element_filters[0]
            elif element_filters.Count > 1:
                final_element_filter = LogicalOrFilter(element_filters)
            # If count is 0, final_element_filter remains None (handled by the check above)

            if final_element_filter:
                 # 4. Define categories for the filter
                categories = List[ElementId]()
                categories.Add(target_category_id)

                # 5. Check if a filter with the same name already exists
                existing_filter = None
                filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                for f in filter_collector:
                    if f.Name == filter_name:
                        existing_filter = f
                        break

                if existing_filter:
                    parameter_filter = existing_filter
                    # print("# Using existing filter: '{}'".format(filter_name)) # Optional Debug
                    # Note: This script does not update the rules/categories of an existing filter.
                    # If update is needed, uncomment and adapt the following (requires external Transaction):
                    # try:
                    #     existing_filter.SetCategoriesAndRules(categories, final_element_filter)
                    #     print("# Updated existing filter '{}' rules/categories.".format(filter_name))
                    # except System.Exception as update_ex:
                    #     print("# Warning: Failed to update existing filter '{}': {}".format(filter_name, update_ex))
                else:
                    # Create the Parameter Filter Element (Transaction handled externally by C# wrapper)
                    try:
                        parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, final_element_filter)
                        # print("# Created new filter: '{}'".format(filter_name)) # Optional Debug
                    except System.Exception as create_ex:
                        print("# Error creating filter '{}': {}".format(filter_name, create_ex))

                # 6. Proceed if the filter exists or was created
                if parameter_filter:
                    # Define Override Graphic Settings
                    override_settings = OverrideGraphicSettings()
                    # Set surface transparency (0=opaque, 100=fully transparent)
                    try:
                         override_settings.SetSurfaceTransparency(transparency_value)
                    except System.ArgumentException as trans_ex:
                         print("# Error setting transparency ({}) for filter '{}': {}. Value must be 0-100.".format(transparency_value, filter_name, trans_ex.Message))
                         # Attempt to proceed without transparency override if value was invalid
                         override_settings = OverrideGraphicSettings() # Reset to default

                    # Apply the filter and overrides to the active view (Transaction handled externally by C# wrapper)
                    try:
                        if not active_view.IsFilterApplied(parameter_filter.Id):
                            active_view.AddFilter(parameter_filter.Id)
                        active_view.SetFilterOverrides(parameter_filter.Id, override_settings)
                        # print("# Successfully applied filter '{}' with overrides to active view.".format(filter_name)) # Optional Debug
                    except System.Exception as apply_ex:
                        # This might fail if the view type doesn't support overrides or filters
                        print("# Error applying filter or overrides for '{}' to the view: {}".format(filter_name, apply_ex))

            # Final check if filter wasn't processed successfully after finding types
            if not parameter_filter and matching_panel_type_ids.Count > 0:
                 # This case occurs if filter creation failed and it didn't exist before
                 print("# Filter '{}' could not be found or created.".format(filter_name))