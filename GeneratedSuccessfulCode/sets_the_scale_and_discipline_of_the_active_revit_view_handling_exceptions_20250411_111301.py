# Purpose: This script sets the scale and discipline of the active Revit view, handling exceptions.

# Purpose: This script sets the scale and discipline of the active view in Revit, handling cases where these properties are not applicable or modifiable.

﻿# Import necessary classes
from Autodesk.Revit.DB import View, ViewDiscipline, ViewType
# from Autodesk.Revit.Exceptions import InvalidOperationException # Optional import for specific exception handling

# Get the active view
active_view = doc.ActiveView

if active_view and isinstance(active_view, View):
    view_name = active_view.Name # Get view name for potential messages

    # --- Set View Scale to 1:50 ---
    new_scale_value = 50
    scale_set_success = False
    try:
        # Check if the view type supports scale setting.
        # Perspective views, schedules, legends, etc., don't use Scale in the same way.
        # The View.Scale property is typically relevant for plan, section, elevation, detail views.
        allowed_scale_types = [
            ViewType.FloorPlan, ViewType.CeilingPlan,
            ViewType.Elevation, ViewType.Section, ViewType.Detail,
            ViewType.DraftingView, ViewType.AreaPlan, ViewType.EngineeringPlan
            # Add other view types if applicable
        ]
        if active_view.ViewType in allowed_scale_types:
             # Setting Scale to 50 represents 1:50
             active_view.Scale = new_scale_value
             scale_set_success = True
             # print("# Scale set to 1:{} for view '{}'".format(new_scale_value, view_name)) # Optional confirmation
        else:
             print("# Info: Scale property is not applicable or settable for view type: {}".format(active_view.ViewType)) # Escaped format

    except Exception as e:
        print("# Error setting view scale for '{}': {}".format(view_name, e)) # Escaped format

    # --- Set View Discipline to Architectural ---
    discipline_set_success = False
    try:
        # Check if view has a Discipline property using HasViewDiscipline()
        # This helps avoid errors for views that don't have this concept (e.g., schedules)
        if active_view.HasViewDiscipline():
            # Attempt to set the discipline using the ViewDiscipline enum
            # An InvalidOperationException might occur if the discipline cannot be changed for this view/type
            active_view.Discipline = ViewDiscipline.Architectural
            discipline_set_success = True
            # print("# Discipline set to Architectural for view '{}'".format(view_name)) # Optional confirmation
        else:
            print("# Info: View '{}' does not have a modifiable Discipline property.".format(view_name)) # Escaped format

    except Exception as e: # Catches potential exceptions like InvalidOperationException
        print("# Error setting view discipline for '{}': {}".format(view_name, e)) # Escaped format

    # Optional: Final status message based on success flags
    # if scale_set_success and discipline_set_success:
    #     print("# Successfully updated scale and discipline for view '{}'".format(view_name))
    # elif not scale_set_success:
    #      print("# Failed to set scale for view '{}'".format(view_name))
    # elif not discipline_set_success:
    #      print("# Failed to set discipline for view '{}'".format(view_name))


elif not active_view:
    print("# Error: No active view found.")
else:
    # This case might happen if the "active view" isn't a standard View object
    print("# Error: The active element is not a standard View object suitable for these operations.")