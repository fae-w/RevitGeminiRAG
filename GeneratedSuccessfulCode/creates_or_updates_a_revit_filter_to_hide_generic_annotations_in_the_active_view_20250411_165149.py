# Purpose: This script creates or updates a Revit filter to hide Generic Annotations in the active view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId, View, Level,
    ParameterFilterElement, ParameterFilterRuleFactory, FilterRule,
    ViewType, Category
)
from Autodesk.Revit.Exceptions import ArgumentException

# --- Configuration ---
filter_name = "TEMP - Hide Generic Annotations"

# --- Main Script ---

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Active view is not a valid project view or is a view template.")
# Check if the view type supports filters
elif not active_view.AreAnnotationCategoriesHidden: # Checks if the view type supports Visibility/Graphics Overrides for Annotation Categories
     print("# Error: The active view type ('{{}}') does not support Visibility/Graphics Overrides for Annotation Categories, cannot apply filter.".format(active_view.ViewType))
     active_view = None # Prevent further processing

# Proceed only if the view is valid and supports annotation V/G overrides
if active_view and isinstance(active_view, View) and not active_view.IsTemplate:

    # --- Filter Definition ---
    # Target Category: Generic Annotations (OST_GenericAnnotation)
    target_bic = BuiltInCategory.OST_GenericAnnotation
    try:
        target_category = Category.GetCategory(doc, target_bic)
        if not target_category:
            print("# Error: Could not find the 'Generic Annotations' category in the document.")
            target_category_id = None
        else:
            target_category_id = target_category.Id
            # Verify if this category can be controlled by filters in this view
            if not target_category.AllowsVisibilityControl(active_view):
                 print("# Error: The category 'Generic Annotations' cannot have its visibility controlled in the active view ('{{}}').".format(active_view.Name))
                 target_category_id = None
            elif not active_view.CanCategoryBeHidden(target_category_id):
                 print("# Error: The category 'Generic Annotations' cannot be hidden in the active view ('{{}}').".format(active_view.Name))
                 target_category_id = None

    except Exception as e:
        print("# Error accessing Generic Annotations category: {{}}".format(e))
        target_category_id = None

    if target_category_id:
        categories = List[ElementId]()
        categories.Add(target_category_id)

        # Rules: No rules needed. An empty rule set means the filter applies to all elements
        # of the specified categories.
        filter_rules = List[FilterRule]()

        # Check if a filter with the same name already exists
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        new_filter_id = ElementId.InvalidElementId
        try:
            # Transaction is handled externally by C# wrapper
            if existing_filter:
                # print("# Filter named '{{}}' already exists. Updating categories.".format(filter_name)) # Optional info
                try:
                    # Ensure categories and rules match the desired state
                    existing_filter.SetCategories(categories)
                    # Setting rules, even if empty, might be necessary if previously had rules
                    existing_filter.SetRules(filter_rules)
                    new_filter_id = existing_filter.Id
                    # print("# Updated existing filter '{{}}'.".format(filter_name)) # Optional info
                except Exception as update_e:
                    print("# Error updating existing filter '{{}}': {{}}".format(filter_name, update_e))
                    new_filter_id = ElementId.InvalidElementId # Prevent proceeding if update fails
            else:
                # Create the Parameter Filter Element
                try:
                    # Create filter with the category list and an empty rule list
                    new_filter = ParameterFilterElement.Create(doc, filter_name, categories, filter_rules)
                    new_filter_id = new_filter.Id
                    # print("# Created new filter: '{{}}'".format(filter_name)) # Optional info
                except Exception as create_e:
                    print("# Error creating ParameterFilterElement: {{}}".format(create_e))

            if new_filter_id != ElementId.InvalidElementId:
                # --- Apply Filter to Active View ---
                try:
                    # Check if filter is already applied to the view
                    applied_filters = active_view.GetFilters()
                    if new_filter_id not in applied_filters:
                        active_view.AddFilter(new_filter_id)
                        # print("# Added filter '{{}}' to view '{{}}'.".format(filter_name, active_view.Name)) # Optional info
                    # else:
                    #     print("# Filter '{{}}' was already present in view '{{}}'.".format(filter_name, active_view.Name)) # Optional info

                    # Set the filter to be NOT visible (hides matching elements)
                    active_view.SetFilterVisibility(new_filter_id, False)
                    print("# Applied filter '{{}}' to hide 'Generic Annotations' in view '{{}}'.".format(filter_name, active_view.Name))

                except Exception as apply_e:
                     # Check for specific error related to V/G overrides support
                    if "View type does not support Visibility/Graphics Overrides" in str(apply_e) or \
                       "View type does not support filters" in str(apply_e):
                         print("# Error: The current view ('{{}}', type: {{}}) does not support Filters or Visibility/Graphics Overrides for the target category.".format(active_view.Name, active_view.ViewType))
                    else:
                         print("# Error applying filter visibility to view '{{}}': {{}}".format(active_view.Name, apply_e))
        except Exception as outer_e:
            # Catch errors during filter creation/update or applying to view
            print("# An error occurred during filter processing: {{}}".format(outer_e))
        finally:
            # Transaction commit/rollback handled externally
            pass
    else:
         # Error message printed during category check
         print("# Filter application aborted due to category issues.")

# Else for initial view check handled above
elif not active_view:
     # Error message already printed
     pass