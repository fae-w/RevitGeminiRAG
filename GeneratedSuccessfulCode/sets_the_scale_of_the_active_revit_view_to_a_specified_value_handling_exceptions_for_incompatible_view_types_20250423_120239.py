# Purpose: This script sets the scale of the active Revit view to a specified value, handling exceptions for incompatible view types.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import View, ViewType, View3D
import System

# Define the target scale denominator (for 1:100, the value is 100)
target_scale_denominator = 100

# Get the active view
active_view = doc.ActiveView

# Check if an active view exists
if active_view is None:
    print("# Error: No active view found.")
else:
    # Check if the view type supports setting a scale
    # Perspective views, sheets, schedules, legends, etc., generally do not use the Scale property in the same way.
    is_perspective = isinstance(active_view, View3D) and active_view.IsPerspective
    unscalable_types = [
        ViewType.Schedule, ViewType.ColumnSchedule, ViewType.PanelSchedule,
        ViewType.Legend, ViewType.DrawingSheet, ViewType.ProjectBrowser,
        ViewType.SystemBrowser, ViewType.Walkthrough, ViewType.Rendering # Add others if necessary
    ]
    is_unscalable_type = active_view.ViewType in unscalable_types

    if is_perspective:
        print("# Error: Cannot set the 'Scale' property for Perspective views. View: '{}'".format(active_view.Name))
    elif is_unscalable_type:
        print("# Error: Cannot set the 'Scale' property for View Type '{}'. View: '{}'".format(active_view.ViewType.ToString(), active_view.Name))
    else:
        # Validate the target scale denominator
        if View.IsValidViewScale(target_scale_denominator):
            try:
                # Check if the scale is already the target value
                if active_view.Scale == target_scale_denominator:
                    print("# View '{}' scale is already 1:{}.".format(active_view.Name, target_scale_denominator))
                else:
                    # Set the view scale
                    active_view.Scale = target_scale_denominator
                    print("# Successfully set View '{}' scale to 1:{}.".format(active_view.Name, target_scale_denominator))
            except System.Exception as e:
                # Catch potential errors if setting the scale fails for any reason
                print("# Error setting scale for View '{}'. Exception: {}".format(active_view.Name, str(e)))
                print("# View Type: {}".format(active_view.ViewType.ToString()))
        else:
            # This check is technically redundant given the hardcoded value 100, but good practice
            print("# Error: Target scale denominator {} is invalid. Must be between 1 and 24000.".format(target_scale_denominator))