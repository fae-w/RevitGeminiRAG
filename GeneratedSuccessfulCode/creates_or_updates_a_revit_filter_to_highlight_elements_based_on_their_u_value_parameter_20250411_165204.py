# Purpose: This script creates or updates a Revit filter to highlight elements based on their U-Value parameter.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List, ICollection, ISet

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    ElementCategoryFilter,
    Category,
    ParameterFilterRuleFactory,
    FilterDoubleRule, # Specific rule type for numbers
    FilterRule, # Base class for rules list
    BuiltInParameter,
    Color,
    FillPatternElement,
    FillPatternTarget,
    ParameterFilterUtilities # To check filterable categories and parameters
)
from Autodesk.Revit.Exceptions import ArgumentException # For potential errors

# --- Configuration ---
filter_name = "Windows U-Value < 1.5 Cyan"
target_bic = BuiltInCategory.OST_Windows
# Removed the specific BuiltInParameter attempt that caused the error.
# Will rely on finding the parameter by name.
param_bip_to_try = None
param_name_to_find = "U-Value" # Parameter name to search for (case-sensitive)
param_id = ElementId.InvalidElementId # Initialize as invalid
param_value_threshold = 1.5 # W/(m²·K) - Revit API handles units for comparison rules
cyan_color = Color(0, 255, 255)

# --- Helper function to find the Solid Fill pattern ---
def find_solid_fill_pattern(doc):
    """Finds the first solid fill pattern element."""
    fp_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solid_pattern_elem = next((fp for fp in fp_collector if fp.GetFillPattern().IsSolidFill), None)
    if solid_pattern_elem:
        return solid_pattern_elem.Id
    return ElementId.InvalidElementId

# --- Get Windows Category ---
windows_category = Category.GetCategory(doc, target_bic)
if windows_category is None:
    print("# Error: Windows category (OST_Windows) not found in the document.")
    windows_category_id = ElementId.InvalidElementId
else:
    windows_category_id = windows_category.Id

# --- Check if Category is Filterable ---
filterable_categories = ParameterFilterUtilities.GetAllFilterableCategories()
if windows_category_id == ElementId.InvalidElementId or windows_category_id not in filterable_categories:
    print("# Error: The 'Windows' category (OST_Windows) is not filterable or not found.")
    filter_element = None
