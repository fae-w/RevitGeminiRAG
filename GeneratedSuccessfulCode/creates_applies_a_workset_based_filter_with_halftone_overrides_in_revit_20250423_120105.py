# Purpose: This script creates/applies a workset-based filter with halftone overrides in Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>
clr.AddReference('System') # Required for Enum and Exception handling

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Workset,
    WorksetKind,
    FilteredWorksetCollector,
    WorksetId,
    ElementWorksetFilter,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    Category
)
from System.Collections.Generic import List
import System # For exception handling, Enum

# --- Configuration ---
filter_name = "Linked Arch Elements - Halftone"
target_workset_name = "Linked Arch Model"

# Define categories the filter should apply to.
target_categories_enum = [
    BuiltInCategory.OST_Walls, BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows,
    BuiltInCategory.OST_Floors, BuiltInCategory.OST_Ceilings, BuiltInCategory.OST_Roofs,
    BuiltInCategory.OST_Columns, BuiltInCategory.OST_StructuralColumns, BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_Stairs, BuiltInCategory.OST_StairsRailing, BuiltInCategory.OST_Furniture,
    BuiltInCategory.OST_Casework, BuiltInCategory.OST_PlumbingFixtures, BuiltInCategory.OST_GenericModel,
    BuiltInCategory.OST_CurtainWallPanels, BuiltInCategory.OST_CurtainWallMullions,
    # Add more BuiltInCategory enums here if needed
]

# --- Initialize state ---
proceed_execution = True
parameter_filter_element = None
active_view = None
error_messages = [] # Collect errors

# --- Pre-checks ---
if not doc.IsWorkshared:
    error_messages.append("# Error: Document is not workshared. Cannot create a workset-based filter.")
    proceed_execution = False

if proceed_execution:
    active_view = doc.ActiveView
    if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
        error_messages.append("# Error: Requires an active, non-template graphical view to apply filter overrides.")
        proceed_execution = False
    elif not active_view.AreFiltersEnabled:
         error_messages.append("# Error: Filters are not enabled in the active view '{}'.".format(active_view.Name))
         proceed_execution = False

# --- Find Target Workset ---
target_workset_id = None
if proceed_execution:
    workset_collector = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
    worksets = workset_collector.ToWorksets()
    found_ws = False
    for ws in worksets:
        # Case-insensitive comparison robust against None names
        ws_name = ws.Name
        if ws_name and ws_name.lower() == target_workset_name.lower():
            target_workset_id = ws.Id
            print("# Found workset '{}' with ID: {}".format(target_workset_name, target_workset_id))
            found_ws = True
            break
    if not found_ws:
        error_messages.append("# Error: Workset named '{}' not found.".format(target_workset_name))
        proceed_execution = False

# --- Prepare Categories ---
category_ids = List[ElementId]()
if proceed_execution:
    all_categories = doc.Settings.Categories
    for cat_enum_val in target_categories_enum:
        built_in_cat = None
        try:
            # Ensure it's a valid BuiltInCategory enum member before proceeding
            if System.Enum.IsDefined(clr.GetClrType(BuiltInCategory), cat_enum_val):
                 built_in_cat = cat_enum_val
            else:
                 print("# Warning: Invalid BuiltInCategory value provided: {}".format(cat_enum_val))
                 continue # Skip this enum value
        except Exception as enum_err:
             print("# Warning: Error validating BuiltInCategory value {}: {}".format(cat_enum_val, enum_err))
             continue

        if built_in_cat is not None:
            try:
                category = all_categories.get_Item(built_in_cat)
                # Check if category exists in the doc and supports bound parameters (needed for filters)
                if category is not None and category.AllowsBoundParameters and category.Id.IntegerValue > 0:
                    category_ids.Add(category.Id)
                # else:
                    # Optional: Log if category invalid/unsupported
                    # print("# Info: Category {} not found, invalid, or does not support filters.".format(built_in_cat))
                    # pass
            except System.Exception as cat_err:
                 print("# Warning: Error processing category {}: {}".format(built_in_cat, cat_err.Message))
            except Exception as py_err:
                 print("# Warning: Python error processing category {}: {}".format(built_in_cat, py_err))

    if category_ids.Count == 0:
        error_messages.append("# Error: No valid & applicable categories found or specified for the filter.")
        proceed_execution = False

