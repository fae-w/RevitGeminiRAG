# Purpose: This script isolates structural elements in the active 3D view by hiding all other categories.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T> and HashSet<T>

from System.Collections.Generic import List, HashSet

from Autodesk.Revit.DB import (
    View3D,
    ElementId,
    BuiltInCategory,
    Category,
    CategoryType,
    View # Base class for View checking
)

# Define the categories to keep visible
categories_to_keep_visible_bics = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFoundation
]

# Convert BuiltInCategory enums to ElementIds and store in a HashSet for efficient lookup
categories_to_keep_visible_ids = HashSet[ElementId]()
for bic in categories_to_keep_visible_bics:
    try:
        # Get the category ElementId based on the BuiltInCategory enum
        cat = Category.GetCategory(doc, bic)
        if cat:
            categories_to_keep_visible_ids.Add(cat.Id)
        # else: # Optional: Log if a BuiltInCategory doesn't resolve to a category
        #     print("# Warning: Could not find Category for BuiltInCategory: {}".format(bic))
    except Exception as e:
         # print("# Error getting category ID for {}: {}".format(bic, e)) # Optional Debug
         pass # Silently skip if BIC is invalid or category doesn't exist in the project

# Get the active view
active_view = uidoc.ActiveView

# Check if the active view is a 3D view and supports category visibility overrides
if not active_view or not isinstance(active_view, View3D):
    print("# Error: The active view is not a 3D view. Script terminated.")
elif not active_view.CanModifyCategoryVisibility():
     print("# Error: The active 3D view does not support modifying category visibility (e.g., it might be a template or have other restrictions). Script terminated.")
else:
    # Check if we successfully identified the categories to keep
    if categories_to_keep_visible_ids.Count == 0:
        print("# Error: Could not identify the ElementIds for the structural categories specified. Ensure these categories exist in the project. Script terminated.")
    else:
        # Note: This script modifies the view's Visibility/Graphics overrides directly
        # by hiding categories, rather than creating and applying a ParameterFilterElement.
        # This is often a more direct way to achieve the goal of isolating specific categories visually,
        # as filters are primarily for applying overrides to elements *selected* by the filter's rules.

        hidden_count = 0
        made_visible_count = 0
        skipped_count = 0

        # Get all categories in the document
        all_categories = doc.Settings.Categories

        # Iterate through all categories and modify visibility in the active view
        for cat in all_categories:
            if cat is None: continue # Skip null categories if any

            try:
                category_id = cat.Id

                # Check if the category is a Model category and if its visibility can be controlled in this view
                # Also check if the category is not a subcategory (Parent is null) unless it's explicitly allowed
                # For simplicity, we operate on main model categories that can be hidden
                if cat.CategoryType == CategoryType.Model and active_view.CanCategoryBeHidden(category_id):
                    # Check if this category is one we want to keep visible
                    if categories_to_keep_visible_ids.Contains(category_id):
                        # Ensure this category is visible
                        if active_view.IsCategoryHidden(category_id): # Check current state first to avoid unnecessary calls
                           active_view.SetCategoryHidden(category_id, False)
                           made_visible_count += 1
                        # else: # Optional: Category already visible
                        #    pass
                    else:
                        # Hide this category if it's not already hidden
                         if not active_view.IsCategoryHidden(category_id): # Check current state first
                            active_view.SetCategoryHidden(category_id, True)
                            hidden_count += 1
                         # else: # Optional: Category already hidden
                         #    pass
                else:
                    # Category is not a model category or cannot be hidden in this view
                    skipped_count += 1

            except Exception as e:
                 # print("# Warning: Error processing category '{}' (ID: {}): {}".format(cat.Name, cat.Id, e)) # Optional Debug
                 skipped_count += 1
                 continue # Skip to next category on error

        # Optional: Print summary to RevitPythonShell or pyRevit output
        # print("# Visibility Settings Applied to Active 3D View:")
        # print("# - Categories hidden: {}".format(hidden_count))
        # print("# - Categories ensured visible: {}".format(made_visible_count))
        # print("# - Categories skipped (not model/controllable/error): {}".format(skipped_count))
        # print("# NOTE: This script modified V/G settings directly, not via a named filter element.")