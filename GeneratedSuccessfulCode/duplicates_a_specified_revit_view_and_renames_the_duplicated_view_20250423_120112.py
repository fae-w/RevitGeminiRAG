# Purpose: This script duplicates a specified Revit view and renames the duplicated view.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import FilteredElementCollector, View, ViewDuplicateOption, ElementId

# --- Configuration ---
target_view_name = "Section Through Parking"
new_view_name = "Section Through Parking - Working"
duplicate_option = ViewDuplicateOption.WithDetailing # Or ViewDuplicateOption.Duplicate or ViewDuplicateOption.AsDependent

# --- Find the view to duplicate ---
view_to_duplicate = None
collector = FilteredElementCollector(doc).OfClass(View)
for view in collector:
    if isinstance(view, View) and view.Name == target_view_name:
        view_to_duplicate = view
        break # Found the view, exit the loop

# --- Perform duplication and renaming ---
if view_to_duplicate is None:
    print("# Error: View named '{{}}' not found.".format(target_view_name)) # Escaped format
else:
    # Check if the view can be duplicated with the chosen option
    if not view_to_duplicate.CanViewBeDuplicated(duplicate_option):
        print("# Error: View '{{}}' (ID: {{{{}}}}) cannot be duplicated with the option: {{{{}}}}.".format(target_view_name, view_to_duplicate.Id.ToString(), duplicate_option.ToString())) # Escaped format
    else:
        try:
            # Duplicate the view
            new_view_id = view_to_duplicate.Duplicate(duplicate_option)

            if new_view_id != ElementId.InvalidElementId:
                # Get the newly created view element
                new_view = doc.GetElement(new_view_id)

                if new_view and isinstance(new_view, View):
                    original_new_name = new_view.Name # Name assigned by Revit during duplication
                    try:
                        # Rename the new view
                        new_view.Name = new_view_name
                        print("# Successfully duplicated view '{{}}' (ID: {{{{}}}}) as '{{}}' (ID: {{{{}}}}) and renamed it from '{{}}'.".format(target_view_name, view_to_duplicate.Id.ToString(), new_view_name, new_view_id.ToString(), original_new_name)) # Escaped format
                    except Exception as rename_ex:
                        print("# Successfully duplicated view '{{}}' (ID: {{{{}}}}) as '{{}}' (ID: {{{{}}}), but failed to rename it to '{{}}'. Error: {{{{}}}}".format(target_view_name, view_to_duplicate.Id.ToString(), original_new_name, new_view_id.ToString(), new_view_name, rename_ex)) # Escaped format
                else:
                    print("# Error: Duplication returned a valid ID ({{{{}}}}), but failed to retrieve the newly created view element.".format(new_view_id.ToString())) # Escaped format
            else:
                print("# Error: Failed to duplicate the view '{{}}' (ID: {{{{}}}}). The Duplicate method returned an invalid ID.".format(target_view_name, view_to_duplicate.Id.ToString())) # Escaped format

        except Exception as ex:
            # Catch potential errors during duplication
            print("# Error duplicating view '{{}}' (ID: {{{{}}}}): {{{{}}}}".format(target_view_name, view_to_duplicate.Id.ToString(), ex)) # Escaped format