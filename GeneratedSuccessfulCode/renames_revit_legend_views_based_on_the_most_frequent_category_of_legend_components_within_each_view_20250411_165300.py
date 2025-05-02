# Purpose: This script renames Revit legend views based on the most frequent category of legend components within each view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
clr.AddReference('System.Core') # Keep for Linq just in case, though not used below
from System import String, ArgumentException, InvalidOperationException

# Import Revit API namespaces
from Autodesk.Revit.DB import *

# --- Configuration ---
new_name_prefix = "LEG - "
# Handle cases where no primary category can be determined
default_name_if_no_category = None # Set to a string like "LEG - Undefined" to rename these, or None to skip

# --- Initialization ---
renamed_count = 0
skipped_no_components_count = 0
skipped_no_change_count = 0
error_count = 0
processed_legends_count = 0
errors = []

# --- Step 1: Collect Legend Views ---
# Ensure doc is defined (provided by the execution environment)
collector = FilteredElementCollector(doc).OfClass(View)
legend_views = [v for v in collector if v.ViewType == ViewType.Legend and not v.IsTemplate]

# --- Step 2: Iterate through Legend Views ---
for view in legend_views:
    processed_legends_count += 1
    original_name = "Unknown" # Default for error messages
    try:
        original_name = view.Name
        view_id = view.Id

        # --- Step 3: Collect Legend Components within this view ---
        component_collector = FilteredElementCollector(doc, view_id).OfClass(LegendComponent)
        legend_components = list(component_collector) # Convert to list for easier processing

        if not legend_components:
            skipped_no_components_count += 1
            # print("# Skipping Legend View '{{}}' (ID: {{}}): No Legend Components found.".format(original_name, view_id)) # Debug
            continue

        # --- Step 4: Determine the 'primary' category (most frequent) ---
        category_counts = {} # Use standard Python dictionary
        for lc in legend_components:
            try:
                # Get the ElementType ID represented by the Legend Component
                type_id = lc.GetTypeId() # Correct method name

                if type_id != ElementId.InvalidElementId:
                    element_type = doc.GetElement(type_id)
                    if element_type and element_type.Category:
                        category = element_type.Category
                        if category and category.Name: # Ensure category and category name are valid
                            category_name = category.Name
                            if category_name in category_counts:
                                category_counts[category_name] += 1
                            else:
                                category_counts[category_name] = 1
            except Exception as e_inner:
                # Log error getting category for a specific component, but continue processing others
                errors.append("# Error getting category for component ID {{}} in view '{{}}': {{}}".format(lc.Id, original_name, e_inner))
                error_count += 1


        # --- Step 5: Identify the most frequent category ---
        primary_category_name = None
        if len(category_counts) > 0:
            # Find the category name with the highest count using iteration
            max_count = -1
            # Use iteritems() for IronPython 2.7 compatibility if needed, items() usually works
            for cat_name, count in category_counts.items():
                 if count > max_count:
                     max_count = count
                     primary_category_name = cat_name
                 # Optional: Handle ties consistently if needed (e.g., alphabetically)
                 # elif count == max_count and cat_name < primary_category_name:
                 #    primary_category_name = cat_name

        # --- Step 6: Construct the new name ---
        new_name = None
        if primary_category_name:
            new_name = new_name_prefix + primary_category_name
        elif default_name_if_no_category is not None:
             new_name = default_name_if_no_category
        # else: new_name remains None, and the view will be skipped

        # --- Step 7: Rename the Legend View (Transaction handled externally) ---
        if new_name and new_name != original_name:
            try:
                # Check if a view with the new name already exists (case-insensitive)
                # Note: Revit's internal check prevents duplicates, but this is explicit
                existing_view_with_name = FilteredElementCollector(doc).OfClass(View).Where(lambda v: v.Name.Equals(new_name, StringComparison.InvariantCultureIgnoreCase)).FirstOrDefault()

                # Avoid renaming if it's the same view or another view already has the name
                if existing_view_with_name is None or existing_view_with_name.Id == view.Id:
                    view.Name = new_name
                    renamed_count += 1
                    # print("# Renamed view '{{}}' to '{{}}' (ID: {{}})".format(original_name, new_name, view_id)) # Debug
                else:
                    # Name collision with a DIFFERENT view
                    error_count += 1
                    errors.append("# Error renaming Legend View '{}' (ID: {}): New name '{}' is already used by another view (ID: {}).".format(original_name, view_id, new_name, existing_view_with_name.Id))

            except ArgumentException as arg_ex:
                error_count += 1
                # This might catch duplicate names if the explicit check above fails or other invalid args
                errors.append("# Error renaming Legend View '{}' (ID: {}): {}. New name '{}' might already exist or be invalid.".format(original_name, view_id, arg_ex.Message, new_name))
            except Exception as e_rename:
                error_count += 1
                errors.append("# Unexpected error renaming Legend View '{}' (ID: {}): {}".format(original_name, view_id, e_rename))
        elif new_name == original_name:
            skipped_no_change_count += 1
            # print("# Skipping Legend View '{{}}' (ID: {{}}): Name based on primary category ('{{}}') is already correct.".format(original_name, view_id, primary_category_name)) # Debug
        else:
             # This case handles when primary_category_name is None and default_name_if_no_category is None
             # Or when no LegendComponents were found initially (already handled by 'continue')
             if legend_components: # Only count as skipped for this reason if components existed
                 skipped_no_components_count += 1 # Reusing this counter for 'no category determined'
                 # print("# Skipping Legend View '{{}}' (ID: {{}}): Could not determine primary category and no default name set.".format(original_name, view_id)) # Debug


    except Exception as e_outer:
        error_count += 1
        errors.append("# Error processing Legend View '{}' (ID: {}): {}".format(original_name, view.Id if view else "N/A", e_outer))

# --- Optional: Print summary and errors (comment out if not desired in final environment) ---
# print("\n--- Legend View Renaming Summary ---")
# print("Total Legend Views processed: {}".format(processed_legends_count))
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (no components or category undetermined): {}".format(skipped_no_components_count))
# print("Skipped (name already correct): {}".format(skipped_no_change_count))
# print("Errors encountered: {}".format(error_count))
# if errors:
#   print("--- Errors ---")
#   for err in errors:
#       print(err)