# Purpose: This script hides the 'Roofs' category in the active Revit 3D view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    View3D,
    BuiltInCategory,
    Category,
    ElementId,
    View # Base class for type checking
)
import System # For Exception handling

# Get the active view
active_view = uidoc.ActiveView

# Get the Roofs category ID
roof_category = Category.GetCategory(doc, BuiltInCategory.OST_Roofs)
roof_cat_id = None
if roof_category:
    roof_cat_id = roof_category.Id
else:
    print("# Error: Could not find the 'Roofs' category in the document.")

# Proceed only if we have a valid view and category ID
if not active_view:
    print("# Error: No active view found.")
elif not isinstance(active_view, View3D):
    print("# Error: The active view is not a 3D view.")
elif roof_cat_id is None:
    # Error message already printed above
    pass
else:
    try:
        # Check if the view allows modifying category visibility directly
        # This accounts for potential view template locks on V/G overrides
        if not active_view.CanModifyCategoryVisibility():
            print("# Error: The active view does not allow direct modification of category visibility (potentially locked by a View Template).")
        # Check if the Roofs category specifically can be hidden in this view
        elif not active_view.CanCategoryBeHidden(roof_cat_id):
             print("# Error: The 'Roofs' category cannot be hidden in this specific view type or due to view settings.")
        else:
            # Hide the Roofs category
            active_view.SetCategoryHidden(roof_cat_id, True)
            # Optional: Print success message
            # print("# Successfully hid the 'Roofs' category in the active 3D view: '{}'".format(active_view.Name))

    except System.Exception as e:
        print("# An error occurred while trying to hide the 'Roofs' category: {}".format(e))