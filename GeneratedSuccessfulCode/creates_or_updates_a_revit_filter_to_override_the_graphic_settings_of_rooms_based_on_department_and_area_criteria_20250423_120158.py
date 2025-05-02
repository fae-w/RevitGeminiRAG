# Purpose: This script creates or updates a Revit filter to override the graphic settings of rooms based on department and area criteria.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Needed for uidoc
clr.AddReference('System.Collections')
clr.AddReference('System') # Required for List generic type

# Standard library imports
import System

# Revit API Imports
from System.Collections.Generic import List, ICollection, IList, IDictionary # Import necessary generic types
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, LogicalAndFilter, ParameterFilterRuleFactory,
    # FilterStringRule, FilterNumericLessRule, <--- Removed these as they caused import error and Factory is used
    OverrideGraphicSettings, Color, View, BuiltInParameter, ParameterFilterUtilities,
    FillPatternElement, FillPatternTarget, Category, ParameterElement,
    UnitUtils, # Keep for potential future use
    InstanceBinding, Element, ElementFilter # Added ElementFilter
)
# Note: BuiltInParameterGroup is an enum, accessed via Autodesk.Revit.DB.BuiltInParameterGroup, not imported directly

# --- Configuration ---
filter_name = "Small Office Rooms"
target_bic = BuiltInCategory.OST_Rooms
department_param_name = "Department" # Fallback name if BIP fails
department_param_bip = BuiltInParameter.ROOM_DEPARTMENT
department_value = "Office Space"
area_param_name = "Area" # Fallback name if BIP fails
area_param_bip = BuiltInParameter.ROOM_AREA
area_value_sqm = 12.0 # Area threshold in square meters
override_color = Color(255, 255, 0) # Yellow
solid_fill_pattern_name = "<Solid fill>" # Revit's default name for the solid fill pattern

# --- Convert Area to Internal Units (Square Feet) ---
# Revit's internal unit for Area is typically square feet.
# 1 square meter = 10.7639104 square feet
area_value_sqft = area_value_sqm * 10.7639104
# print("# Area threshold converted: {{}} sqm = {{:.4f}} sqft".format(area_value_sqm, area_value_sqft)) # Optional debug print

# --- Helper function to find Solid Fill Pattern ---
def find_solid_fill_pattern_id(doc_param):
    """Finds the ElementId of the 'Solid fill' drafting pattern."""
    solid_pattern_id = ElementId.InvalidElementId
    # First, try finding specifically the solid fill pattern marked as IsSolidFill for Drafting
    collector = FilteredElementCollector(doc_param).OfClass(FillPatternElement)
    for pattern_elem in collector:
        try:
            # Check if it's a FillPatternElement before getting the pattern
            if isinstance(pattern_elem, FillPatternElement):
                pattern = pattern_elem.GetFillPattern()
                # Check if it's a FillPattern, IsSolidFill, and Target is Drafting
                if pattern and pattern.IsSolidFill and pattern.Target == FillPatternTarget.Drafting:
                     solid_pattern_id = pattern_elem.Id
                     # print("# Found Solid Fill Pattern (Drafting) by IsSolidFill: {{}}".format(solid_pattern_id)) # Debug
                     break # Found the Drafting Solid Fill
        except Exception as e:
            # Ignore elements that fail GetFillPattern() or accessing properties
            # print("Debug: Error accessing pattern info for element {{}}: {{}}".format(pattern_elem.Id, e))
            pass

    # Fallback: If not found via IsSolidFill, search by name (less reliable)
    if solid_pattern_id == ElementId.InvalidElementId:
         # print("# Solid fill not found by IsSolidFill. Searching by name: '{{}}'".format(solid_fill_pattern_name)) # Debug
         pattern_elem_by_name = None
         try:
             collector_by_name = FilteredElementCollector(doc_param).OfClass(FillPatternElement)
             for p in collector_by_name:
                 # Check name and target safely
                 pattern_name = ""
                 try:
                     pattern_name = p.Name
                 except: pass # Ignore elements without a valid name property access

                 is_drafting = False
                 try:
                     fill_pattern = p.GetFillPattern()
                     if fill_pattern:
                         is_drafting = (fill_pattern.Target == FillPatternTarget.Drafting)
                 except: pass # Ignore errors getting pattern or target

                 if pattern_name == solid_fill_pattern_name and is_drafting:
                     pattern_elem_by_name = p
                     # print("# Found potential solid fill by name: {{}} (Drafting: {{}})".format(p.Id, is_drafting)) # Debug
                     break
         except Exception as e_coll:
             # print("# Error during fallback search for solid fill: {{}}".format(e_coll)) # Debug
             pass # Ignore collector errors

         if pattern_elem_by_name:
             solid_pattern_id = pattern_elem_by_name.Id
             # print("# Found solid fill pattern by name fallback: {{}}".format(solid_pattern_id)) # Optional debug print

    # Final check if still not found
    # if solid_pattern_id == ElementId.InvalidElementId:
    #     print("# Warning: Solid fill pattern '{{}}' for Drafting target not found.".format(solid_fill_pattern_name)) # Debug

    return solid_pattern_id