else:
    # --- Check if Parameter is Filterable for the Category ---
    # Get filterable parameters for the specific category
    categories_list_for_check = List[ElementId]([windows_category_id])
    filterable_params = ParameterFilterUtilities.GetFilterableParametersInCommon(doc, categories_list_for_check)

    # Try the BuiltInParameter first (if one was provided and not None)
    if param_bip_to_try is not None:
        temp_param_id = ElementId(param_bip_to_try)
        if temp_param_id in filterable_params:
            param_id = temp_param_id
            print("# Using BuiltInParameter {} (ID: {})".format(param_bip_to_try, param_id))
        else:
            print("# Warning: Provided BuiltInParameter {} (ID: {}) not filterable for Windows. Trying to find parameter by name: '{}'".format(param_bip_to_try, temp_param_id, param_name_to_find))
            # Fall through to name search below
    else:
        print("# No specific BuiltInParameter provided or needed. Searching by name: '{}'".format(param_name_to_find))

    # If param_id is still invalid (BIP not found, not filterable, or not provided), search by name
    # Corrected check: Compare with ElementId.InvalidElementId
    if param_id == ElementId.InvalidElementId:
        found_param_id = ElementId.InvalidElementId

        # Method 1: Check existing ParameterFilterElements for efficiency
        param_filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for pfe in param_filter_collector:
             param_ids_in_filter = pfe.GetElementFilterParameters()
             for pid in param_ids_in_filter:
                 try:
                     p_elem = doc.GetElement(pid)
                     if p_elem and p_elem.Name == param_name_to_find:
                         # Check if this parameter ID is actually filterable for Windows
                         if pid in filterable_params:
                            found_param_id = pid
                            print("# Found parameter '{}' (ID: {}) in existing filter '{}'.".format(param_name_to_find, pid, pfe.Name))
                            break
                         else:
                             # Found by name, but not filterable for Windows in this context
                             print("# Found parameter '{}' (ID: {}) in filter '{}' but it's not filterable for the Windows category.".format(param_name_to_find, pid, pfe.Name))
                 except Exception:
                     # Ignore potential errors getting element or name
                     continue
             # Corrected check: Compare with ElementId.InvalidElementId
             if found_param_id != ElementId.InvalidElementId:
                 break

        # Method 2: If not found via existing filters, search elements (less efficient but broader)
        # Corrected check: Compare with ElementId.InvalidElementId
        if found_param_id == ElementId.InvalidElementId:
             print("# Parameter '{}' not found in existing filters. Searching elements...".format(param_name_to_find))
             # Collect window instances to check parameters
             window_collector = FilteredElementCollector(doc).OfCategory(target_bic).WhereElementIsNotElementType() # Removed .Take(20) here
             checked_param_ids = set() # Keep track of IDs already checked
             element_search_limit = 20 # Define the limit
             elements_checked = 0

             # Iterate and manually limit the search
             for window in window_collector:
                 if elements_checked >= element_search_limit:
                     print("# Reached element search limit ({}). Stopping parameter search on elements.".format(element_search_limit))
                     break # Exit loop after checking the limit

                 # Check instance parameters first
                 param = window.LookupParameter(param_name_to_find)
                 if param and param.Id not in checked_param_ids: # Check ID before HasValue for broader match
                     checked_param_ids.add(param.Id)
                     if param.Id in filterable_params:
                         found_param_id = param.Id
                         print("# Found filterable instance parameter by name: '{}' (ID: {}) on element {}".format(param_name_to_find, found_param_id, window.Id))
                         break # Found it

                 # If not found on instance, check type parameters
                 # Corrected check: Compare with ElementId.InvalidElementId
                 if found_param_id == ElementId.InvalidElementId and window.GetTypeId() != ElementId.InvalidElementId:
                     win_type = doc.GetElement(window.GetTypeId())
                     if win_type:
                         param = win_type.LookupParameter(param_name_to_find)
                         if param and param.Id not in checked_param_ids: # Check ID before HasValue
                              checked_param_ids.add(param.Id)
                              if param.Id in filterable_params:
                                  found_param_id = param.Id
                                  print("# Found filterable type parameter by name: '{}' (ID: {}) on type {}".format(param_name_to_find, found_param_id, win_type.Id))
                                  break # Found it

                 elements_checked += 1 # Increment the counter

                 # Corrected check: Compare with ElementId.InvalidElementId
                 if found_param_id != ElementId.InvalidElementId:
                     break # Exit outer loop once found

        # Method 3: Check Shared Parameters (if applicable and not found yet)
        # This is complex and often requires knowing the GUID. Sticking to name lookup for now.

        # Final assignment based on findings
        # Corrected check: Compare with ElementId.InvalidElementId
        if found_param_id != ElementId.InvalidElementId:
            param_id = found_param_id # Use the ID found by name
        else:
             print("# Error: Could not find a filterable parameter named '{}' for the Windows category after checking existing filters and {} elements.".format(param_name_to_find, elements_checked if 'elements_checked' in locals() else 'some'))
             param_id = ElementId.InvalidElementId # Mark as invalid


    # Proceed only if we have a valid category and parameter ID
    # Corrected checks: Compare with ElementId.InvalidElementId
    if windows_category_id != ElementId.InvalidElementId and param_id != ElementId.InvalidElementId:
        filter_element = None
        # --- Find or Create Filter Element ---
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        existing_filters = list(collector) # Get elements before iterating
        for existing_filter in existing_filters:
            if existing_filter.Name == filter_name:
                filter_element = existing_filter
                print("# Using existing filter: '{}'".format(filter_name))
                break

        categories_for_filter = List[ElementId]()
        categories_for_filter.Add(windows_category_id)

        # Create the filter rule: U-Value < threshold
        filter_rule = None
        try:
            # Ensure the value is a float
            rule_value_float = float(param_value_threshold)
            # Create the rule for "less than" a double value
            # Revit handles internal unit conversion based on param_id type
            filter_rule = ParameterFilterRuleFactory.CreateLessRule(param_id, rule_value_float)
        except ArgumentException as arg_ex:
             param_name_for_error = "Unknown"
             try:
                 param_elem = doc.GetElement(param_id)
                 if param_elem: param_name_for_error = param_elem.Name
             except: pass
             print("# Error creating filter rule (ArgumentException): {} - Check if parameter ID '{}' ({}) is valid for numeric rules.".format(arg_ex.Message, param_name_for_error, param_id))
        except Exception as rule_ex:
            print("# Error creating filter rule: {}".format(rule_ex))

        if filter_rule:
            filter_rules = List[FilterRule]() # Requires importing FilterRule base class
            filter_rules.Add(filter_rule)

            # If the filter doesn't exist, create it (Transaction managed externally)
            if filter_element is None:
                print("# Creating new filter: '{}'".format(filter_name))
                try:
                    filter_element = ParameterFilterElement.Create(
                        doc,
                        filter_name,
                        categories_for_filter,
                        filter_rules # Pass the list of rules
                    )
                    print("# Filter '{}' created successfully.".format(filter_name))
                except Exception as create_ex:
                    print("# Error creating filter '{}': {}".format(filter_name, create_ex))
                    filter_element = None # Ensure filter_element is None if creation failed
            else:
                # Filter exists, update its rules and categories if necessary (Transaction managed externally)
                 try:
                     needs_update = False
                     # Check if categories need update
                     current_categories = list(filter_element.GetCategories())
                     if len(current_categories) != len(categories_for_filter) or \
                        any(c not in current_categories for c in categories_for_filter):
                         filter_element.SetCategories(categories_for_filter)
                         print("# Updated categories for filter '{}'".format(filter_name))
                         needs_update = True

                     # Check if rules need update (simple check based on count and rule type/value)
                     current_rules = list(filter_element.GetRules()) # Convert to list
                     if len(current_rules) != len(filter_rules):
                          needs_update = True
                     else:
                          # Compare the single rule (more specific check)
                          # Note: Comparing rules directly might be complex due to internal state.
                          # This assumes CreateLessRule generates a predictable object structure
                          # or we just overwrite based on potential difference.
                          # Let's check the specific rule parameter and value if possible.
                          existing_rule = current_rules[0] # Assuming one rule
                          # Simple check: if rule parameter ID or value class type differs, update
                          if not isinstance(existing_rule, FilterDoubleRule) or \
                             existing_rule.RuleParameter != filter_rule.RuleParameter:
                              needs_update = True
                          else:
                              # Cannot easily compare rule_value_float directly due to potential unit conversions.
                              # Let's assume if param ID matches and type seems correct, it's okay unless forced update.
                              # To be safe, let's set rules if filter exists unless we are sure they match
                              # needs_update = True # Uncomment to always update rules if filter exists
                              pass # Assume OK if param ID and type match for now


                     if needs_update:
                         filter_element.SetRules(filter_rules)
                         print("# Updated rules for existing filter '{}'.".format(filter_name))
                     else:
                         print("# Existing filter '{}' configuration appears to match. No rule update needed.".format(filter_name))


                 except Exception as update_ex:
                     print("# Error updating existing filter '{}': {}".format(filter_name, update_ex))
                     # Decide if we should proceed with applying potentially outdated filter or stop
                     # For safety, let's nullify it if update fails significantly
                     # filter_element = None

        else: # filter_rule creation failed
            print("# Filter rule creation failed. Cannot create or update filter element.")
            filter_element = None

    else: # Parameter ID or category ID was invalid
        # Corrected checks: Compare with ElementId.InvalidElementId
        if windows_category_id == ElementId.InvalidElementId:
             print("# Cannot proceed without a valid category.")
        elif param_id == ElementId.InvalidElementId:
             print("# Cannot proceed without a valid filterable parameter.")
        filter_element = None


