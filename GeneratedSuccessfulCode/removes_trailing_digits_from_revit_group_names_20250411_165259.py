# Purpose: This script removes trailing digits from Revit group names.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, Group

# Import regular expressions module for string manipulation
import re # Used for robust trailing number removal

# --- Helper function to remove trailing digits ---
def remove_trailing_digits(s):
    """Removes trailing digits and any subsequent trailing whitespace from a string."""
    if not s: # Handle empty or None strings
        return s
    # Use regex to find the last non-digit character's position
    match = re.search(r'\D\d*$', s)
    if match:
        # Found a non-digit followed by digits at the end
        # Keep up to the last non-digit
        # Example: "Group 123", match is 'p 123', last non-digit is ' ' at index 5. Keep s[:6]
        # Example: "MyGroup45", match is 'p45', last non-digit is 'p' at index 6. Keep s[:7]
        # Simpler: find the start of the first trailing digit
        original_length = len(s)
        temp_stripped = s.rstrip('0123456789')
        if len(temp_stripped) < original_length:
            # Digits were removed, now remove trailing whitespace
            return temp_stripped.rstrip()
        else:
            # No trailing digits found, return original (potentially stripping existing whitespace)
            return s.rstrip()
    elif s.isdigit():
         # String consists only of digits
         return "" # Remove everything
    else:
        # String has no trailing digits
        return s.rstrip() # Still strip potential trailing whitespace


# --- Script Core Logic ---

# Collect all Group instances in the project
collector = FilteredElementCollector(doc).OfClass(Group).WhereElementIsNotElementType()

groups_to_process = list(collector) # Convert iterator to list

renamed_count = 0
skipped_count = 0
error_count = 0

for group in groups_to_process:
    # Ensure it's a Group object (collector should handle this)
    if not isinstance(group, Group):
        continue

    try:
        current_name = group.Name
        if not current_name:
            # Skip groups with no name
            skipped_count += 1
            continue

        # Calculate the new name by removing trailing digits and whitespace
        new_name = remove_trailing_digits(current_name)

        # Check if rename is needed and the new name is not empty
        if new_name and new_name != current_name:
            # Rename the group
            group.Name = new_name
            renamed_count += 1
            # print("# Renamed Group ID {} from '{}' to '{}'".format(group.Id, current_name, new_name)) # Debug
        else:
            # Skipped because name didn't change or became empty
            skipped_count += 1
            # if not new_name:
            #    print("# Skipped Group ID {}: Name '{}' would become empty after removing digits.".format(group.Id, current_name)) # Debug
            # else:
            #    print("# Skipped Group ID {}: Name '{}' has no trailing digits.".format(group.Id, current_name)) # Debug


    except Exception as e:
        # Log any errors during processing a specific group
        # print("# Error processing Group ID {}: {}".format(group.Id, e)) # Debug
        error_count += 1

# Optional: Print summary (commented out)
# print("--- Group Renaming Summary ---")
# print("Successfully renamed: {}".format(renamed_count))
# print("Skipped (no change needed or empty name): {}".format(skipped_count))
# print("Errors encountered: {}".format(error_count))
# print("Total Groups processed: {}".format(len(groups_to_process)))