# --- Create ElementWorksetFilter ---
workset_filter_rule = None
if proceed_execution:
    # Filter for elements *in* the specified workset (inverted=False)
    workset_filter_rule = ElementWorksetFilter(target_workset_id, False)
    if workset_filter_rule is None: # Should not happen if target_workset_id is valid, but check defensively
        error_messages.append("# Error: Failed to create ElementWorksetFilter.")
        proceed_execution = False

# --- Find or Create ParameterFilterElement ---
if proceed_execution:
    existing_filter = None
    try:
        collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in collector:
            if f.Name == filter_name:
                existing_filter = f
                break
    except Exception as e:
        error_messages.append("# Error finding existing filters: {}".format(e))
        proceed_execution = False

    if proceed_execution:
        if existing_filter:
            print("# Found existing filter: '{}' (ID: {}). Using existing.".format(filter_name, existing_filter.Id))
            parameter_filter_element = existing_filter
            # Optional: Could add logic here to check/update categories or rules if needed.
            # For now, just use the existing filter as found.
            # Check if existing filter's categories/rule match desired ones - complex check skipped for simplicity.

        else:
            print("# Filter '{}' not found. Creating new filter...".format(filter_name))
            try:
                # Ensure the rule is valid before creation attempt
                if workset_filter_rule and category_ids.Count > 0:
                    parameter_filter_element = ParameterFilterElement.Create(doc, filter_name, category_ids, workset_filter_rule)
                    print("# Successfully created filter: '{}' (ID: {}).".format(filter_name, parameter_filter_element.Id))
                else:
                    error_messages.append("# Error: Cannot create filter due to invalid rule or categories.")
                    proceed_execution = False # Prevent further steps

            except System.Exception as create_err:
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
            if active_view.IsFilterApplicable(filter_id):
                active_view.AddFilter(filter_id)
                print("# Applied filter '{}' to view '{}'.".format(filter_name, active_view.Name))
                filter_applied_or_exists = True
            else:
                 error_messages.append("# Error: Filter '{}' is not applicable to the active view '{}' (check view type/discipline and filter categories).".format(filter_name, active_view.Name))

        # If filter is successfully applied (or was already), set overrides
        if filter_applied_or_exists:
            override_settings = OverrideGraphicSettings()
            override_settings.SetHalftone(True)

            # Check if overrides can be set
            if active_view.CanApplyFilterOverrides(filter_id, override_settings):
                 active_view.SetFilterOverrides(filter_id, override_settings)
                 print("# Set Halftone override for filter '{}' in view '{}'.".format(filter_name, active_view.Name))
            else:
                 error_messages.append("# Warning: Cannot apply the specified overrides for filter '{}' in view '{}'.".format(filter_name, active_view.Name))

    except System.Exception as apply_err:
        error_messages.append("# Error applying filter/overrides for '{}' in view '{}'. Reason: {}".format(filter_name, active_view.Name, apply_err.Message))
    except Exception as py_err:
         error_messages.append("# Error: An unexpected Python error occurred applying filter/overrides: {}".format(py_err))


elif proceed_execution and not parameter_filter_element:
    # This case means filter creation failed or was skipped
    if not existing_filter: # Only report this if we didn't find an existing one either
        error_messages.append("# Filter '{}' could not be created or found. Overrides not applied.".format(filter_name))

# Print any accumulated errors at the end
if error_messages:
    print("\n# --- Errors Encountered ---")
    for msg in error_messages:
        print(msg)

# Final status message (optional)
# if proceed_execution and parameter_filter_element:
#    print("# Script finished successfully.")
# elif not proceed_execution:
#    print("# Script halted due to prerequisite errors.")