# --- Get Rooms Category ---
# Use doc from the provided scope
rooms_category = None
rooms_category_id = ElementId.InvalidElementId
try:
    rooms_category = Category.GetCategory(doc, target_bic)
    if rooms_category:
        rooms_category_id = rooms_category.Id
    else:
        print("# Error: Rooms category (OST_Rooms) not found in the document.")

except System.ArgumentNullException: # Handle case where BuiltInCategory is invalid
     print("# Error: Invalid BuiltInCategory specified for Rooms: {{}}".format(target_bic))
except Exception as cat_ex:
     print("# Error getting Rooms category: {{}}".format(cat_ex))


# --- Check if Category is Filterable and Parameters Exist ---
can_proceed = False
dept_param_id = ElementId.InvalidElementId
area_param_id = ElementId.InvalidElementId

if rooms_category_id != ElementId.InvalidElementId:
    filterable_categories = ParameterFilterUtilities.GetAllFilterableCategories()
    if rooms_category_id not in filterable_categories:
        print("# Error: The 'Rooms' category (OST_Rooms) is not filterable.")
    else:
        # --- Check if Parameters are Filterable for the Category ---
        categories_list_for_check = List[ElementId]([rooms_category_id])
        filterable_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories_list_for_check)
        filterable_param_ids = set(p_id for p_id in filterable_params) # Use a set for faster lookups

        # Check Department Parameter
        temp_dept_param_id = ElementId(department_param_bip)
        if temp_dept_param_id in filterable_param_ids:
            dept_param_id = temp_dept_param_id
            # print("# Using BuiltInParameter ROOM_DEPARTMENT (ID: {{}})".format(dept_param_id)) # Optional debug print
        else:
            print("# Warning: BuiltInParameter ROOM_DEPARTMENT not filterable for Rooms. Trying name: '{{}}'".format(department_param_name))
            # Fallback search by name (optimized)
            param_found = False
            # Find ParameterElement by name first
            param_elem_by_name = None
            all_params_collector = FilteredElementCollector(doc).OfClass(ParameterElement)
            for p_elem in all_params_collector:
                 try:
                     if p_elem.Name == department_param_name:
                          param_elem_by_name = p_elem
                          break
                 except: pass # Ignore errors accessing name

            if param_elem_by_name and param_elem_by_name.Id in filterable_param_ids:
                # Check if the parameter definition applies to the room category
                try:
                    internal_def = param_elem_by_name.GetDefinition()
                    binding_map = doc.ParameterBindings
                    if binding_map.Contains(internal_def):
                        binding = binding_map.Item[internal_def]
                        if binding and isinstance(binding, InstanceBinding):
                            cat_set = binding.Categories
                            if cat_set.Contains(rooms_category):
                                dept_param_id = param_elem_by_name.Id
                                print("# Found filterable parameter by name: '{{}}' (ID: {{}})".format(department_param_name, dept_param_id))
                                param_found = True
                    else:
                        # Check Shared Parameters bound to Project Parameters
                        # If it's filterable, assume it's bound correctly somewhere if name matches
                         dept_param_id = param_elem_by_name.Id
                         print("# Found potentially filterable parameter by name: '{{}}' (ID: {{}}). Assuming correct binding.".format(department_param_name, dept_param_id))
                         param_found = True

                except Exception as e:
                    # print("# Debug: Error checking binding for param '{{}}': {{}}".format(department_param_name, e))
                    pass # Ignore errors during parameter binding check
            if not param_found:
                print("# Error: Could not find a filterable parameter for 'Department' by name ('{{}}') or BuiltInParam.".format(department_param_name))


        # Check Area Parameter
        temp_area_param_id = ElementId(area_param_bip)
        if temp_area_param_id in filterable_param_ids:
            area_param_id = temp_area_param_id
            # print("# Using BuiltInParameter ROOM_AREA (ID: {{}})".format(area_param_id)) # Optional debug print
        else:
            # Area is fundamental, if the BIP isn't filterable, something is very wrong.
            print("# Error: BuiltInParameter ROOM_AREA is not filterable for Rooms. Cannot proceed with Area rule.")
            # Setting area_param_id remains InvalidElementId

        # Set proceed flag based on finding valid parameters
        can_proceed = (dept_param_id != ElementId.InvalidElementId and area_param_id != ElementId.InvalidElementId)

