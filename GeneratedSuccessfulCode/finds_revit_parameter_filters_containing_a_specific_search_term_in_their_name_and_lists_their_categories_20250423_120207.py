# Purpose: This script finds Revit parameter filters containing a specific search term in their name and lists their categories.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ParameterFilterElement, Category, ElementId

# Search term (case-insensitive)
search_term = "rating"

# Find all ParameterFilterElement instances in the document
collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)

found_filters = False
for filter_element in collector:
    if isinstance(filter_element, ParameterFilterElement):
        try:
            filter_name = filter_element.Name
            # Check if the filter name contains the search term (case-insensitive)
            if search_term.lower() in filter_name.lower():
                found_filters = True
                category_ids = filter_element.GetCategories()
                category_names = []
                if category_ids and category_ids.Count > 0:
                    for cat_id in category_ids:
                        category = Category.GetCategory(doc, cat_id)
                        if category:
                            category_names.append(category.Name)
                        else:
                            category_names.append("Invalid Category ID: {}".format(cat_id.IntegerValue))
                else:
                    category_names.append("No Categories Assigned")

                print("Filter: {} | Categories: {}".format(filter_name, ", ".join(category_names)))

        except Exception as e:
            # Log error processing a specific filter but continue
            print("# Error processing filter ID {}: {}".format(filter_element.Id.IntegerValue, e))

if not found_filters:
    print("# No filters found with '{}' in their name.".format(search_term))