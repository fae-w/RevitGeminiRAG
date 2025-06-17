# Purpose: This script renames Revit scope boxes based on the name of the first view using them.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from System.Collections.Generic import Dictionary, List # For mapping
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    View,
    Element,
    ElementId,
    BuiltInParameter
)
import System # For Exception handling

# --- Initialization ---
processed_scope_boxes = 0
renamed_count = 0
skipped_no_views_count = 0
skipped_already_correct_count = 0
failed_count = 0
errors = []

# --- Step 1: Collect all Scope Box elements ---
scope_box_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_SectionBox).WhereElementIsNotElementType()
all_scope_boxes = list(scope_box_collector)
# print("# Found {{{{}}}} scope boxes.".format(len(all_scope_boxes))) # Escaped {{}} # Optional debug

# --- Step 2: Collect all Views and map Scope Box usage ---
view_collector = FilteredElementCollector(doc).OfClass(View)
all_views = [v for v in view_collector if v and v.IsValidObject and not v.IsTemplate]

# Dictionary to store: scope_box_id -> list of view names using it
scope_box_usage = Dictionary[ElementId, List[str]]()

for view in all_views:
    try:
        # Get the scope box parameter for the view
        scope_box_param = view.get_Parameter(BuiltInParameter.VIEW_PROJECT_BOX)

        if scope_box_param and scope_box_param.HasValue:
            scope_box_id = scope_box_param.AsElementId()

            # Check if a valid scope box is assigned
            if scope_box_id != ElementId.InvalidElementId:
                view_name = view.Name
                if not scope_box_usage.ContainsKey(scope_box_id):
                    scope_box_usage[scope_box_id] = List[str]()
                scope_box_usage[scope_box_id].Add(view_name)

    except Exception as ex:
        # Log error if processing a view fails, but continue
        errors.append("# Error processing view '{{{{}}}}' (ID: {{{{}}}}): {{{{}}}}".format(view.Name, view.Id, ex)) # Escaped {{}}
        failed_count += 1 # Count as a failure in processing stage

# --- Step 3: Iterate through Scope Boxes and attempt rename ---
for scope_box in all_scope_boxes:
    processed_scope_boxes += 1
    current_name = "Unknown" # Default for error messages
    try:
        scope_box_id = scope_box.Id
        current_name = scope_box.Name

        # Check if this scope box is used by any views
        if scope_box_usage.ContainsKey(scope_box_id):
            # Get the list of view names using this scope box
            view_names = scope_box_usage[scope_box_id]

            if view_names.Count > 0:
                # --- Assumption: Use the name of the *first* view found in the list ---
                # Note: This is arbitrary. If the same scope box is used by multiple views,
                # the renaming will depend on the order views were processed.
                # A different logic might be needed depending on the desired "primary" view definition.
                target_name = view_names[0]

                # Check if renaming is necessary
                if target_name == current_name:
                    skipped_already_correct_count += 1
                    # print("# Skipping scope box '{{{{}}}}' (ID: {{{{}}}}), already named correctly.".format(current_name, scope_box_id)) # Optional debug # Escaped {{}}
                    continue

                # Attempt to rename the scope box
                try:
                    # Use Element.Name property setter for renaming
                    scope_box.Name = target_name
                    renamed_count += 1
                    # print("# Renamed scope box '{{{{}}}}' to '{{{{}}}}' (ID: {{{{}}}})".format(current_name, target_name, scope_box_id)) # Optional debug # Escaped {{}}

                except System.ArgumentException as arg_ex:
                    failed_count += 1
                    # Common error: Name is already in use by another scope box or element
                    errors.append("# Rename Error (likely duplicate name): Scope Box '{{{{}}}}' (ID: {{{{}}}}) to '{{{{}}}}'. Error: {{{{}}}}".format(current_name, scope_box_id, target_name, arg_ex.Message)) # Escaped {{}}
                except Exception as rename_ex:
                    failed_count += 1
                    errors.append("# Rename Error: Scope Box '{{{{}}}}' (ID: {{{{}}}}) to '{{{{}}}}'. Error: {{{{}}}}".format(current_name, scope_box_id, target_name, rename_ex)) # Escaped {{}}
            else:
                # This case should not happen if ContainsKey is true, but handle defensively
                 skipped_no_views_count += 1
                 # print("# Skipping scope box '{{{{}}}}' (ID: {{{{}}}}), found in map but with empty view list.".format(current_name, scope_box_id)) # Optional debug # Escaped {{}}
        else:
            # Scope box is not applied to any view tracked
            skipped_no_views_count += 1
            # print("# Skipping scope box '{{{{}}}}' (ID: {{{{}}}}), not applied to any views.".format(current_name, scope_box_id)) # Optional debug # Escaped {{}}

    except Exception as outer_ex:
        failed_count += 1
        errors.append("# Unexpected Error processing scope box '{{{{}}}}' (ID: {{{{}}}}): {{{{}}}}".format(current_name, scope_box.Id, outer_ex)) # Escaped {{}}


# --- Final Summary (Optional: print to console) ---
# print("\n# --- Scope Box Renaming Summary ---")
# print("# Total scope boxes processed: {{{{}}}}".format(processed_scope_boxes)) # Escaped {{}}
# print("# Successfully renamed: {{{{}}}}".format(renamed_count)) # Escaped {{}}
# print("# Skipped (already correct name): {{{{}}}}".format(skipped_already_correct_count)) # Escaped {{}}
# print("# Skipped (not applied to any views): {{{{}}}}".format(skipped_no_views_count)) # Escaped {{}}
# print("# Failed operations (incl. view processing errors): {{{{}}}}".format(failed_count)) # Escaped {{}}
# if errors:
#   print("# --- Errors ---")
#   for err in errors:
#       print(err)
# print("# NOTE: Renaming based on the *first* view found using the scope box.") # Escaped {{}}