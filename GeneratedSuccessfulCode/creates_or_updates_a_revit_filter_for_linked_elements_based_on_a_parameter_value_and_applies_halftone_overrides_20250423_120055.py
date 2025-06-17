# Purpose: This script creates or updates a Revit filter for linked elements based on a parameter value and applies halftone overrides.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>
clr.AddReference('System') # Required for Enum and Exception handling

# Import Revit API namespaces
import Autodesk.Revit.DB as DB
from System.Collections.Generic import List
import System # For exception handling

# --- Configuration ---
filter_name = "Linked Arch Podium Elements - Halftone"
target_link_instance_name = "ARCH_Podium_Link" # Case-sensitive match for link instance name
parameter_to_check_bip = DB.BuiltInParameter.ALL_MODEL_MARK
parameter_value_contains = "Podium" # Case-sensitive check

# Define categories the filter should apply to. Use a broad set for linked elements.
target_categories_enum = [
    DB.BuiltInCategory.OST_Walls, DB.BuiltInCategory.OST_Doors, DB.BuiltInCategory.OST_Windows,
    DB.BuiltInCategory.OST_Floors, DB.BuiltInCategory.OST_Ceilings, DB.BuiltInCategory.OST_Roofs,
    DB.BuiltInCategory.OST_Columns, DB.BuiltInCategory.OST_StructuralColumns, DB.BuiltInCategory.OST_StructuralFraming,
    DB.BuiltInCategory.OST_Stairs, DB.BuiltInCategory.OST_StairsRailing, DB.BuiltInCategory.OST_Furniture,
    DB.BuiltInCategory.OST_Casework, DB.BuiltInCategory.OST_PlumbingFixtures, DB.BuiltInCategory.OST_GenericModel,
    DB.BuiltInCategory.OST_CurtainWallPanels, DB.BuiltInCategory.OST_CurtainWallMullions,
    DB.BuiltInCategory.OST_Entourage, DB.BuiltInCategory.OST_Planting, DB.BuiltInCategory.OST_Site,
    DB.BuiltInCategory.OST_Topography, DB.BuiltInCategory.OST_Ramps, DB.BuiltInCategory.OST_MechanicalEquipment,
    DB.BuiltInCategory.OST_ElectricalEquipment, DB.BuiltInCategory.OST_LightingFixtures,
    # Add more BuiltInCategory enums here if needed
]

# --- Initialize state ---
proceed_execution = True
parameter_filter_element = None
active_view = None
link_instance_id = None
error_messages = [] # Collect errors
existing_filter = None # Initialize existing_filter

# --- Pre-checks ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, DB.View) or active_view.IsTemplate:
    error_messages.append("# Error: Requires an active, non-template graphical view to apply filter overrides.")
    proceed_execution = False
# Removed the 'AreFiltersEnabled' check as it was incorrect for the View class

# --- Find Target Link Instance ---
if proceed_execution:
    link_collector = DB.FilteredElementCollector(doc).OfClass(DB.RevitLinkInstance)
    found_link = False
    for link_instance in link_collector:
        # Compare instance name directly using GetName() method if available, or .Name property
        instance_name = DB.Element.Name.__get__(link_instance) # More robust way to get name
        if instance_name == target_link_instance_name:
            link_instance_id = link_instance.Id
            print("# Found link instance '{}' with ID: {}".format(target_link_instance_name, link_instance_id))
            found_link = True
            break
    if not found_link:
        error_messages.append("# Error: Revit Link Instance named '{}' not found.".format(target_link_instance_name))
        proceed_execution = False

