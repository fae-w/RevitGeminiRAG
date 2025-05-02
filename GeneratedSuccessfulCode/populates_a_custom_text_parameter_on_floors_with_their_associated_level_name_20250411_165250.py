# Purpose: This script populates a custom text parameter on floors with their associated level name.

﻿# Mandatory Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Floor,
    Parameter,
    BuiltInParameter,
    ElementId,
    Level,
    StorageType
)
# No clr needed for these standard Revit API types
# No System imports needed

# --- Parameters ---
# Define the name of the custom text parameter to be populated.
target_param_name = "Floor Level Text"

# --- Script Core Logic ---

# Create a collector for Floor instances in the document
floor_collector = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_Floors)\
    .WhereElementIsNotElementType()

# Counters for feedback (optional, useful for debugging/logging if needed later)
processed_count = 0
skipped_no_level_count = 0
skipped_no_target_param_count = 0
skipped_target_param_wrong_type_count = 0
skipped_target_param_readonly_count = 0
error_count = 0

# Iterate through each floor element found
for floor in floor_collector:
    # Basic check to ensure it's a Floor object (though collector should handle this)
    if not isinstance(floor, Floor):
        continue

    try:
        # --- 1. Get Source Value (Level Name) ---
        level_name = None
        level_param = floor.get_Parameter(BuiltInParameter.LEVEL_PARAM) # Parameter containing the floor's associated Level

        if level_param and level_param.HasValue:
            level_id = level_param.AsElementId()
            # Check if the ElementId is valid (not InvalidElementId)
            if level_id and level_id != ElementId.InvalidElementId:
                level_element = doc.GetElement(level_id)
                # Check if the retrieved element is actually a Level
                if isinstance(level_element, Level):
                    level_name = level_element.Name # Get the Level's name

        # Proceed only if we successfully obtained a level name
        if level_name:
            # --- 2. Get Target Parameter ---
            # Use LookupParameter for potentially faster access if name uniqueness is assumed
            target_param = floor.LookupParameter(target_param_name)

            if target_param:
                # --- 3. Validate Target Parameter ---
                if target_param.IsReadOnly:
                    # Target parameter is read-only
                    skipped_target_param_readonly_count += 1
                elif target_param.StorageType == StorageType.String:
                    # --- 4. Set Target Value ---
                    # Transaction is handled externally by the C# wrapper
                    current_value = target_param.AsString()
                    # Set value only if it's different to avoid unnecessary operations
                    if current_value != level_name:
                         target_param.Set(level_name)
                    processed_count += 1
                else:
                    # Target parameter exists but is not a Text parameter
                    skipped_target_param_wrong_type_count += 1
            else:
                # Target parameter not found on this floor instance
                skipped_no_target_param_count += 1
        else:
            # Could not retrieve a valid level name for this floor
            skipped_no_level_count += 1

    except Exception as e:
        # Catch any unexpected errors during processing of a single floor
        error_count += 1
        # Example of logging the error (optional, will print in RPS/pyRevit console)
        # print("Error processing Floor ID {}: {}".format(floor.Id, str(e)))

# --- Optional: Print summary (useful for debugging in RPS/pyRevit) ---
# total_floors = floor_collector.GetElementCount()
# print("--- Floor Level Parameter Update Summary ---")
# print("Total Floors found: {}".format(total_floors))
# print("Successfully processed/updated: {}".format(processed_count))
# print("Skipped (No valid Level found): {}".format(skipped_no_level_count))
# print("Skipped (Target parameter '{}' not found): {}".format(target_param_name, skipped_no_target_param_count))
# print("Skipped (Target parameter '{}' not Text type): {}".format(target_param_name, skipped_target_param_wrong_type_count))
# print("Skipped (Target parameter '{}' is read-only): {}".format(target_param_name, skipped_target_param_readonly_count))
# print("Errors encountered during processing: {}".format(error_count))
# print("-----------------------------------------")