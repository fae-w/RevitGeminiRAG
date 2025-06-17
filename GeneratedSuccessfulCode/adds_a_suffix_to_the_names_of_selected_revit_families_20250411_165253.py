# Purpose: This script adds a suffix to the names of selected Revit families.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    Family,
    ElementId,
    Element
)
from System.Collections.Generic import ICollection

# --- Script Core Logic ---

# Get the currently selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

renamed_count = 0
skipped_count = 0
error_count = 0
suffix = "_ToBeReviewed"

if not selected_ids or selected_ids.Count == 0:
    # print("# No elements selected.") # Debug: No elements selected
    pass # Exit gracefully if nothing is selected
else:
    for element_id in selected_ids:
        try:
            element = doc.GetElement(element_id)

            # Check if the selected element is a Family
            if isinstance(element, Family):
                family = element
                try:
                    current_name = family.Name
                    new_name = current_name + suffix

                    # Check if rename is actually needed (optional, but good practice)
                    if new_name != current_name:
                        # Attempt to rename the family (Transaction handled externally)
                        family.Name = new_name
                        renamed_count += 1
                        # print(f"# Renamed Family ID {family.Id}: '{current_name}' to '{new_name}'") # Debug
                    else:
                        # Skipped because the name is already correct or suffix is empty
                        skipped_count += 1
                        # print(f"# Skipped Family ID {family.Id}: Name already ends with suffix or suffix is empty.") # Debug

                except Exception as rename_error:
                    # Handle potential errors during renaming (e.g., duplicate names, invalid characters)
                    error_count += 1
                    # print(f"# Error renaming Family ID {family.Id} ('{current_name}' to '{new_name}'): {rename_error}") # Debug
            else:
                # The selected element is not a Family, skip it
                skipped_count += 1
                # print(f"# Skipped Element ID {element_id}: Not a Family element.") # Debug

        except Exception as get_element_error:
            # Handle potential errors retrieving the element
            error_count += 1
            # print(f"# Error processing selected Element ID {element_id}: {get_element_error}") # Debug

# Optional: Print summary (commented out by default as per instructions)
# print("--- Family Renaming Summary ---")
# print(f"Total Selected Elements: {selected_ids.Count}")
# print(f"Families Successfully Renamed: {renamed_count}")
# print(f"Elements Skipped (Not Families or Already Correct): {skipped_count}")
# print(f"Errors Encountered: {error_count}")