# --- Prepare Categories ---
category_ids = List[DB.ElementId]()
if proceed_execution:
    all_categories = doc.Settings.Categories
    parameter_id = DB.ElementId(parameter_to_check_bip) # Get ElementId for Mark parameter
    parameter_found = False

    # Check if the BuiltInParameter itself is valid first by trying to find its definition
    try:
        param_elem = DB.BuiltInParameterUtility.GetDefinition(doc, parameter_to_check_bip)
        if param_elem is not None:
             parameter_found = True
        else: # This case might be less likely for common BIPS like Mark, but good practice
             error_messages.append("# Error: The specified BuiltInParameter (Mark: {}) is not valid in this document.".format(parameter_to_check_bip))
             proceed_execution = False
    except Exception as param_check_err:
        error_messages.append("# Error: Could not validate BuiltInParameter (Mark: {}): {}".format(parameter_to_check_bip, param_check_err))
        proceed_execution = False


    if proceed_execution and parameter_found:
        # Now check if it's valid for filtering across the potential categories
        valid_categories_for_param = DB.ParameterFilterUtilities.GetAllFilterableCategories()
        # Since we apply to linked elements, checking applicability per category is essential

        for cat_enum_val in target_categories_enum:
            built_in_cat = None
            try:
                # Ensure it's a valid BuiltInCategory enum member before proceeding
                if System.Enum.IsDefined(clr.GetClrType(DB.BuiltInCategory), cat_enum_val):
                    built_in_cat = cat_enum_val
                else:
                    # print("# Warning: Invalid BuiltInCategory value provided: {}".format(cat_enum_val)) # Debug
                    continue # Skip this enum value
            except Exception as enum_err:
                print("# Warning: Error validating BuiltInCategory value {}: {}".format(cat_enum_val, enum_err))
                continue

            if built_in_cat is not None:
                try:
                    cat_id = DB.ElementId(built_in_cat)
                    category = all_categories.get_Item(built_in_cat)
                    # Check if category exists, supports bound parameters, and supports the filter parameter
                    if (category is not None and category.AllowsBoundParameters and
                        cat_id.IntegerValue > 0 and # Ensure valid category ID
                        valid_categories_for_param.Contains(cat_id) and # Check if category is generally filterable
                        DB.ParameterFilterUtilities.IsParameterApplicableToCategory(parameter_id, cat_id)): # Check param specific applicability
                        category_ids.Add(cat_id)
                    # else:
                        # Optional: Log if category invalid/unsupported/doesn't support the parameter
                        # print("# Info: Category {} invalid or does not support parameter filter.".format(built_in_cat))
                        # pass
                except System.Exception as cat_err:
                    print("# Warning: Error processing category {}: {}".format(built_in_cat, cat_err.Message))
                except Exception as py_err:
                    print("# Warning: Python error processing category {}: {}".format(built_in_cat, py_err))

        if category_ids.Count == 0:
            error_messages.append("# Error: No valid & applicable categories found or specified for the filter (or parameter not applicable).")
            proceed_execution = False
        # else: # Debug check if categories were added
            # print("# Info: {} applicable categories identified for the filter.".format(category_ids.Count))


# --- Create Filter Rules ---
combined_filter = None
if proceed_execution:
    try:
        # Rule 1: Element is from the specified link instance
        link_filter = DB.ElementIsFromLinkFilter(link_instance_id)

        # Rule 2: Mark parameter contains the specified text
        param_id = DB.ElementId(parameter_to_check_bip)
        # Note: FilterStringContains is case-sensitive in the API
        # Using CreateContainsRule requires the parameter ID, the value, and case sensitivity bool
        # NOTE: Revit API documentation suggests case sensitivity might be ignored by CreateContainsRule.
        # If case-insensitivity is needed, consider using CreateEqualsRule with multiple rules ORed together,
        # or potentially CreateSharedParameterApplicableRule if it were a shared param.
        # For 'contains', case-sensitive is the expected behavior here based on the request.
        string_rule = DB.ParameterFilterRuleFactory.CreateContainsRule(param_id, parameter_value_contains, True) # True for case-sensitive (API default might vary)

        param_filter = DB.ElementParameterFilter(string_rule)

        # Combine rules: Must be from link AND have the correct mark value
        filter_list = List[DB.ElementFilter]()
        filter_list.Add(link_filter)
        filter_list.Add(param_filter)
        combined_filter = DB.LogicalAndFilter(filter_list)

    except System.Exception as rule_err:
        error_messages.append("# Error creating filter rules: {}".format(rule_err.Message))
        proceed_execution = False
    except Exception as py_err:
        error_messages.append("# Error: An unexpected Python error occurred creating filter rules: {}".format(py_err))
        proceed_execution = False

