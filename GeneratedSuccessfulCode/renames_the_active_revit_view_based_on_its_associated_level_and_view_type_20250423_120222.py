# Purpose: This script renames the active Revit view based on its associated level and view type.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    View,
    Level,
    ElementId,
    BuiltInParameter
)

# --- Get the Active View ---
try:
    active_view = uidoc.ActiveView
    if not active_view:
        print("# Error: No active view found.")
        # Exit the script gracefully if there's no active view
        # In a real script, you might raise an exception or use sys.exit()
        # For pyRevit/RPS, just printing and not proceeding is often sufficient.
        active_view = None # Ensure it's None to skip further processing
except Exception as e:
    print("# Error accessing active view: {}".format(e))
    active_view = None # Ensure it's None

# --- Proceed only if an active view exists ---
if active_view:
    # --- Check if the view is a template ---
    if active_view.IsTemplate:
        print("# Info: Active view '{}' is a template. Skipping rename.".format(active_view.Name))
        active_view = None # Skip renaming templates

# --- Proceed only if it's a valid, non-template view ---
if active_view:
    level_name = None
    level_found = False
    original_name = active_view.Name

    # --- Get Associated Level Name ---
    try:
        # Try using the GenLevel property first (more direct for some views)
        level_element = active_view.GenLevel
        if level_element and isinstance(level_element, Level):
            level_name = level_element.Name
            level_found = True
        else:
            # Fallback: Try the PLAN_VIEW_LEVEL parameter (common for plans)
            level_param = active_view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL)
            if level_param and level_param.HasValue:
                level_id = level_param.AsElementId()
                if level_id and level_id != ElementId.InvalidElementId:
                    level_element_param = doc.GetElement(level_id)
                    if isinstance(level_element_param, Level):
                        level_name = level_element_param.Name
                        level_found = True

    except Exception as e:
        print("# Warning: Error trying to get associated level for view '{}': {}".format(original_name, e))
        # Continue without a level name if an error occurred

    # --- Get View Type Name ---
    view_type_name = "UnknownViewType" # Default
    try:
        view_type_enum = active_view.ViewType
        view_type_name = view_type_enum.ToString()
    except Exception as e:
        print("# Warning: Error trying to get view type for view '{}': {}".format(original_name, e))

    # --- Construct and Apply New Name (only if level was found) ---
    if level_found:
        # Construct the new name
        new_name = "{} - {}".format(level_name, view_type_name)

        # Check if renaming is necessary
        if original_name != new_name:
            try:
                # Attempt to rename the view
                active_view.Name = new_name
                print("# Renamed active view from '{}' to '{}'".format(original_name, new_name))
            except Exception as e_rename:
                print("# Error renaming view '{}' to '{}': {}".format(original_name, new_name, e_rename))
                # Possible reasons: Name already exists, invalid characters (though unlikely here), permissions
        else:
            print("# Info: Active view '{}' already has the desired name.".format(original_name))
    else:
        # If no level was found, do not rename and inform the user
        print("# Info: Could not find an associated Level for the active view '{}'. View not renamed.".format(original_name))

# --- End of Script ---