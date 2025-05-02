# Purpose: This script isolates elements within a specified scope box in a 3D Revit view by applying a filter.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    # ScopeBox, # Removed - Not directly needed for import if collecting by category
    ElementId,
    View3D,
    ParameterFilterElement,
    FilterRule, # Needed for ParameterFilterRuleFactory results and LogicalFilter
    ParameterFilterRuleFactory,
    LogicalOrFilter,
    BuiltInParameter,
    Category
    # View # Not strictly needed if checking isinstance(active_view, View3D)
)
from System.Collections.Generic import List

# --- Configuration ---
scope_box_name = 'Core Area'
filter_name = "Filter - Isolate Scope Box '{}'".format(scope_box_name) # Use curly braces {} for format

# --- Get Active View and Document ---
# Assumes 'uidoc' and 'doc' are available globally
active_view = uidoc.ActiveView

# --- Check Compatibility ---
if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View3D):
    print("# Error: Active view is not a 3D view.")
# Check if the view supports filters by trying to get existing ones (avoids InvalidElementId issue)
elif not active_view.AreGraphicsOverridesAllowed(): # A more robust check
     print("# Error: Active view '{}' does not support filters/graphics overrides.".format(active_view.Name))
else:
    # --- Find the Scope Box ---
    scope_box_element = None
    # Correctly collect scope box elements using the BuiltInCategory
    scope_box_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ScopeBoxes).WhereElementIsNotElementType()
    for sb in scope_box_collector:
        if sb.Name == scope_box_name:
            scope_box_element = sb
            break

    if not scope_box_element:
        print("# Error: Scope Box named '{}' not found in the project.".format(scope_box_name))
    else:
        scope_box_id = scope_box_element.Id

        # --- Get Scope Box Parameter ID ---
        # Using BuiltInParameter.ELEMENT_SCOPE_BOX is standard practice.
        scope_box_param_id = ElementId(BuiltInParameter.ELEMENT_SCOPE_BOX)

        # --- Define Categories for the Filter ---
        # Define categories known to commonly use Scope Boxes.
        categories_to_filter_bics = [
            BuiltInCategory.OST_Walls, BuiltInCategory.OST_Floors,
            BuiltInCategory.OST_StructuralColumns, BuiltInCategory.OST_StructuralFraming,
            BuiltInCategory.OST_StructuralFoundation, BuiltInCategory.OST_Ceilings,
            BuiltInCategory.OST_Roofs, BuiltInCategory.OST_Grids,
            BuiltInCategory.OST_Levels, BuiltInCategory.OST_Columns, # Architectural Columns
            BuiltInCategory.OST_Stairs, BuiltInCategory.OST_Ramps,
            BuiltInCategory.OST_Railings, BuiltInCategory.OST_Furniture,
            BuiltInCategory.OST_Casework, BuiltInCategory.OST_PlumbingFixtures,
            BuiltInCategory.OST_MechanicalEquipment, BuiltInCategory.OST_ElectricalEquipment,
            BuiltInCategory.OST_LightingFixtures, BuiltInCategory.OST_Doors,
            BuiltInCategory.OST_Windows
            # Add more relevant categories as needed
        ]
        categories_to_filter_ids = List[ElementId]()
        all_cat_ids_in_doc = [c.Id for c in doc.Settings.Categories] # Get all valid category IDs

        for bic in categories_to_filter_bics:
            try:
                cat = Category.GetCategory(doc, bic)
                if cat and cat.Id in all_cat_ids_in_doc and cat.AllowsBoundParameters: # Ensure category exists and supports parameters
                    categories_to_filter_ids.Add(cat.Id)
            except:
                # Ignore if a BuiltInCategory doesn't exist in the specific project template/version
                pass

        if categories_to_filter_ids.Count == 0:
             print("# Error: Could not find any specified filterable categories in the project.")
        else:
            # --- Create Filter Rules ---
            # Rule 1: Element's Scope Box parameter IS NOT EQUAL to the target Scope Box ID
            rule_not_equal = ParameterFilterRuleFactory.CreateNotEqualsRule(scope_box_param_id, scope_box_id)

            # Rule 2: Element's Scope Box parameter IS EQUAL to None (InvalidElementId means unassigned)
            rule_is_none = ParameterFilterRuleFactory.CreateEqualsRule(scope_box_param_id, ElementId.InvalidElementId)

            # Combine rules using LogicalOrFilter:
            # We want to HIDE elements where (ScopeBox != Target) OR (ScopeBox == None)
            # This effectively isolates elements where ScopeBox == Target
            element_filter_logic = LogicalOrFilter(rule_not_equal, rule_is_none)

            # --- Find or Create Parameter Filter Element ---
            parameter_filter_element = None
            filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
            for existing_filter in filter_collector:
                if existing_filter.Name == filter_name:
                    parameter_filter_element = existing_filter
                    # Optional: Update existing filter's categories and rules if needed
                    # For simplicity, we'll just use the existing one by name match
                    # parameter_filter_element.SetCategories(categories_to_filter_ids)
                    # parameter_filter_element.SetElementFilter(element_filter_logic)
                    # print("# Found and potentially updated existing filter: '{}'".format(filter_name)) # Debug
                    break

            if not parameter_filter_element:
                try:
                    # Create the filter since it doesn't exist
                    # Pass the combined LogicalOrFilter directly to Create
                    parameter_filter_element = ParameterFilterElement.Create(doc, filter_name, categories_to_filter_ids, element_filter_logic)
                    # print("# Created new filter: '{}'".format(filter_name)) # Debug
                except Exception as create_ex:
                    print("# Error creating ParameterFilterElement: {}".format(create_ex))
                    parameter_filter_element = None # Ensure failure state

            # --- Apply Filter to the View ---
            if parameter_filter_element:
                filter_id = parameter_filter_element.Id
                try:
                    # Check if the filter is already applied before adding
                    applied_filters = active_view.GetFilters()
                    if filter_id not in applied_filters:
                        active_view.AddFilter(filter_id)
                        # print("# Added filter '{}' to view '{}'".format(filter_name, active_view.Name)) # Debug

                    # Set the filter to HIDE elements that match the rules
                    # (i.e., elements outside the scope box or with no scope box)
                    active_view.SetFilterVisibility(filter_id, False)

                    # Ensure the filter is enabled in the view's V/G settings
                    active_view.SetIsFilterEnabled(filter_id, True)

                    print("# Applied filter '{}' to isolate scope box '{}' in view '{}'.".format(filter_name, scope_box_name, active_view.Name)) # Success message
                except Exception as apply_ex:
                    print("# Error applying filter '{}' to view '{}': {}".format(filter_name, active_view.Name, apply_ex))
            else:
                print("# Filter could not be found or created. Cannot apply to view.")