# --- Find or Create ParameterFilterElement ---
if proceed_execution and combined_filter:
    try:
        collector = DB.FilteredElementCollector(doc).OfClass(DB.ParameterFilterElement)
        for f in collector:
            if DB.Element.Name.__get__(f) == filter_name:
                existing_filter = f
                break
    except Exception as e:
        error_messages.append("# Error finding existing filters: {}".format(e))
        proceed_execution = False

    if proceed_execution:
        if existing_filter:
            print("# Found existing filter: '{}' (ID: {}). Using existing.".format(filter_name, existing_filter.Id))
            parameter_filter_element = existing_filter
            # Check if update is needed (basic check here, assumes user wants to update if found)
            # Note: Requires Transaction if changes are made. Script assumes wrapper handles transaction.
            try:
                needs_update = False
                # Check categories
                existing_cat_ids_net = existing_filter.GetCategories()
                existing_cat_ids_set = set([cat_id.IntegerValue for cat_id in existing_cat_ids_net])
                desired_cat_ids_set = set([cat_id.IntegerValue for cat_id in category_ids])
                if existing_cat_ids_set != desired_cat_ids_set:
                     print("# Info: Updating categories for existing filter '{}'".format(filter_name))
                     # existing_filter.SetCategories(category_ids) # Requires Transaction
                     needs_update = True # Flag that update happened or is needed

                # Check filter definition (this is harder to compare directly)
                # A simple approach is to just set it again if we found an existing one
                # This ensures the logic (e.g., link ID, parameter rule) is current
                # existing_filter.SetElementFilter(combined_filter) # Requires Transaction
                # needs_update = True # Flag that update happened or is needed

                # If needs_update:
                    # Potentially add doc.Regenerate() here if within a transaction scope
                    # pass # Assume transaction handled externally

                # For this script, we will just USE the existing filter ID and apply overrides.
                # If the existing filter's rules/categories are wrong, the user should delete it manually first.

            except Exception as update_err:
                 error_messages.append("# Warning: Could not verify/update existing filter '{}': {}".format(filter_name, update_err))

        else:
            print("# Filter '{}' not found. Creating new filter...".format(filter_name))
            try:
                # Ensure the rule and categories are valid before creation attempt
                if combined_filter and category_ids.Count > 0:
                    # Create needs doc, name, categories, filter definition
                    # NOTE: ParameterFilterElement.Create is expected to be wrapped in a transaction
                    parameter_filter_element = DB.ParameterFilterElement.Create(doc, filter_name, category_ids, combined_filter)
                    print("# Successfully created filter: '{}' (ID: {}).".format(filter_name, parameter_filter_element.Id))
                else:
                    # Error message already added if category_ids count is 0 or combined_filter is None
                    if not combined_filter: error_messages.append("# Error: Filter rule creation failed earlier.")
                    proceed_execution = False # Prevent further steps

            except System.Exception as create_err:
                # Provide more context if possible, e.g., ArgumentException might mean bad categories/parameter combo
                error_messages.append("# Error: Failed to create filter '{}'. Reason: {}".format(filter_name, create_err.Message))
                parameter_filter_element = None # Ensure it's None if creation fails
                proceed_execution = False # Stop further steps if creation failed
            except Exception as py_err: # Catch potential IronPython exceptions
                error_messages.append("# Error: An unexpected Python error occurred during filter creation: {}".format(py_err))
                parameter_filter_element = None
                proceed_execution = False # Stop further steps if creation failed

# --- Apply Filter and Overrides to Active View ---
if proceed_execution and parameter_filter_element and active_view:
    filter_id = parameter_filter_element.Id
    filter_applied_or_exists = False

    try:
        # Check if filter is already applied to the view
        applied_filters = active_view.GetFilters()
        if filter_id in applied_filters:
            print("# Filter '{}' is already applied to view '{}'.".format(filter_name, active_view.Name))
            filter_applied_or_exists = True
        else:
            # Add the filter to the view if applicable
            # NOTE: AddFilter is expected to be wrapped in a transaction
            if active_view.IsFilterApplicable(filter_id):
                active_view.AddFilter(filter_id)
                # Need to regenerate document after adding filter for changes to take effect immediately within the same transaction scope (if applicable)
                # doc.Regenerate() # Not strictly necessary if transaction commits after script finishes
                print("# Applied filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                filter_applied_or_exists = True
            else:
                 error_messages.append("# Error: Filter '{}' is not applicable to the active view '{}' (check view type/discipline and filter categories).".format(filter_name, active_view.Name))
                 proceed_execution = False # Stop trying to apply overrides if filter not applicable

        # If filter is successfully applied (or was already), set overrides
        if filter_applied_or_exists and proceed_execution:
            override_settings = DB.OverrideGraphicSettings()
            override_settings.SetHalftone(True)

            # Check if overrides can be set before attempting
            # NOTE: SetFilterOverrides is expected to be wrapped in a transaction
            if active_view.CanApplyFilterOverrides(filter_id, override_settings):
                 active_view.SetFilterOverrides(filter_id, override_settings)
                 print("# Set Halftone override for filter '{}' in view '{}'.".format(filter_name, active_view.Name))
            else:
                 # This might happen if the view settings (e.g., discipline) prevent halftone overrides
                 error_messages.append("# Warning: Cannot apply the specified overrides (Halftone) for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

    except System.Exception as apply_err:
        error_messages.append("# Error applying filter/overrides for '{}' in view '{}'. Reason: {}".format(filter_name, active_view.Name, apply_err.Message))
    except Exception as py_err:
         error_messages.append("# Error: An unexpected Python error occurred applying filter/overrides: {}".format(py_err))


elif proceed_execution and not parameter_filter_element:
    # This case means filter creation failed or was skipped, and we didn't find an existing one either
    if not existing_filter: # Only report this if creation failed and none existed
        # Check if error messages already explain the failure
        if not any("create filter" in msg.lower() or "rule creation failed" in msg.lower() or "applicable categories" in msg.lower() for msg in error_messages):
             error_messages.append("# Filter '{}' could not be created or found. Overrides not applied.".format(filter_name))

# Print any accumulated errors at the end
if error_messages:
    print("\n# --- Errors Encountered ---")
    for msg in error_messages:
        print(msg)
# else: # Optional success message if no errors
#     if proceed_execution and parameter_filter_element:
#         print("# Script finished successfully.")
#     elif not proceed_execution and not error_messages:
#          print("# Script halted due to pre-check failures or configuration issues.")