# --- Main Processing Logic ---
if can_proceed:
    # --- Find solid fill pattern ---
    solid_fill_id = find_solid_fill_pattern_id(doc)
    if solid_fill_id == ElementId.InvalidElementId:
        print("# Warning: Could not find the 'Solid fill' pattern. Overrides will lack surface fill.")
        apply_fill = False
    else:
        apply_fill = True
        # print("# Found Solid Fill Pattern ID: {{}}".format(solid_fill_id)) # Optional debug print

    # --- Get Active View ---
    # Use uidoc from the provided scope to get ActiveView
    active_view = None
    view_can_have_filters = False
    try:
        if uidoc:
            active_view = uidoc.ActiveView
            if active_view and active_view.IsValidObject:
                 # Check if view type supports filters
                 if active_view.AreGraphicsOverridesAllowed():
                      view_can_have_filters = True
                 else:
                      print("# Error: View '{{}}' (Type: {{}}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
            else:
                 print("# Error: No active view found or the active view is invalid.")
        else:
             print("# Error: uidoc variable not available in scope.")

    except Exception as view_ex:
        print("# Error getting active view: {{}}".format(view_ex))
        # Ensure can_proceed reflects the failure
        view_can_have_filters = False

    # Final check before filter creation/application
    can_proceed = can_proceed and view_can_have_filters

    if can_proceed:
        # --- Define Categories ---
        categories = List[ElementId]()
        categories.Add(rooms_category_id)

        # --- Define Filter Rules ---
        # Case sensitivity for string rules: Use False for case-insensitive matching
        rule1 = ParameterFilterRuleFactory.CreateEqualsRule(dept_param_id, department_value, False)
        # Use FilterNumericLessRule for numeric comparison. Revit handles internal units.
        # Tolerance (epsilon) is often not strictly needed for 'Less' but good practice if using 'Equals' with doubles.
        epsilon = 0.0001 # Small tolerance
        rule2 = ParameterFilterRuleFactory.CreateLessRule(area_param_id, area_value_sqft, epsilon)

        # --- Combine Rules with LogicalAndFilter ---
        rules = List[FilterRule]()
        rules.Add(rule1)
        rules.Add(rule2)
        element_filter = None
        try:
            # Create the logical AND filter combining the rules
            # ElementParameterFilter wraps IList<FilterRule> into an ElementFilter
            element_parameter_filter = ElementParameterFilter(rules)

            # LogicalAndFilter constructor takes IList<ElementFilter>
            element_filter_list = List[ElementFilter]()
            element_filter_list.Add(element_parameter_filter) # Add the wrapped rules
            element_filter = LogicalAndFilter(element_filter_list)

        except Exception as filter_create_err:
            print("# Error: Failed to create LogicalAndFilter with rules: {{}}".format(filter_create_err))
            can_proceed = False # Cannot proceed if filter logic fails

        if can_proceed and element_filter:
            # --- Check for Existing Filter ---
            existing_filter = None
            filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
            for f in filter_collector:
                filter_name_check = None
                try:
                     filter_name_check = f.Name
                except Exception as name_err:
                     pass # Ignore elements where name access fails

                if filter_name_check == filter_name:
                    existing_filter = f
                    break

            parameter_filter = None
            # IMPORTANT: Filter creation/modification requires a Transaction (assumed handled externally).
            if existing_filter:
                parameter_filter = existing_filter
                print("# Found existing filter: '{{}}'".format(filter_name))
                try:
                    # Check if categories need update
                    current_cats_ok = True
                    current_cats = existing_filter.GetCategories()
                    if current_cats.Count != categories.Count:
                        current_cats_ok = False
                    else:
                        current_cat_ids = set(c.IntegerValue for c in current_cats)
                        new_cat_ids = set(c.IntegerValue for c in categories)
                        if current_cat_ids != new_cat_ids:
                            current_cats_ok = False

                    if not current_cats_ok:
                         existing_filter.SetCategories(categories)
                         print("# Updated categories for filter '{{}}'.".format(filter_name))

                    # Check if rules need update (safer to just set)
                    existing_filter.SetElementFilter(element_filter) # Update the rules
                    print("# Updated rules for filter '{{}}'.".format(filter_name))
                except Exception as update_err:
                    print("# Warning: Failed to update existing filter '{{}}': {{}}".format(filter_name, update_err))
                    parameter_filter = None # Mark as unusable if update failed
            else:
                # --- Create New Filter ---
                try:
                     if ParameterFilterElement.IsNameUnique(doc, filter_name):
                         parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                         print("# Created new filter: '{{}}'".format(filter_name))
                     else:
                         print("# Warning: Filter name '{{}}' reported as not unique, attempting to find it again.".format(filter_name))
                         filter_collector_retry = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
                         for f_retry in filter_collector_retry:
                              name_retry = None
                              try: name_retry = f_retry.Name
                              except: pass
                              if name_retry == filter_name:
                                  parameter_filter = f_retry
                                  print("# Found filter '{{}}' on retry.".format(filter_name))
                                  # Attempt to update it
                                  try:
                                       parameter_filter.SetCategories(categories)
                                       parameter_filter.SetElementFilter(element_filter)
                                       print("# Updated filter '{{}}' rules and categories after retry.".format(filter_name))
                                  except Exception as update_err_retry:
                                       print("# Warning: Failed to update filter '{{}}' after retry: {{}}".format(filter_name, update_err_retry))
                                       parameter_filter = None # Failed to update, treat as unusable
                                  break
                         if not parameter_filter:
                             print("# Error: Filter name '{{}}' is not unique, and filter could not be found on retry.".format(filter_name))

                except Exception as e:
                    print("# Error creating filter '{{}}': {{}}".format(filter_name, e))
                    parameter_filter = None # Creation failed

            # --- Apply Filter and Overrides to View ---
            if parameter_filter and parameter_filter.IsValidObject:
                # Define Override Graphic Settings
                override_settings = OverrideGraphicSettings()
                if apply_fill:
                    # Use Surface patterns for plan views of rooms
                    override_settings.SetSurfaceForegroundPatternId(solid_fill_id)
                    override_settings.SetSurfaceForegroundPatternColor(override_color)
                    override_settings.SetSurfaceForegroundPatternVisible(True)
                    # Optionally set background pattern if needed
                    # override_settings.SetSurfaceBackgroundPatternId(solid_fill_id)
                    # override_settings.SetSurfaceBackgroundPatternColor(override_color)
                    # override_settings.SetSurfaceBackgroundPatternVisible(True)
                else:
                     # Fallback: Maybe just color projection lines if no fill pattern?
                     override_settings.SetProjectionLineColor(override_color)
                     print("# Applying line color override as solid fill pattern was not found.")


                # Apply the filter to the active view (requires transaction managed externally)
                try:
                    filter_id_to_apply = parameter_filter.Id
                    applied_filter_ids_collection = active_view.GetFilters() # Returns ICollection<ElementId>
                    # Convert ICollection<ElementId> to a Python list or set for easier checking
                    applied_filter_ids = List[ElementId](applied_filter_ids_collection) # Can use List for 'in' check

                    category_visible_in_view = False
                    try:
                        category_visible_in_view = not active_view.GetCategoryHidden(rooms_category_id)
                    except Exception as cat_vis_ex:
                        print("# Warning: Could not determine category visibility status: {{}}".format(cat_vis_ex))

                    filter_already_applied = filter_id_to_apply in applied_filter_ids

                    if not filter_already_applied:
                        can_add_filter = category_visible_in_view or active_view.CanCategoryBeHidden(rooms_category_id)

                        if can_add_filter:
                            active_view.AddFilter(filter_id_to_apply)
                            print("# Added filter '{{}}' to view '{{}}'.".format(filter_name, active_view.Name))
                            filter_already_applied = True # Mark as applied for override step
                        else:
                             print("# Warning: Filter '{{}}' cannot be added to view '{{}}'. The Rooms category visibility might be permanently off.".format(filter_name, active_view.Name))
                             filter_id_to_apply = ElementId.InvalidElementId
                    else:
                         print("# Filter '{{}}' is already present in view '{{}}'.".format(filter_name, active_view.Name))

                    # Set the overrides for the filter in the view, only if the filter is applicable/applied
                    if filter_id_to_apply != ElementId.InvalidElementId and filter_already_applied:
                        active_view.SetFilterOverrides(filter_id_to_apply, override_settings)

                        if not active_view.IsFilterEnabled(filter_id_to_apply):
                             active_view.SetIsFilterEnabled(filter_id_to_apply, True)

                        if not active_view.GetFilterVisibility(filter_id_to_apply):
                             active_view.SetFilterVisibility(filter_id_to_apply, True)

                        print("# Applied/Updated overrides for filter '{{}}' in view '{{}}'.".format(filter_name, active_view.Name))

                        if not category_visible_in_view:
                             print("# Info: Filter '{{}}' overrides applied, but the main Rooms category might be hidden in view '{{}}' V/G settings.".format(filter_name, active_view.Name))

                except Exception as e:
                    print("# Error applying filter or overrides to the view '{{}}': {{}}".format(active_view.Name, e))
            elif not existing_filter and not parameter_filter:
                print("# Filter '{{}}' could not be created or found after failure.".format(filter_name))
            elif existing_filter and not parameter_filter:
                 print("# Filter '{{}}' exists but could not be updated or used.".format(filter_name))

# Final messages if initial checks failed earlier
elif rooms_category_id == ElementId.InvalidElementId:
    pass # Error already printed
elif dept_param_id == ElementId.InvalidElementId or area_param_id == ElementId.InvalidElementId:
    print("# Cannot proceed: Required parameters ('Department' or 'Area') not found or not filterable for Rooms.")
# else cases handled within the main block for view/category checks

# print("# Script finished.") # Optional final message