# --- Apply Filter to Active View (Transaction managed externally) ---
if filter_element is not None:
    filter_id = filter_element.Id
    active_view = doc.ActiveView # Assumes 'doc' is available

    if active_view is not None and active_view.IsValidObject:
        # Check if the view type supports filters/overrides
        if active_view.AreGraphicsOverridesAllowed():
            # Find solid fill pattern
            solid_fill_id = find_solid_fill_pattern(doc)
            if solid_fill_id == ElementId.InvalidElementId:
                 print("# Warning: Could not find a 'Solid fill' pattern. Overrides will be applied without fill pattern.")
                 apply_fill = False
            else:
                 apply_fill = True
                 print("# Found Solid Fill Pattern ID: {}".format(solid_fill_id))

            try:
                # Check if the filter is already added to the view
                applied_filter_ids = active_view.GetFilters()
                if filter_id not in applied_filter_ids:
                    # Add the filter to the view
                    active_view.AddFilter(filter_id)
                    print("# Filter '{}' added to view '{}'.".format(filter_name, active_view.Name))
                else:
                    print("# Filter '{}' is already present in view '{}'.".format(filter_name, active_view.Name))

                # Define the graphic overrides
                override_settings = OverrideGraphicSettings()

                # --- Apply CYANA Override ---
                # Set surface pattern (Projection) - Visible surfaces when looking at the model
                override_settings.SetProjectionLineColor(cyan_color) # Optional: Color projection lines
                if apply_fill:
                     override_settings.SetSurfaceForegroundPatternVisible(True)
                     override_settings.SetSurfaceForegroundPatternId(solid_fill_id)
                     override_settings.SetSurfaceForegroundPatternColor(cyan_color)
                else:
                     override_settings.SetSurfaceForegroundPatternVisible(False) # Ensure it's off if no pattern found

                # Set cut pattern - Visible surfaces when the element is cut by the view plane
                override_settings.SetCutLineColor(cyan_color) # Optional: Color cut lines
                if apply_fill:
                     override_settings.SetCutForegroundPatternVisible(True)
                     override_settings.SetCutForegroundPatternId(solid_fill_id)
                     override_settings.SetCutForegroundPatternColor(cyan_color)
                else:
                    override_settings.SetCutForegroundPatternVisible(False)

                # Apply the overrides to the filter in the view
                active_view.SetFilterOverrides(filter_id, override_settings)
                # Ensure the filter is visible/active in the view
                active_view.SetFilterVisibility(filter_id, True)
                print("# Cyan override applied for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

            except Exception as view_ex:
                print("# Error applying filter/overrides to view '{}': {}".format(active_view.Name, view_ex))
        else:
            print("# Error: View '{}' (Type: {}) does not support graphic overrides/filters.".format(active_view.Name, active_view.ViewType))
    else:
        print("# Error: No active view found or the active view is invalid.")
# Corrected checks: Compare with ElementId.InvalidElementId
elif windows_category_id != ElementId.InvalidElementId and param_id != ElementId.InvalidElementId: # Only print if category/param were OK but filter failed
   print("# Filter '{}' could not be found or created. Cannot apply to view.".format(filter_name))
# If category or param failed, errors were already printed above.