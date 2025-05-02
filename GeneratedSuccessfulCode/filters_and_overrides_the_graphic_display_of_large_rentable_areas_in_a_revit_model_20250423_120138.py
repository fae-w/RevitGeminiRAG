# Purpose: This script filters and overrides the graphic display of large rentable areas in a Revit model.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for List, Double, Math
import math
from System import Exception as SysException
from System.Collections.Generic import List, ICollection, IList, ISet

# Revit API Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementParameterFilter, FilterRule, LogicalAndFilter, ParameterFilterRuleFactory,
    OverrideGraphicSettings, View, BuiltInParameter, ParameterFilterUtilities,
    Area, AreaScheme, Category, ElementFilter, Element
)

# --- Configuration ---
filter_name = "Large Rentable Areas"
target_category_bic = BuiltInCategory.OST_Areas
target_area_scheme_name = "Rentable Area"
area_threshold_sqm = 1000.0
override_pattern_visibility = False # Set fill pattern visibility off

# --- Convert Area Threshold to Internal Units (Square Feet) ---
# Revit's internal unit for Area is square feet.
# 1 square meter = 10.7639104 square feet
area_threshold_sqft = area_threshold_sqm * 10.7639104
epsilon = 0.0001 # Tolerance for numeric comparisons

# --- Find Target Area Scheme ID ---
target_area_scheme_id = ElementId.InvalidElementId
area_scheme_collector = FilteredElementCollector(doc).OfClass(AreaScheme)
for scheme in area_scheme_collector:
    try:
        if scheme.Name == target_area_scheme_name:
            target_area_scheme_id = scheme.Id
            # print("# Found Area Scheme '{{}}' with ID: {{}}".format(target_area_scheme_name, target_area_scheme_id)) # Debug
            break
    except Exception as e:
        # print("# Warning: Could not access name for Area Scheme element ID {{}}: {{}}".format(scheme.Id, e)) # Debug
        pass # Ignore elements where name access fails

if target_area_scheme_id == ElementId.InvalidElementId:
    print("# Error: Area Scheme named '{{}}' not found in the document. Cannot create filter.".format(target_area_scheme_name))
    can_proceed = False
else:
    can_proceed = True

# --- Get Areas Category ---
areas_category = None
areas_category_id = ElementId.InvalidElementId
if can_proceed:
    try:
        areas_category = Category.GetCategory(doc, target_category_bic)
        if areas_category:
            areas_category_id = areas_category.Id
        else:
            print("# Error: Areas category (OST_Areas) not found in the document.")
            can_proceed = False
    except SysException: # Handle case where BuiltInCategory is invalid
         print("# Error: Invalid BuiltInCategory specified for Areas: {{}}".format(target_category_bic))
         can_proceed = False
    except Exception as cat_ex:
         print("# Error getting Areas category: {{}}".format(cat_ex))
         can_proceed = False

# --- Check if Category is Filterable and Parameters Exist/Filterable ---
if can_proceed:
    filterable_categories = ParameterFilterUtilities.GetAllFilterableCategories()
    if areas_category_id not in filterable_categories:
        print("# Error: The 'Areas' category (OST_Areas) is not filterable.")
        can_proceed = False
    else:
        # --- Check if Parameters are Filterable for the Category ---
        categories_list_for_check = List[ElementId]([areas_category_id])
        filterable_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories_list_for_check)
        filterable_param_ids = set(p_id for p_id in filterable_params) # Use a set for faster lookups

        # Check Area Scheme ID Parameter
        area_scheme_param_bip = BuiltInParameter.AREA_SCHEME_ID
        area_scheme_param_id = ElementId(area_scheme_param_bip)
        if area_scheme_param_id not in filterable_param_ids:
            print("# Error: BuiltInParameter AREA_SCHEME_ID is not filterable for Areas.")
            can_proceed = False

        # Check Area Parameter
        area_param_bip = BuiltInParameter.AREA_AREA # Parameter containing the Area value
        area_param_id = ElementId(area_param_bip)
        if area_param_id not in filterable_param_ids:
            print("# Error: BuiltInParameter AREA_AREA is not filterable for Areas.")
            can_proceed = False

