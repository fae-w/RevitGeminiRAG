# Purpose: This script adds a specified filter to a Revit view template.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List/ICollection

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ParameterFilterElement,
    ElementId
)
# Import necessary .NET classes
from System.Collections.Generic import List

# --- Configuration ---
view_template_name = "Structural Framing Plan"
filter_name = "Concrete Columns ID"

# --- Find the View Template ---
view_template = None
view_collector = FilteredElementCollector(doc).OfClass(View)
for view in view_collector:
    if view.IsTemplate and view.Name == view_template_name:
        view_template = view
        break

# --- Find the Filter Element ---
parameter_filter = None
filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
for filt in filter_collector:
    if filt.Name == filter_name:
        parameter_filter = filt
        break

# --- Add Filter to View Template ---
if view_template and parameter_filter:
    try:
        # Get the ID of the filter
        filter_id = parameter_filter.Id

        # Check if the filter is already applied to the view template
        applied_filters = view_template.GetFilters()
        if filter_id not in applied_filters:
            # Add the filter to the view template
            # IMPORTANT: This requires an external Transaction, which is assumed to be handled.
            view_template.AddFilter(filter_id)
            # print("# Successfully added filter '{}' to view template '{}'.".format(filter_name, view_template_name)) # Optional success message
        else:
            pass
            # print("# Filter '{}' is already present in view template '{}'.".format(filter_name, view_template_name)) # Optional info message

    except Exception as e:
        print("# Error adding filter '{}' to view template '{}': {}".format(filter_name, view_template_name, e))

elif not view_template:
    print("# Error: View Template '{}' not found.".format(view_template_name))
elif not parameter_filter:
    print("# Error: Filter '{}' not found.".format(filter_name))