# Purpose: This script copies view filters and their graphic overrides from the active floor plan view to other floor plan views on the same level.

# Purpose: This script copies view filters, overrides, and visibility settings from the active floor plan view to other floor plan views on the same level.

﻿# Mandatory Imports
import clr
clr.AddReference('System.Collections')
# from System.Collections.Generic import ICollection, Dictionary # Using Python dict

# Revit API Imports
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Required for UIDocument if needed, although not directly used here
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewPlan,
    ViewType,
    Level,
    ElementId,
    ParameterFilterElement,
    OverrideGraphicSettings,
    BuiltInParameter,
    Transaction # Although transaction handling is external, good practice to import if used internally sometimes
)
# Note: Transaction will not be used as per constraints.

# --- Script Core Logic ---

# Get active view (assuming 'doc' is pre-defined)
active_view = doc.ActiveView

# Validate active view
active_view_valid = False
active_level = None
active_level_id = ElementId.InvalidElementId

if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, ViewPlan) or active_view.ViewType != ViewType.FloorPlan:
    print("# Error: Active view '{}' is not a Floor Plan.".format(active_view.Name))
elif active_view.IsTemplate:
    print("# Error: Active view '{}' is a template. Select a non-template project view.".format(active_view.Name))
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: Active view '{}' does not support Visibility/Graphics Overrides.".format(active_view.Name))
else:
    # Active view seems to be a valid candidate, now check its level
    try:
        level_param = active_view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL)
        if level_param and level_param.HasValue:
             param_level_id = level_param.AsElementId()
             if param_level_id and param_level_id != ElementId.InvalidElementId:
                 fetched_level = doc.GetElement(param_level_id)
                 if fetched_level and isinstance(fetched_level, Level):
                     active_level = fetched_level
                     active_level_id = active_level.Id
                     active_view_valid = True # View is valid and level found
                 else:
                      print("# Error: Could not find a valid Level element for ID {} associated with active view '{}'.".format(param_level_id, active_view.Name))
        else:
             print("# Error: Active view '{}' does not have a value for the PLAN_VIEW_LEVEL parameter.".format(active_view.Name))

    except Exception as lvl_ex:
        print("# Error accessing level parameter for active view '{}': {}".format(active_view.Name, lvl_ex))

    if not active_level and active_view_valid: # If level determination failed after basic view checks passed
         print("# Error: Could not determine the Level associated with the active view '{}'.".format(active_view.Name))
         active_view_valid = False # Mark as invalid if level is crucial and not found


