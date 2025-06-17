# Purpose: This script duplicates an existing Revit filter, applies it to a new category (Floors), and handles potential rule incompatibility.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ParameterFilterElement,
    ElementId,
    BuiltInCategory,
    ElementFilter # Needed to get the filter logic
)
from System.Collections.Generic import List
from Autodesk.Revit.Exceptions import ArgumentException

# --- Configuration ---
existing_filter_name = "Wall Finishes"
new_filter_name = "Floor Finishes"
new_category_id = ElementId(BuiltInCategory.OST_Floors)

# --- Main Script ---

# Function to find a filter by name
def find_filter_by_name(doc, filter_name):
    filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    for f in filter_collector:
        if f.Name == filter_name:
            return f
    return None

# Find the existing filter
existing_filter = find_filter_by_name(doc, existing_filter_name)

if not existing_filter:
    print("# Error: Existing filter '{}' not found. Cannot create new filter.".format(existing_filter_name))
else:
    # Check if the new filter already exists
    new_filter_check = find_filter_by_name(doc, new_filter_name)
    if new_filter_check:
        print("# Error: A filter named '{}' already exists.".format(new_filter_name))
    else:
        # Get the filter logic (rules) from the existing filter
        try:
            # GetElementFilter returns the combined logic (e.g., ElementParameterFilter)
            existing_element_filter = existing_filter.GetElementFilter()
            if existing_element_filter is None:
                 print("# Error: Could not retrieve filter logic (ElementFilter) from '{}'.".format(existing_filter_name))
            else:
                # Prepare the category list for the new filter
                new_categories = List[ElementId]()
                new_categories.Add(new_category_id)

                # Attempt to create the new Parameter Filter Element
                # The Create method will validate if the rules are applicable to the new category
                try:
                    # Transaction is handled externally by the C# wrapper
                    new_filter = ParameterFilterElement.Create(doc, new_filter_name, new_categories, existing_element_filter)
                    print("# Successfully created filter: '{}' based on '{}' for Category: Floors".format(new_filter_name, existing_filter_name))
                except ArgumentException as arg_ex:
                     print("# Error creating filter '{}': {}. The rules from '{}' might not be applicable to the Floors category.".format(new_filter_name, arg_ex.Message, existing_filter_name))
                except Exception as create_ex:
                     print("# Error creating ParameterFilterElement '{}': {}".format(new_filter_name, create_ex))

        except Exception as get_filter_ex:
            print("# Error retrieving filter logic from existing filter '{}': {}".format(existing_filter_name, get_filter_ex))