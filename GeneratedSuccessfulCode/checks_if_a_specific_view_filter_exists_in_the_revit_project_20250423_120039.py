# Purpose: This script checks if a specific view filter exists in the Revit project.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ParameterFilterElement

# --- Configuration ---
target_filter_name = "Life Safety Plan Filter"

# --- Main Script ---
found_filter = False

# Collect all ParameterFilterElement instances in the document
filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)

# Iterate through the collected filters
for filter_element in filter_collector:
    if isinstance(filter_element, ParameterFilterElement):
        try:
            if filter_element.Name == target_filter_name:
                found_filter = True
                break # Exit loop once found
        except Exception as e:
            # Handle potential errors accessing element properties
            print("# Warning: Could not access properties for element ID {}: {}".format(filter_element.Id, e))

# Print the result
if found_filter:
    print("# View filter named '{}' exists in the project.".format(target_filter_name))
else:
    print("# View filter named '{}' does NOT exist in the project.".format(target_filter_name))