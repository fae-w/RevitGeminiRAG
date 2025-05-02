# Purpose: This script duplicates a specified Revit view as a dependent view.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ElementId,
    ViewDuplicateOption
)
import System # Required for Exception handling

# --- Configuration ---
target_view_name = "L1 - Block 43 Floor Plan"
duplicate_option = ViewDuplicateOption.AsDependent

# --- Find the View ---
view_to_duplicate = None
view_collector = FilteredElementCollector(doc).OfClass(View)

for view in view_collector:
    if view.Name == target_view_name and not view.IsTemplate:
        view_to_duplicate = view
        break

# --- Duplicate the View ---
if view_to_duplicate is None:
    print("# Error: View named '{}' not found.".format(target_view_name))
else:
    try:
        # Check if the view can be duplicated with the specified option
        if view_to_duplicate.CanViewBeDuplicated(duplicate_option):
            # Duplicate the view
            new_view_id = view_to_duplicate.Duplicate(duplicate_option)

            if new_view_id != ElementId.InvalidElementId:
                new_view = doc.GetElement(new_view_id)
                print("# Successfully duplicated view '{}' (ID: {}) as dependent. New view name: '{}', ID: {}.".format(
                    view_to_duplicate.Name,
                    view_to_duplicate.Id,
                    new_view.Name if new_view else "Unknown",
                    new_view_id
                ))
            else:
                print("# Error: Duplication of view '{}' (ID: {}) failed, returned InvalidElementId.".format(
                    view_to_duplicate.Name,
                    view_to_duplicate.Id
                ))
        else:
            print("# Error: View '{}' (ID: {}) cannot be duplicated with the option: {}".format(
                view_to_duplicate.Name,
                view_to_duplicate.Id,
                duplicate_option.ToString()
            ))

    except System.Exception as e:
        print("# Error duplicating view '{}' (ID: {}): {}".format(
            view_to_duplicate.Name,
            view_to_duplicate.Id,
            str(e)
        ))