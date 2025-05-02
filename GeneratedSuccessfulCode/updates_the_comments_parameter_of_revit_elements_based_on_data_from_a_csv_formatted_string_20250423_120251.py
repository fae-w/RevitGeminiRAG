# Purpose: This script updates the 'Comments' parameter of Revit elements based on data from a CSV-formatted string.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import Element, ElementId, BuiltInParameter, Parameter
import sys

# --- Input Data ---
# Format: Comma-separated values (CSV). First line is header, subsequent lines are ID,Comment
input_data = """ID,Comment
11111,Needs Verification
22222,Approved
33333,Needs Verification"""
# --- End Input Data ---

# --- Processing ---
processed_count = 0
error_count = 0
error_messages = []

# Split the input data into lines and remove leading/trailing whitespace
lines = input_data.strip().split('\n')

# Skip the header row (first line)
data_lines = lines[1:]

# Iterate through each data line
for line in data_lines:
    line = line.strip()
    if not line:
        continue # Skip empty lines

    try:
        # Split the line by the first comma only to handle comments containing commas
        parts = line.split(',', 1)
        if len(parts) != 2:
            error_messages.append("# Warning: Skipping malformed line (expected ID,Comment): {}".format(line))
            error_count += 1
            continue

        id_str, comment_value = parts
        comment_value = comment_value.strip() # Remove potential whitespace around the comment

        # Attempt to convert the ID string to an integer
        try:
            target_element_id_int = int(id_str.strip())
        except ValueError:
            error_messages.append("# Warning: Skipping line due to invalid Element ID format: {}".format(line))
            error_count += 1
            continue

        # Construct the ElementId
        target_element_id = ElementId(target_element_id_int)

        # Get the element from the document
        element = doc.GetElement(target_element_id)

        if element:
            # Get the 'Comments' parameter (ALL_MODEL_INSTANCE_COMMENTS is common)
            comments_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

            # Fallback to lookup by name if BuiltInParameter fails or doesn't exist for the element type
            if not comments_param:
                comments_param = element.LookupParameter("Comments")

            # Check if the parameter exists and is not read-only
            if comments_param and not comments_param.IsReadOnly:
                # Set the new value for the 'Comments' parameter
                comments_param.Set(comment_value)
                processed_count += 1
            else:
                if not comments_param:
                    error_messages.append("# Error: 'Comments' parameter not found for element ID {}.".format(target_element_id_int))
                elif comments_param.IsReadOnly:
                    error_messages.append("# Error: 'Comments' parameter is read-only for element ID {}.".format(target_element_id_int))
                error_count += 1
        else:
            error_messages.append("# Error: Element with ID {} not found in the document.".format(target_element_id_int))
            error_count += 1

    except Exception as e:
        # Catch any other unexpected errors during processing of a line
        error_messages.append("# Error: An unexpected error occurred processing line '{}': {}".format(line, e))
        error_count += 1

# --- Optional: Print Summary ---
# Use print for feedback that won't interfere with EXPORT format (if it were used)
if error_messages:
    print("--- ERRORS/WARNINGS ---")
    for msg in error_messages:
        print(msg)
    print("----------------------")
# print("# Summary: Successfully updated comments for {} elements. {} lines had errors or were skipped.".format(processed_count, error_count))