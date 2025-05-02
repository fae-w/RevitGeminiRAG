# Purpose: This script duplicates a primary Revit view as dependent views, adding quadrant suffixes to their names.

# Purpose: This script duplicates a primary Revit view as dependent views, adding quadrant suffixes to their names (NE, NW, SE, SW).

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ElementId,
    ViewDuplicateOption,
    ViewPlan # Although not strictly necessary for finding by name, useful for context
)
import sys # For error reporting (optional)

# --- Configuration ---
primary_view_name = "Level 1 Floor Plan"
quadrant_suffixes = ["NE", "NW", "SE", "SW"] # Quadrants to create

# --- Find the primary view ---
primary_view = None
collector = FilteredElementCollector(doc).OfClass(View)
# Ensure it's not a template and matches the name
for view in collector:
    if not view.IsTemplate and view.Name == primary_view_name:
        # Basic check if it's a plan view, as dependent views are common for them
        if isinstance(view, ViewPlan):
            primary_view = view
            break
        else:
             # Found by name, but maybe not the right type? Continue searching just in case.
             # If this is the only match, we'll use it but might warn later.
             primary_view = view


# --- Process the primary view ---
if primary_view:
    # Optional: Add a warning if the found view isn't a typical plan view
    if not isinstance(primary_view, ViewPlan):
        print("# Warning: Found view '{}' is not a standard Plan View (Type: {}). Dependent view creation might behave unexpectedly.".format(primary_view_name, primary_view.GetType().Name))

    created_views_count = 0
    errors = []

    for suffix in quadrant_suffixes:
        new_view_name = "{} - {}".format(primary_view.Name, suffix)

        # Check if a view with this name already exists
        existing_view_found = False
        name_check_collector = FilteredElementCollector(doc).OfClass(View)
        for v_check in name_check_collector:
            if not v_check.IsTemplate and v_check.Name == new_view_name:
                existing_view_found = True
                break
        if existing_view_found:
            errors.append("# Skipping: A view named '{}' already exists.".format(new_view_name))
            continue # Skip to the next quadrant

        try:
            # Check if duplication as dependent is possible
            if primary_view.CanViewBeDuplicated(ViewDuplicateOption.AsDependent):
                # Duplicate the view as dependent
                new_view_id = primary_view.Duplicate(ViewDuplicateOption.AsDependent)

                if new_view_id != ElementId.InvalidElementId:
                    # Get the newly created view element
                    dependent_view = doc.GetElement(new_view_id)
                    if dependent_view:
                        try:
                            # Rename the new dependent view
                            dependent_view.Name = new_view_name
                            created_views_count += 1
                            # print("# Successfully created and renamed: '{}'".format(new_view_name)) # Optional debug log
                        except Exception as rename_ex:
                            errors.append("# Error renaming view (ID: {}) to '{}': {}".format(new_view_id, new_view_name, rename_ex))
                            # Optionally try to delete the partially created view if renaming fails? Outside scope.
                    else:
                        # This case should be rare if Duplicate returned a valid ID
                        errors.append("# Error: Failed to retrieve Element for newly created dependent view ID: {} (Suffix: '{}').".format(new_view_id, suffix))
                else:
                    # Duplicate method returned InvalidElementId
                    errors.append("# Error: View.Duplicate(AsDependent) returned InvalidElementId for view '{}' (Suffix: '{}').".format(primary_view_name, suffix))
            else:
                # If CanViewBeDuplicated is false, report it and stop trying for this view
                errors.append("# Error: Primary view '{}' reported that it cannot be duplicated as dependent. Stopping.".format(primary_view.Name))
                break # Stop processing quadrants for this view

        except Exception as e:
            errors.append("# Error creating/renaming dependent view for suffix '{}' from view '{}': {}".format(suffix, primary_view_name, e))
            # Optional: Include more details like exception type
            # errors.append("#   Exception Type: {}".format(type(e).__name__))

    # --- Report Results ---
    print("# Created {} dependent views for '{}'.".format(created_views_count, primary_view_name))
    if errors:
        print("# Encountered errors during dependent view creation:")
        for error in errors:
            print(error)

else:
    print("# Error: Primary view named '{}' not found or is not a suitable view type.".format(primary_view_name))