# Purpose: This script duplicates the active Revit view as a dependent and renames the duplicated view with a specified suffix.

# Purpose: This script duplicates the active view in Revit and renames the duplicated view with a suffix.

﻿# Import necessary classes
from Autodesk.Revit.DB import View, ViewDuplicateOption, ElementId

# Get the active view
active_view = doc.ActiveView

if active_view is None:
    print("# Error: No active view found.")
else:
    # Check if the view is a type that can be duplicated (most graphical views can)
    # Although View.Duplicate will throw an exception, we can do a basic check
    if not isinstance(active_view, View) or not active_view.CanBePrinted:
         print("# Error: The active view cannot be duplicated (e.g., it might be a schedule, project browser, etc.).")
    else:
        try:
            # Get the original view name
            original_name = active_view.Name

            # Define the new view name
            new_view_name = original_name + "_Detail A"

            # Duplicate the view as a dependent
            new_view_id = active_view.Duplicate(ViewDuplicateOption.AsDependent)

            if new_view_id != ElementId.InvalidElementId:
                # Get the newly created view element
                new_view = doc.GetElement(new_view_id)

                if new_view and isinstance(new_view, View):
                    try:
                        # Rename the new view
                        # Revit might automatically adjust the name if it already exists (e.g., append a number)
                        new_view.Name = new_view_name
                        print("# Successfully duplicated view '{}' as '{}' (ID: {})".format(original_name, new_view.Name, new_view_id.ToString())) # Escaped format string
                    except Exception as rename_ex:
                        print("# Error renaming the new view (ID: {}): {}".format(new_view_id.ToString(), rename_ex)) # Escaped format string
                else:
                    print("# Error: Failed to retrieve the newly created view element (ID: {}).".format(new_view_id.ToString())) # Escaped format string
            else:
                print("# Error: Failed to duplicate the view '{}'. The Duplicate method returned an invalid ID.".format(original_name)) # Escaped format string

        except Exception as ex:
            # Catch potential errors during duplication (e.g., view type cannot be duplicated)
            print("# Error duplicating view '{}': {}".format(active_view.Name, ex)) # Escaped format string