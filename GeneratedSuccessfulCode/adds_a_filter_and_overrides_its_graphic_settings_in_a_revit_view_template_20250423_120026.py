# Purpose: This script adds a filter and overrides its graphic settings in a Revit view template.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Added for exceptions

# Import Revit API classes
from Autodesk.Revit.DB import (
    View,
    ElementId,
    FilteredElementCollector,
    ParameterFilterElement,
    OverrideGraphicSettings,
    Color
)
# Import System classes for Exceptions
from System import InvalidOperationException, ArgumentException

# --- Configuration ---
filter_name_to_add = "Wall Fire Ratings"
override_color = Color(255, 0, 0) # Red

# --- Main Script ---
# Assume 'doc' is pre-defined and available

active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid non-template graphical view.")
else:
    template_id = active_view.ViewTemplateId
    if template_id == ElementId.InvalidElementId:
        print("# Error: The active view '{{}}' does not have a View Template assigned.".format(active_view.Name))
    else:
        template_view = doc.GetElement(template_id)
        if not isinstance(template_view, View):
            print("# Error: Could not retrieve a valid View element for the assigned View Template (ID: {{}}).".format(template_id.IntegerValue))
        else:
            # Find the filter element by name
            filter_element = None
            filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
            for f in filter_collector:
                if f.Name == filter_name_to_add:
                    filter_element = f
                    break

            if not filter_element:
                print("# Error: Filter named '{{}}' not found in the document.".format(filter_name_to_add))
            else:
                filter_id = filter_element.Id
                try:
                    # Check if the filter is already added to the template
                    applied_filters = template_view.GetFilters()
                    if filter_id not in applied_filters:
                        # Transaction managed externally - Add the filter
                        template_view.AddFilter(filter_id)
                        print("# Added filter '{{}}' to View Template '{{}}'.".format(filter_name_to_add, template_view.Name))
                    else:
                        print("# Filter '{{}}' is already present in View Template '{{}}'.".format(filter_name_to_add, template_view.Name))

                    # Create graphic overrides
                    ogs = OverrideGraphicSettings()
                    ogs.SetProjectionLineColor(override_color)

                    # Transaction managed externally - Apply the overrides
                    template_view.SetFilterOverrides(filter_id, ogs)
                    # Optional: Ensure the filter is visible if needed (default is usually visible)
                    # template_view.SetFilterVisibility(filter_id, True)
                    print("# Set Projection Line Color override (Red) for filter '{{}}' in View Template '{{}}'.".format(filter_name_to_add, template_view.Name))

                except ArgumentException as ae:
                    print("# Error applying filter or overrides to View Template '{{}}': {{}}".format(template_view.Name, ae.Message))
                except InvalidOperationException as ioe:
                    print("# Error: The View Template '{{}}' might not support filters/overrides: {{}}".format(template_view.Name, ioe.Message))
                except Exception as e:
                    # Use standard Python exception formatting
                    print("# An unexpected error occurred while modifying View Template '{{}}': {{}}".format(template_view.Name, str(e)))