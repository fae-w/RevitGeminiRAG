# Purpose: This script identifies Revit views whose assigned view template lacks a specified filter.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ElementId,
    ParameterFilterElement
)

# Define the exact name of the filter to check for exclusion
target_filter_name = 'Room Department Colors'

# List to store names of views meeting the criteria
views_without_filter_in_template = []

# Collect all views in the document
collector_views = FilteredElementCollector(doc).OfClass(View)

for view in collector_views:
    # Skip views that are templates themselves
    if view.IsTemplate:
        continue

    # Check if the view has a view template assigned
    template_id = view.ViewTemplateId
    if template_id == ElementId.InvalidElementId:
        continue

    # Get the view template element
    view_template = doc.GetElement(template_id)

    # Verify the retrieved element is a valid View and is indeed a template
    if not view_template or not isinstance(view_template, View) or not view_template.IsTemplate:
        # print("# Warning: View '{0}' ({1}) has an invalid or non-template ViewTemplateId {2}.".format(view.Name, view.Id, template_id)) # Debug info
        continue

    try:
        # Get the filters applied to the view template
        template_filter_ids = view_template.GetFilters()
        found_target_filter = False

        if template_filter_ids and template_filter_ids.Count > 0:
            for filter_id in template_filter_ids:
                if filter_id == ElementId.InvalidElementId:
                    continue

                filter_element = doc.GetElement(filter_id)

                # Check if the element is a ParameterFilterElement and its name matches the target
                if filter_element and isinstance(filter_element, ParameterFilterElement):
                    try:
                        if filter_element.Name == target_filter_name:
                            found_target_filter = True
                            break # Found the filter, no need to check others for this template
                    except Exception as e_name:
                        # print("# Warning: Could not get name for Filter ID {0} in template '{1}'. Error: {2}".format(filter_id, view_template.Name, e_name)) # Debug info
                        pass # Continue checking other filters if name retrieval fails for one

        # If the target filter was NOT found in the template's filters, add the view name
        if not found_target_filter:
            try:
                view_name = view.Name
                views_without_filter_in_template.append(view_name)
            except Exception as e_view_name:
                 # print("# Warning: Could not get name for View ID {0}. Error: {1}".format(view.Id, e_view_name)) # Debug info
                 pass # Skip if view name cannot be retrieved

    except Exception as e_template:
        # Handle potential errors when getting filters from the template
        # print("# Warning: Could not process filters for template '{0}' (ID: {1}). Error: {2}".format(view_template.Name, template_id, e_template)) # Debug info
        pass # Skip this view if template processing fails

# Print the results
if views_without_filter_in_template:
    # Sort the list alphabetically for consistent output
    views_without_filter_in_template.sort()
    # print("# Views with a template that does NOT include the filter '{0}':".format(target_filter_name)) # Optional header
    for view_name in views_without_filter_in_template:
        print(view_name)
else:
    print("# No views found with an assigned template that excludes the filter '{0}'.".format(target_filter_name))