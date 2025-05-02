# Purpose: This script renames dependent views in Revit based on their primary view's name.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, View, ElementId, Element
import System # For Exception handling

# --- Initialization ---
processed_count = 0
dependent_count = 0
renamed_count = 0
skipped_already_correct_count = 0
skipped_no_suffix_count = 0
failed_count = 0
errors = []

# --- Step 1: Collect all View elements ---
view_collector = FilteredElementCollector(doc).OfClass(View)
# Filter for views that are valid objects, just in case
all_views = [v for v in view_collector if v and v.IsValidObject]

print("# Found {{}} total view elements. Processing...".format(len(all_views))) # Escaped {}

# --- Step 2: Iterate through views and process dependents ---
for view in all_views:
    processed_count += 1
    primary_view_id = ElementId.InvalidElementId # Initialize
    is_dependent = False
    dependent_name = "Unknown" # Default for error messages

    try:
        # Ensure it's actually a View element before proceeding
        if not isinstance(view, View):
             # This shouldn't happen with OfClass(View) but good practice
             continue

        dependent_name = view.Name # Get name early for potential error messages

        # Check if the view is dependent
        primary_view_id = view.GetPrimaryViewId()
        if primary_view_id != ElementId.InvalidElementId:
            is_dependent = True
            dependent_count += 1
        else:
            continue # Skip non-dependent views

        # Get the primary view element
        primary_view = doc.GetElement(primary_view_id)
        if not primary_view or not isinstance(primary_view, View):
            errors.append("# Error: Could not find or access Primary View (ID: {{}}) for Dependent View '{{}}' (ID: {{}}). Skipping.".format(primary_view_id, dependent_name, view.Id)) # Escaped {}
            failed_count += 1
            continue

        primary_name = primary_view.Name

        # Determine the suffix for the new name based on the original dependent name
        suffix = None
        if dependent_name == primary_name:
             # Handle edge case where dependent has exact same name as primary
             errors.append("# Warning: Dependent View '{{}}' (ID: {{}}) has same name as Primary View '{{}}' (ID: {{}}). Cannot determine unique suffix. Skipping.".format(dependent_name, view.Id, primary_name, primary_view_id)) # Escaped {}
             skipped_no_suffix_count += 1
             continue
        elif dependent_name.startswith(primary_name):
            remainder = dependent_name[len(primary_name):]
            # Clean up common leading separators ('-', '(', ')', ':') and surrounding whitespace
            cleaned_suffix = remainder.lstrip(' -():').strip()
            if cleaned_suffix:
                suffix = cleaned_suffix
            else:
                # If cleaning leaves nothing (e.g., "PrimaryName ()"), use the original dependent name as the suffix
                # This prevents creating names like "PrimaryName - " which might be undesirable
                suffix = dependent_name
        else:
            # If dependent name doesn't start with primary name, use the whole dependent name as the suffix
            suffix = dependent_name

        # Construct the target name if suffix is valid
        if suffix:
            target_name = primary_name + " - " + suffix

            # Check if the view is already named correctly
            if target_name == dependent_name:
                skipped_already_correct_count += 1
                continue

            # Attempt to rename the dependent view
            try:
                # Revit's name length limit is generally large enough, but API might throw if invalid chars etc.
                view.Name = target_name
                renamed_count += 1
                # print("# Renamed Dependent View '{{}}' to '{{}}'".format(dependent_name, target_name)) # Optional debug # Escaped {}
            except System.ArgumentException as arg_ex:
                failed_count += 1
                # Common error: Name is already in use.
                errors.append("# Rename Error (likely duplicate): Dependent '{{}}' (ID: {{}}) to '{{}}'. Error: {{}}".format(dependent_name, view.Id, target_name, arg_ex.Message)) # Escaped {}
            except Exception as rename_ex:
                failed_count += 1
                errors.append("# Rename Error: Dependent '{{}}' (ID: {{}}) to '{{}}'. Error: {{}}".format(dependent_name, view.Id, target_name, rename_ex)) # Escaped {}
        else:
            # This case should theoretically not be reached due to fallbacks, but included for safety
            errors.append("# Error: Could not determine a valid suffix for Dependent View '{{}}' (ID: {{}}). Skipping.".format(dependent_name, view.Id)) # Escaped {}
            skipped_no_suffix_count += 1
            continue

    except Exception as outer_ex:
        failed_count += 1
        # Use the 'dependent_name' captured at the start of the try block if available
        errors.append("# Unexpected Error processing view '{{}}' (ID: {{}}): {{}}".format(dependent_name, view.Id, outer_ex)) # Escaped {}


# --- Final Summary ---
print("\n# --- Dependent View Renaming Summary ---")
print("# Total views processed: {{}}".format(processed_count))