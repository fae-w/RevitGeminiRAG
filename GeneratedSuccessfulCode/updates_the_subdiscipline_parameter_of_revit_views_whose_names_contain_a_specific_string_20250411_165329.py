# Purpose: This script updates the subdiscipline parameter of Revit views whose names contain a specific string.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import FilteredElementCollector, View, Parameter
import System # For Exception handling

# --- Parameters ---
search_string = "Enlarged Plan"
parameter_name = "Subdiscipline" # Assuming this is the exact, case-sensitive name
new_value = "Details"

# --- Initialization ---
processed_count = 0
matched_name_count = 0
modified_count = 0
skipped_no_param = 0
skipped_read_only = 0
failed_count = 0
errors = []

# --- Step 1: Collect all View elements ---
view_collector = FilteredElementCollector(doc).OfClass(View)
all_views = [v for v in view_collector if v and v.IsValidObject]

print("# Found {{{{}}}} total view elements. Processing...".format(len(all_views))) # Escaped {{}}

# --- Step 2: Iterate through views and modify parameter ---
for view in all_views:
    processed_count += 1
    view_name = "Unknown" # Default for error messages

    try:
        view_name = view.Name

        # Check if the view name contains the search string
        if search_string in view_name:
            matched_name_count += 1

            # Attempt to find the parameter by name
            # Note: LookupParameter is case-sensitive
            param = view.LookupParameter(parameter_name)

            if param is not None and param.HasValue:
                # Check if the parameter is read-only
                if param.IsReadOnly:
                    skipped_read_only += 1
                    # print("# Skipping view '{{{{}}}}' (ID: {{{{}}}}). Parameter '{{{{}}}}' is read-only.".format(view_name, view.Id, parameter_name)) # Debug # Escaped {{}}
                else:
                    try:
                        # Set the parameter value
                        current_value = None
                        storage_type = param.StorageType
                        if storage_type == StorageType.String:
                            current_value = param.AsString()
                        elif storage_type == StorageType.ElementId:
                             # Handle case where subdiscipline might be linked to a Key Schedule or similar (less common)
                             # For simplicity, we assume it's a string here. If it's an ID, setting with a string will fail.
                             # Could add logic here to check if 'Details' exists as an element name if needed.
                             pass
                        elif storage_type == StorageType.Integer or storage_type == StorageType.Double:
                             # Subdiscipline is typically text, handle error if not
                             failed_count += 1
                             errors.append("# Error: Parameter '{{{{}}}}' in view '{{{{}}}}' (ID: {{{{}}}}) is not a Text parameter (Type: {{{{}}}}). Cannot set to '{{{{}}}}'.".format(parameter_name, view_name, view.Id, storage_type, new_value)) # Escaped {{}}
                             continue # Skip to next view


                        # Only set if the value is different
                        if current_value != new_value:
                            param.Set(new_value)
                            modified_count += 1
                            # print("# Set '{{{{}}}}' to '{{{{}}}}' for view '{{{{}}}}' (ID: {{{{}}}}).".format(parameter_name, new_value, view_name, view.Id)) # Debug # Escaped {{}}
                        # else: # Parameter already has the correct value, do nothing. Could add counter if needed.
                        #    pass

                    except Exception as set_ex:
                        failed_count += 1
                        errors.append("# Set Error: View '{{{{}}}}' (ID: {{{{}}}}), Param '{{{{}}}}'. Error: {{{{}}}}".format(view_name, view.Id, parameter_name, set_ex.Message)) # Escaped {{}}
            else:
                skipped_no_param += 1
                # print("# Skipping view '{{{{}}}}' (ID: {{{{}}}}). Parameter '{{{{}}}}' not found or has no value.".format(view_name, view.Id, parameter_name)) # Debug # Escaped {{}}

    except Exception as outer_ex:
        failed_count += 1
        errors.append("# Unexpected Error processing view '{{{{}}}}' (ID: {{{{}}}}): {{{{}}}}".format(view_name, view.Id, outer_ex)) # Escaped {{}}

# --- Final Summary ---
print("\n# --- View Subdiscipline Update Summary ---")
print("# Searched for views containing: '{}'".format(search_string)) # Escaped {}
print("# Target parameter: '{}'".format(parameter_name)) # Escaped {}
print("# Target value: '{}'".format(new_value)) # Escaped {}
print("# Total views processed: {}".format(processed_count)) # Escaped {}
print("# Views with matching name: {}".format(matched_name_count)) # Escaped {}
print("# Views successfully modified: {}".format(modified_count)) # Escaped {}
print("# Skipped (Parameter '{}' not found/no value): {}".format(parameter_name, skipped_no_param)) # Escaped {}
print("# Skipped (Parameter '{}' read-only): {}".format(parameter_name, skipped_read_only)) # Escaped {}
print("# Failed attempts (errors): {}".format(failed_count)) # Escaped {}

# Print specific errors if any occurred
if errors:
    print("\n# Errors Encountered:")
    for error in errors:
        print(error)