# --- Get Active View and Validate ---
active_view = None
view_can_have_filters = False
if can_proceed:
    try:
        if uidoc:
            active_view = uidoc.ActiveView
            if active_view and active_view.IsValidObject and not active_view.IsTemplate:
                 # Check if view type supports filters
                 if active_view.AreGraphicsOverridesAllowed():
                      # Check if the view is an Area Plan view associated with the correct Area Scheme
                      is_correct_view_type = False
                      if hasattr(active_view, "AreaScheme") and active_view.AreaScheme is not None:
                          if active_view.AreaScheme.Id == target_area_scheme_id:
                              is_correct_view_type = True
                          else:
                              try:
                                  # Get names for better error message
                                  view_scheme_name = active_view.AreaScheme.Name
                                  print("# Warning: Active view '{{}}' is an Area Plan, but uses scheme '{{}}', not '{{}}'. Filter rules apply, but might not be meaningful.".format(active_view.Name, view_scheme_name, target_area_scheme_name))
                                  is_correct_view_type = True # Allow applying, but warn user. Alternatively, set to False to prevent.
                              except:
                                   print("# Warning: Active view '{{}}' is an Area Plan, but its Area Scheme could not be verified against '{{}}'.".format(active_view.Name, target_area_scheme_name))
                                   is_correct_view_type = True # Allow applying
                      else:
                           # It's not an Area Plan view, but can it still show Areas and apply filters? Yes.
                           # print("# Info: Active view '{{}}' is not an Area Plan view. Ensure Areas are visible.".format(active_view.Name)) # Optional Info
                           is_correct_view_type = True # Allow applying filter to non-Area Plan views

                      if is_correct_view_type:
                            view_can_have_filters = True
                      # else: Filter will not be applied if is_correct_view_type remains False and logic requires it

                 else:
                      print("# Error: View '{{}}' (Type: {{}}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
            else:
                 print("# Error: No active valid view found, the active view is invalid, or it is a view template.")
        else:
             print("# Error: uidoc variable not available in scope.")
    except Exception as view_ex:
        print("# Error getting or validating active view: {{}}".format(view_ex))

    # Update can_proceed based on view validation
    can_proceed = can_proceed and view_can_have_filters

# --- Main Processing Logic ---
if can_proceed:
    # --- Define Categories for Filter ---
    categories = List[ElementId]()
    categories.Add(areas_category_id)

    # --- Define Filter Rules ---
    # Rule 1: Area Scheme ID equals the ID found earlier
    rule1 = ParameterFilterRuleFactory.CreateEqualsRule(area_scheme_param_id, target_area_scheme_id)
    # Rule 2: Area value is greater than the threshold
    rule2 = ParameterFilterRuleFactory.CreateGreaterRule(area_param_id, area_threshold_sqft, epsilon)

    # --- Combine Rules with LogicalAndFilter ---
    rules = List[FilterRule]()
    rules.Add(rule1)
    rules.Add(rule2)
    element_filter = None
    try:
        element_parameter_filter = ElementParameterFilter(rules)
        element_filter_list = List[ElementFilter]()
        element_filter_list.Add(element_parameter_filter)
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
            try: filter_name_check = f.Name
            except: pass # Ignore elements where name access fails
            if filter_name_check == filter_name:
                existing_filter = f
                break

        parameter_filter = None
        # Transaction is handled externally by the C# wrapper
        if existing_filter:
            parameter_filter = existing_filter
            print("# Found existing filter: '{{}}'".format(filter_name))
            try:
                # Check if categories need update
                current_cats = existing_filter.GetCategories()
                if current_cats.Count != categories.Count or not all(c in current_cats for c in categories):
                     existing_filter.SetCategories(categories)
                     print("# Updated categories for filter '{{}}'.".format(filter_name))

                # Check if rules need update (simpler to just set them)
                existing_filter.SetElementFilter(element_filter)
                print("# Updated rules for filter '{{}}'.".format(filter_name))
            except Exception as update_err:
                print("# Warning: Failed to update existing filter '{{}}': {{}}".format(filter_name, update_err))
                parameter_filter = None # Mark as unusable if update failed
        else:
            # --- Create New Filter ---
            try:
                 # Check name uniqueness before creation (though C# wrapper manages transaction)
                 # if ParameterFilterElement.IsNameUnique(doc, filter_name):
                 parameter_filter = ParameterFilterElement.Create(doc, filter_name, categories, element_filter)
                 print("# Created new filter: '{{}}'".format(filter_name))
                 # else: # Handle non-unique name case if needed, maybe find it again
                 #    print("# Error: Filter name '{{}}' is not unique.".format(filter_name))
                 #    parameter_filter = None # Indicate creation failed due to name
            except Exception as e:
                print("# Error creating filter '{{}}': {{}}".format(filter_name, e))
                parameter_filter = None # Creation failed

        # --- Apply Filter and Overrides to View ---
        if parameter_filter and parameter_filter.IsValidObject:
            # Define Override Graphic Settings
            override_settings = OverrideGraphicSettings()
            try:
                # Set fill pattern visibility (both foreground and background)
                override_settings.SetSurfaceForegroundPatternVisible(override_pattern_visibility)
                override_settings.SetSurfaceBackgroundPatternVisible(override_pattern_visibility)
                # Area elements don't typically show in section/elevation, but set cut patterns too for completeness
                override_settings.SetCutForegroundPatternVisible(override_pattern_visibility)
                override_settings.SetCutBackgroundPatternVisible(override_pattern_visibility)

                # Optional: Clear pattern IDs if necessary (usually visibility is enough)
                # override_settings.SetSurfaceForegroundPatternId(ElementId.InvalidElementId)
                # override_settings.SetSurfaceBackgroundPatternId(ElementId.InvalidElementId)
                # override_settings.SetCutForegroundPatternId(ElementId.InvalidElementId)
                # override_settings.SetCutBackgroundPatternId(ElementId.InvalidElementId)

            except Exception as override_def_err:
                print("# Error defining override settings: {{}}".format(override_def_err))
                parameter_filter = None # Cannot apply overrides if definition fails

            # Apply the filter to the active view (requires transaction managed externally)
            if parameter_filter: # Check again in case override definition failed
                try:
                    filter_id_to_apply = parameter_filter.Id
                    applied_filter_ids_collection = active_view.GetFilters()
                    applied_filter_ids = List[ElementId](applied_filter_ids_collection)

                    filter_already_applied = filter_id_to_apply in applied_filter_ids

                    if not filter_already_applied:
                         # Check if the category is visible or can be made visible
                         category_visible = not active_view.GetCategoryHidden(areas_category_id)
                         can_add_filter = category_visible or active_view.CanCategoryBeHidden(areas_category_id)

                         if can_add_filter:
                             active_view.AddFilter(filter_id_to_apply)
                             print("# Added filter '{{}}' to view '{{}}'.".format(filter_name, active_view.Name))
                             filter_already_applied = True # Mark as applied for override step
                         else:
                              print("# Warning: Filter '{{}}' cannot be added to view '{{}}'. The Areas category visibility might be permanently off.".format(filter_name, active_view.Name))
                              filter_id_to_apply = ElementId.InvalidElementId # Prevent override attempt
                    else:
                         print("# Filter '{{}}' is already present in view '{{}}'.".format(filter_name, active_view.Name))

                    # Set the overrides for the filter in the view
                    if filter_id_to_apply != ElementId.InvalidElementId and filter_already_applied:
                        active_view.SetFilterOverrides(filter_id_to_apply, override_settings)

                        # Ensure filter is enabled and visible in the view's V/G Filters tab
                        if not active_view.IsFilterEnabled(filter_id_to_apply):
                             active_view.SetIsFilterEnabled(filter_id_to_apply, True)
                        if not active_view.GetFilterVisibility(filter_id_to_apply):
                             active_view.SetFilterVisibility(filter_id_to_apply, True)

                        print("# Applied/Updated overrides for filter '{{}}' in view '{{}}' (Pattern Visibility: {{}}).".format(filter_name, active_view.Name, override_pattern_visibility))

                except Exception as e:
                    print("# Error applying filter or overrides to the view '{{}}': {{}}".format(active_view.Name, e))

        elif not parameter_filter:
            print("# Filter '{{}}' could not be created or updated. Overrides not applied.".format(filter_name))

# Final messages if initial checks failed earlier
elif target_area_scheme_id == ElementId.InvalidElementId:
    pass # Error already printed
elif areas_category_id == ElementId.InvalidElementId:
    pass # Error already printed
elif not can_proceed: # Catches parameter filterability issues or view issues
    print("# Cannot proceed due to previous errors (Category/Parameter filterability or View issues).")

# print("# Script finished.") # Optional final message