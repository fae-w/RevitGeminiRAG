# Purpose: This script removes a specified filter from all Revit view templates.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
# Required for ICollection if needed, though direct iteration often works
# clr.AddReference('System.Collections')

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ParameterFilterElement,
    ElementId
)
# Import necessary .NET classes if needed (e.g., for List<T>)
# from System.Collections.Generic import List, ICollection
import System # For Exception handling

# --- Configuration ---
filter_name_to_remove = "Ceiling Grid Visibility"

# --- Find the Filter Element ---
parameter_filter_to_remove = None
filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
for filt in filter_collector:
    if filt.Name == filter_name_to_remove:
        parameter_filter_to_remove = filt
        break

# --- Proceed only if filter is found ---
if parameter_filter_to_remove:
    filter_id_to_remove = parameter_filter_to_remove.Id
    removed_count = 0
    processed_templates = 0

    # --- Find all View Templates ---
    view_template_collector = FilteredElementCollector(doc).OfClass(View)
    # Filter for views that are templates
    view_templates = [v for v in view_template_collector if v.IsTemplate]

    # --- Iterate through View Templates and Remove Filter ---
    if not view_templates:
        # print("# Info: No View Templates found in the project.") # Optional info message
        pass
    else:
        for view_template in view_templates:
            processed_templates += 1
            try:
                # Check if the view template type supports filters (implicitly handled by GetFilters/RemoveFilter)
                # Get the list of filters currently applied to the view template
                applied_filters = view_template.GetFilters() # Returns ICollection<ElementId>

                # Check if the target filter is in the list of applied filters
                # Direct check using 'in' works with ICollection<ElementId> in IronPython
                if filter_id_to_remove in applied_filters:
                    # Remove the filter
                    # IMPORTANT: This requires an external Transaction, which is assumed to be handled.
                    view_template.RemoveFilter(filter_id_to_remove)
                    removed_count += 1
                    # print("# Successfully removed filter '{0}' from view template '{1}'.".format(filter_name_to_remove, view_template.Name)) # Optional success message

            except System.Exception as e:
                # Catch potential errors (e.g., view type doesn't support filters, though RemoveFilter should handle non-existence gracefully based on docs)
                # print("# Warning: Could not process View Template '{0}'. Error: {1}".format(view_template.Name, e)) # Optional warning message
                pass # Continue with the next view template

        # print("# Processed {0} View Templates. Removed filter '{1}' from {2} templates.".format(processed_templates, filter_name_to_remove, removed_count)) # Optional summary message

elif not parameter_filter_to_remove:
    print("# Error: Filter '{0}' not found.".format(filter_name_to_remove))

# else block handles the case where the filter was found but no templates were processed or the filter wasn't on any templates. No message needed here usually.