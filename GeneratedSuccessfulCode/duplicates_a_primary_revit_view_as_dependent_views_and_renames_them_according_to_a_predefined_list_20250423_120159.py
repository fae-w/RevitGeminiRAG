# Purpose: This script duplicates a primary Revit view as dependent views and renames them according to a predefined list.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ElementId,
    ViewDuplicateOption,
    ViewPlan # Although not directly used for duplication, good practice if interacting with plan properties later
)
import System # Required for Exception handling

# --- Configuration ---
primary_view_name = "L1 - Overall Site Plan"
dependent_view_names = ['Block 35 NE', 'Block 35 SW', 'Block 43 NE', 'Block 43 SW']
duplicate_option = ViewDuplicateOption.AsDependent

# --- Find the Primary View ---
primary_view = None
view_collector = FilteredElementCollector(doc).OfClass(View)

# Iterate through views to find the primary one by name
for view in view_collector:
    # Check if it's a ViewPlan or similar plannable view if needed, but name match is primary
    if view.Name == primary_view_name and not view.IsTemplate:
        primary_view = view
        break

# --- Duplicate the View for each specified name ---
if primary_view is None:
    print("# Error: Primary view named '{}' not found.".format(primary_view_name))
else:
    # Check if the primary view can be duplicated as dependent
    if not primary_view.CanViewBeDuplicated(duplicate_option):
        print("# Error: Primary view '{}' (ID: {}) cannot be duplicated As Dependent.".format(
            primary_view.Name,
            primary_view.Id
        ))
    else:
        created_view_count = 0
        for new_name in dependent_view_names:
            try:
                # Duplicate the view
                new_view_id = primary_view.Duplicate(duplicate_option)

                if new_view_id != ElementId.InvalidElementId:
                    new_view = doc.GetElement(new_view_id)
                    if new_view:
                        try:
                            # Attempt to rename the new dependent view
                            new_view.Name = new_name
                            print("# Successfully created and renamed dependent view: '{}' (ID: {})".format(
                                new_view.Name,
                                new_view_id
                            ))
                            created_view_count += 1
                        except System.Exception as rename_ex:
                            default_name = "Unknown (original name unavailable after rename failure)"
                            try:
                                # Try getting the name again in case it partially worked or reverted
                                current_name = doc.GetElement(new_view_id).Name
                                default_name = current_name if current_name else default_name
                            except:
                                pass # Keep default error name
                            print("# Successfully created dependent view (ID: {}), but failed to rename to '{}'. Current name: '{}'. Error: {}".format(
                                new_view_id,
                                new_name,
                                default_name,
                                str(rename_ex)
                            ))
                            # Still count as created, even if renaming failed
                            created_view_count += 1
                    else:
                        print("# Error: Duplication of view '{}' seemed to succeed (returned ID {}), but failed to retrieve the new view element.".format(
                             primary_view.Name, new_view_id
                        ))
                else:
                    print("# Error: Duplication of view '{}' failed for dependent name '{}', returned InvalidElementId.".format(
                        primary_view.Name,
                        new_name
                    ))

            except System.Exception as e:
                print("# Error duplicating view '{}' for dependent name '{}': {}".format(
                    primary_view.Name,
                    new_name,
                    str(e)
                ))

        # Final summary comment
        print("# --- Summary ---")
        print("# Attempted to create {} dependent views from '{}'.".format(len(dependent_view_names), primary_view_name))
        print("# Successfully created {} views (check logs above for renaming issues).".format(created_view_count))
        print("# Note: Crop regions for these dependent views have NOT been automatically adjusted based on grids.")
        print("# Manual adjustment or further scripting targeting specific grids is required to set the crop boxes.")