# Purpose: This script overrides graphic settings for elements created in the active view's phase.

﻿# Imports
import clr
clr.AddReference('System.Collections') # Required for List
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    View,
    BuiltInParameter,
    OverrideGraphicSettings,
    ViewDetailLevel,
    Element # Import Element base class
)

# Get the active view
active_view = uidoc.ActiveView

# Check if the active view is valid and is a View instance
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view or the active document window is not a view.")
else:
    # Get the phase ElementId of the current view
    view_phase_id = ElementId.InvalidElementId
    view_phase_param = active_view.get_Parameter(BuiltInParameter.VIEW_PHASE)

    if view_phase_param and view_phase_param.HasValue:
        view_phase_id = view_phase_param.AsElementId()
    else:
        print("# Error: Could not determine the phase of the current view (VIEW_PHASE parameter not found or has no value).")

    # Proceed only if the view's phase was successfully retrieved
    if view_phase_id != ElementId.InvalidElementId:

        # Collect all non-element type elements visible in the active view
        collector = FilteredElementCollector(doc, active_view.Id).WhereElementIsNotElementType()

        # List to store the ElementIds of elements to be overridden
        elements_to_override_ids = List[ElementId]() # Use .NET List for efficiency with API calls if needed later, though loop is used here

        # Iterate through collected elements to find those created in the view's phase
        for elem in collector:
            try:
                # Get the 'Phase Created' parameter of the element
                phase_created_param = elem.get_Parameter(BuiltInParameter.PHASE_CREATED)

                # Check if the parameter exists, has a value, and matches the view's phase
                if phase_created_param and phase_created_param.HasValue:
                    elem_phase_id = phase_created_param.AsElementId()
                    if elem_phase_id == view_phase_id:
                        # Check if the element supports graphic overrides (basic check: has a category)
                        # More robust checks could be added, but SetElementOverrides will handle invalid elements
                        if elem.Category is not None:
                            elements_to_override_ids.Add(elem.Id)

            except Exception as e:
                # Silently ignore elements that cause errors during parameter access
                # print("# Debug: Error processing element {0}: {1}".format(elem.Id, e)) # Optional Debug
                pass

        # Create the graphic override settings for 'Fine' detail level
        override_settings = OverrideGraphicSettings()
        override_settings.SetDetailLevel(ViewDetailLevel.Fine)

        # Apply the overrides to the identified elements
        override_count = 0
        if elements_to_override_ids.Count > 0:
            for elem_id in elements_to_override_ids:
                try:
                    # Apply the override to the specific element in the active view
                    active_view.SetElementOverrides(elem_id, override_settings)
                    override_count += 1
                except Exception as e:
                    # Silently ignore elements where override could not be applied
                    # print("# Warning: Could not apply override to element {0}: {1}".format(elem_id, e)) # Optional Warning
                    pass

            # Optional: Print summary message (commented out by default)
            # print("# Applied 'Fine' detail level override to {0} elements created in the view's phase.".format(override_count))
        # else:
            # Optional: Print info message if no elements matched (commented out by default)
            # print("# No elements found matching the view's phase to override.")

    # else case for view_phase_id being InvalidElementId is handled by the error message printed earlier.