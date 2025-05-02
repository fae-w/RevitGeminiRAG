# Purpose: This script updates a specified parameter for multiple Revit elements based on element IDs from input data.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ElementId, Parameter, StorageType, Element
# Need System for Int64 conversion
import System

# Input data as a multiline string
# Format: ID,Reviewer (Header line is ignored)
input_data = """ID,Reviewer
12345,UserA
99999,UserB
67890,UserA
11111,UserC""" # Example includes a potentially non-existent ID

# --- Configuration ---
# The exact name of the parameter to update
reviewed_by_param_name = "Reviewed By"

# --- Initialization ---
not_found_ids = []
failed_update_info = [] # Store tuples (id_str, reason)

# --- Process Input Data ---
lines = input_data.strip().split('\n')

if not lines or len(lines) < 2:
    print("# Error: Input data is empty or missing header/data lines.")
else:
    # Iterate through data lines, skipping the header (index 0)
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue # Skip empty lines

        parts = line.split(',', 1) # Split only on the first comma
        if len(parts) != 2:
            failed_update_info.append((line, "Invalid line format - expected ID,Reviewer"))
            continue

        id_str = parts[0].strip()
        reviewer_name = parts[1].strip()

        element_id = ElementId.InvalidElementId
        try:
            # Convert string ID to Int64 and then to ElementId
            element_id_long = System.Int64.Parse(id_str)
            element_id = ElementId(element_id_long)
            # Check if the parsed ID is valid (e.g., not -1 if InvalidElementId was parsed)
            if element_id == ElementId.InvalidElementId:
                 raise ValueError("Parsed ID resulted in InvalidElementId")

        except ValueError:
            # Catch invalid integer format or potentially negative numbers if Int64.Parse fails
            failed_update_info.append((id_str, "Invalid Element ID format (must be a positive integer)"))
            continue
        except Exception as e:
             # Catch other potential errors during ElementId creation
             failed_update_info.append((id_str, "Error creating ElementId: {}".format(e))) # Escaped curly braces
             continue

        # Try to get the element from the document
        element = doc.GetElement(element_id)

        if element is None:
            # Element ID does not exist in the project
            not_found_ids.append(id_str)
        else:
            # Element found, try to update the parameter
            try:
                # Find the parameter by name using LookupParameter
                param = element.LookupParameter(reviewed_by_param_name)

                if param is None:
                    failed_update_info.append((id_str, "Parameter '{}' not found on element".format(reviewed_by_param_name))) # Escaped curly braces
                elif param.IsReadOnly:
                    failed_update_info.append((id_str, "Parameter '{}' is read-only".format(reviewed_by_param_name))) # Escaped curly braces
                else:
                    # Check if the parameter storage type is String before setting
                    if param.StorageType == StorageType.String:
                         # Set the parameter value (Requires an active transaction managed externally)
                         success = param.Set(reviewer_name)
                         if not success:
                              # Set can return false for various reasons (e.g., internal validation failure)
                              failed_update_info.append((id_str, "Failed to set parameter '{}' (API Set method returned false)".format(reviewed_by_param_name))) # Escaped curly braces
                    else:
                         # Parameter exists but is not a text/string type
                         param_type = param.StorageType.ToString()
                         failed_update_info.append((id_str, "Parameter '{}' is not a Text/String parameter (Actual Type: {})".format(reviewed_by_param_name, param_type))) # Escaped curly braces

            except Exception as e:
                # Catch any unexpected error during parameter access or update for this element
                failed_update_info.append((id_str, "Unexpected error processing element parameter: {}".format(e))) # Escaped curly braces

# --- Report Results ---
update_attempted_count = len(lines) - 1 # Total data lines attempted
success_count = update_attempted_count - len(not_found_ids) - len(failed_update_info)

print("# --- Parameter Update Summary ---") # Escaped
print("# Parameter Name: '{}'".format(reviewed_by_param_name)) # Escaped curly braces
print("# Total IDs Processed: {}".format(update_attempted_count)) # Escaped curly braces
# print("# Successfully updated (assumed): {}".format(success_count)) # Potential ambiguity if Set returns false but no exception

if not_found_ids:
    print("# Element IDs Not Found in Project ({}):".format(len(not_found_ids))) # Escaped curly braces
    for missing_id in not_found_ids:
        print("#   - {}".format(missing_id)) # Escaped curly braces
else:
    print("# All provided Element IDs were found in the project.") # Escaped

if failed_update_info:
    print("# Issues Encountered During Update ({}):".format(len(failed_update_info))) # Escaped curly braces
    for failed_id, reason in failed_update_info:
        print("#   - ID {}: {}".format(failed_id, reason)) # Escaped curly braces
else:
     if update_attempted_count > len(not_found_ids): # Check if there were any found elements to attempt updates on
        print("# No update issues reported for found elements.") # Escaped
     elif update_attempted_count == 0:
         print("# No data lines found in input.") # Escaped
     else: # Only case left is all IDs were not found
         print("# No elements were updated as none of the provided IDs were found.")


# Example of how to potentially access the successfully updated elements if needed later
# Note: This requires re-fetching or storing elements during the update loop if detail needed
# print("# (This script assumes updates occurred within an external transaction)") # Escaped