# --- Main processing block ---
if active_view_valid and active_level:
    print("# Active view: '{}' on Level: '{}'".format(active_view.Name, active_level.Name))

    # Get filters, overrides, and visibility from the active view
    active_filters_data = {} # Python dictionary { filter_id: {'overrides': OverrideGraphicSettings, 'visibility': bool} }
    filter_ids_collection = None
    try:
        filter_ids_collection = active_view.GetFilters() # ICollection<ElementId>

        if not filter_ids_collection or filter_ids_collection.Count == 0:
            print("# Info: Active view '{}' has no filters applied. Nothing to copy.".format(active_view.Name))
            active_filters_data = None # Signal no filters to copy
        else:
            print("# Found {} filters on active view '{}'. Retrieving settings...".format(filter_ids_collection.Count, active_view.Name))
            retrieved_count = 0
            skipped_retrieval = 0
            for filter_id in filter_ids_collection:
                filter_elem = None # Define outside try block for error message
                try:
                    filter_elem = doc.GetElement(filter_id)
                    # Ensure it's a ParameterFilterElement (rule-based or selection-based)
                    if not filter_elem or not isinstance(filter_elem, ParameterFilterElement):
                         # print("# Info: Skipping ID {} - not a ParameterFilterElement.".format(filter_id))
                         skipped_retrieval += 1
                         continue

                    overrides = active_view.GetFilterOverrides(filter_id)
                    visibility = active_view.GetFilterVisibility(filter_id)
                    # Store a copy of overrides to avoid modifying the original if needed later
                    override_copy = OverrideGraphicSettings(overrides)
                    active_filters_data[filter_id] = {'overrides': override_copy, 'visibility': visibility}
                    retrieved_count += 1
                except Exception as e_filter:
                    filter_name = filter_elem.Name if filter_elem else "ID: {}".format(filter_id)
                    print("# Warning: Could not get settings for filter '{}' (ID: {}) on active view: {}".format(filter_name, filter_id, e_filter))
                    skipped_retrieval += 1

            if retrieved_count > 0:
                 print("# Successfully retrieved settings for {} filter(s).".format(retrieved_count)) # Fixed syntax error here
                 if skipped_retrieval > 0:
                      print("# Skipped retrieving settings for {} item(s).".format(skipped_retrieval))
            else:
                 print("# Info: No valid ParameterFilterElement settings could be retrieved from the active view.")
                 active_filters_data = None # Signal no filters to copy

    except Exception as e_get_filters:
        print("# Error retrieving filters from active view '{}': {}".format(active_view.Name, e_get_filters))
        active_filters_data = None # Signal error or no filters


    # --- Apply filters to target views ---
    if active_filters_data: # Proceed only if we have filter data to copy
        print("# Searching for other Floor Plan views on Level '{}'...".format(active_level.Name))

        # Find target views: Floor Plans on the same level, excluding the active view and templates
        target_views = []
        all_views = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()

        for view in all_views:
            # Basic checks
            if view.Id == active_view.Id: continue # Skip active view
            if view.IsTemplate: continue # Skip templates
            if view.ViewType != ViewType.FloorPlan: continue # Ensure it's a floor plan (redundant with OfClass(ViewPlan) but safe)
            if not view.AreGraphicsOverridesAllowed(): continue # Skip views that don't allow overrides

            # Check level
            try:
                level_param = view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL)
                if level_param and level_param.HasValue:
                    view_level_id = level_param.AsElementId()
                    if view_level_id == active_level_id:
                        target_views.append(view) # Add to list if level matches
            except Exception as tv_lvl_ex:
                 print("# Warning: Could not check level for view '{}' (ID: {}): {}".format(view.Name, view.Id, tv_lvl_ex))


        if not target_views:
            print("# Info: No other applicable Floor Plan views found on Level '{}'.".format(active_level.Name))
        else:
            print("# Found {} target Floor Plan view(s) on Level '{}'. Applying filter settings...".format(len(target_views), active_level.Name))
            applied_count = 0
            skipped_views = []

            # Iterate through target views and apply filters
            for target_view in target_views:
                try:
                    print("# Applying settings to view: '{}'...".format(target_view.Name))
                    filters_applied_to_view = 0
                    for filter_id, settings in active_filters_data.items():
                        # Ensure the filter exists in the document (should always be true if retrieved)
                        filter_elem = doc.GetElement(filter_id)
                        if not filter_elem or not isinstance(filter_elem, ParameterFilterElement):
                           # print("# Info: Skipping filter ID {} for view '{}' as it's not a valid ParameterFilterElement in the document.".format(filter_id, target_view.Name))
                           continue

                        # Add filter if not already present
                        if not target_view.IsFilterApplied(filter_id):
                            try:
                                target_view.AddFilter(filter_id)
                                # print("# - Added filter '{}' (ID: {})".format(filter_elem.Name, filter_id))
                            except Exception as add_err:
                                print("#   - Warning: Failed to add filter '{}' (ID: {}) to view '{}': {}".format(filter_elem.Name, filter_id, target_view.Name, add_err))
                                continue # Skip setting overrides/visibility if filter couldn't be added

                        # Apply overrides and visibility
                        try:
                            target_view.SetFilterOverrides(filter_id, settings['overrides'])
                            target_view.SetFilterVisibility(filter_id, settings['visibility'])
                            filters_applied_to_view += 1
                            # print("#   - Applied overrides/visibility for filter '{}'".format(filter_elem.Name))
                        except Exception as set_err:
                            print("#   - Warning: Failed to set overrides/visibility for filter '{}' (ID: {}) on view '{}': {}".format(filter_elem.Name, filter_id, target_view.Name, set_err))

                    if filters_applied_to_view > 0:
                        print("# - Successfully applied settings for {} filter(s) to view '{}'.".format(filters_applied_to_view, target_view.Name))
                        applied_count += 1
                    else:
                        print("# - No filter settings were successfully applied to view '{}' (possibly due to errors adding filters or setting overrides).".format(target_view.Name))
                        skipped_views.append(target_view.Name)

                except Exception as e_apply:
                    print("# Error applying filters to view '{}' (ID: {}): {}".format(target_view.Name, target_view.Id, e_apply))
                    skipped_views.append(target_view.Name)

            print("# --- Summary ---")
            print("# Applied filter settings to {} view(s).".format(applied_count))
            if skipped_views:
                print("# Skipped or encountered errors applying settings to views: {}".format(", ".join(list(set(skipped_views))))) # Use set to remove duplicates

    elif active_filters_data is None and filter_ids_collection and filter_ids_collection.Count > 0:
         # Case where filters existed but none could be retrieved
         print("# Processing skipped: No valid filter settings were retrieved from the active view.")
    elif active_filters_data is None:
         # Case where active view had no filters initially
         print("# Processing skipped: Active view had no filters to copy.")


elif not active_view_valid:
    # Error messages were already printed during the validation phase
    print("# Processing aborted due to invalid active view or inability to determine its level.")