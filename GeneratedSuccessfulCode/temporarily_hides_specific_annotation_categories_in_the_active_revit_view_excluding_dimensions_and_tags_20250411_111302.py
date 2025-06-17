# Purpose: This script temporarily hides specific annotation categories in the active Revit view, excluding dimensions and tags.

# Purpose: This script temporarily hides annotation categories, excluding dimensions and tags, in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    Category,
    CategoryType,
    ElementId,
    BuiltInCategory,
    View,
    TemporaryViewMode # Needed for context, though not directly used for HideCategoriesTemporary
)
import System # Required for Enum.Parse and exception handling

# Assume doc and uidoc are pre-defined

# Get the active view
try:
    active_view = doc.ActiveView
    if active_view is None:
        raise Exception("No active view found.")
except Exception as e:
    print(f"# Error getting active view: {{e}}") # Escaped f-string
    # Stop script execution if no active view
    # In a real script, might exit here or raise an exception
    active_view = None

categories_to_hide_ids = List[ElementId]()

if active_view and isinstance(active_view, View):
    # Get all categories in the document
    all_categories = doc.Settings.Categories

    # Identify categories to hide
    for category in all_categories:
        if category is None:
            continue

        try:
            # Check if it's an Annotation Category
            if category.CategoryType == CategoryType.Annotation:
                # Check if visibility can be controlled in this view
                if not category.AllowsVisibilityControl(active_view):
                    continue

                # Check if it's Dimensions (which should NOT be hidden)
                if category.Id.IntegerValue == int(BuiltInCategory.OST_Dimensions):
                    continue

                # Check if it's a Tag category (which should NOT be hidden)
                # We identify tag categories by checking if their BuiltInCategory enum name ends with 'Tag' or 'Tags'
                # This is an approximation, but covers most standard tag types.
                bic_enum_val = category.Id.IntegerValue
                is_tag = False
                if bic_enum_val < 0: # Check if it's a valid BuiltInCategory ID
                    try:
                        # Attempt to get the BuiltInCategory enum based on its integer value
                        bic_name = System.Enum.GetName(BuiltInCategory, bic_enum_val)
                        if bic_name and (bic_name.EndsWith("Tag") or bic_name.EndsWith("Tags")):
                           is_tag = True
                    except System.ArgumentException:
                        # Not a standard BuiltInCategory, might be a custom annotation. Assume it's not a tag to be safe.
                        pass
                    except Exception:
                         # Handle other potential errors getting enum name
                         pass # Assume not a tag

                if is_tag:
                    continue # Don't hide tag categories

                # If it's an annotation category, allows visibility control,
                # is not Dimensions, and is not identified as a Tag, add it to the hide list.
                categories_to_hide_ids.Add(category.Id)

        except Exception as cat_ex:
            # print(f"# Warning: Could not process category '{{category.Name}}'. Error: {{cat_ex}}") # Escaped f-string
            pass # Continue with the next category

    # Apply the temporary hide if any categories were selected
    if categories_to_hide_ids.Count > 0:
        try:
            # Temporarily hide the collected annotation categories (excluding Dimensions and Tags)
            # Transaction is handled externally by C# wrapper
            active_view.HideCategoriesTemporary(categories_to_hide_ids)
            # print(f"# Temporarily hid {{categories_to_hide_ids.Count}} annotation categories (excluding Dimensions and Tags) in view: {{active_view.Name}}") # Escaped f-string
        except Exception as hide_ex:
            print(f"# Error applying temporary hide: {{hide_ex}}") # Escaped f-string
    #else:
        # print("# No annotation categories (other than Dimensions/Tags) found or eligible to be temporarily hidden in the active view.") # Escaped f-string
        # pass

# else:
    # Error message printed above if active view was not found or invalid
    # print("# Cannot proceed without a valid active view.") # Escaped
    # pass