# Purpose: This script duplicates the active Revit view with detailing.

﻿# Import necessary classes
from Autodesk.Revit.DB import View, ViewDuplicateOption, ElementId

# Get the active view
active_view = uidoc.ActiveView

if active_view is None:
    print("# Error: No active view found.")
else:
    # Get the original view name
    original_name = active_view.Name
    original_id = active_view.Id

    # Check if the view can be duplicated with detailing
    if not active_view.CanViewBeDuplicated(ViewDuplicateOption.WithDetailing):
        print("# Error: The active view '{{}}' (ID: {{}}) cannot be duplicated with detailing.".format(original_name, original_id.ToString())) # Escaped format string
    else:
        try:
            # Duplicate the view with detailing
            # This corresponds to the "Duplicate with Detailing" option in the UI
            new_view_id = active_view.Duplicate(ViewDuplicateOption.WithDetailing)

            if new_view_id != ElementId.InvalidElementId:
                # Get the newly created view element
                new_view = doc.GetElement(new_view_id)

                if new_view and isinstance(new_view, View):
                    print("# Successfully duplicated view '{{}}' (ID: {{}}) with detailing as '{{}}' (ID: {{}})".format(original_name, original_id.ToString(), new_view.Name, new_view_id.ToString())) # Escaped format string
                else:
                    print("# Error: Duplication returned a valid ID ({{}}) but failed to retrieve the newly created view element.".format(new_view_id.ToString())) # Escaped format string
            else:
                print("# Error: Failed to duplicate the view '{{}}' (ID: {{}}). The Duplicate method returned an invalid ID.".format(original_name, original_id.ToString())) # Escaped format string

        except Exception as ex:
            # Catch potential errors during duplication
            print("# Error duplicating view '{{}}' (ID: {{}}): {{}}".format(original_name, original_id.ToString(), ex)) # Escaped format string