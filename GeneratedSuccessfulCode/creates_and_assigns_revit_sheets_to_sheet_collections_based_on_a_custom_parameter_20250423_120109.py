# Purpose: This script creates and assigns Revit sheets to sheet collections based on a custom parameter.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String comparison, Exception handling

from Autodesk.Revit.DB import (
    SheetCollection,
    FilteredElementCollector,
    ViewSheet,
    Parameter,
    ElementId,
    BuiltInCategory # Although not directly used for filtering, good practice to import if related context
)
import System # For String comparison, Exception handling

# --- Configuration ---
# List of names for the Sheet Collections (Sheet Sets) to create
sheet_collection_names = ['Block 35 Submittal', 'Block 43 Submittal', 'Upper Levels Submittal']
# The exact name of the custom sheet parameter used for assignment logic
custom_parameter_name = "Building Area"
# Dictionary to store created Sheet Collection names and their corresponding ElementIds
created_collections = {}

# --- Step 1: Create Sheet Collections ---
print("# Attempting to create Sheet Collections...")
creation_errors = False
for name in sheet_collection_names:
    # Check if a collection with the same name already exists
    existing_collections = FilteredElementCollector(doc).OfClass(SheetCollection).ToElements()
    found_existing = False
    existing_id = ElementId.InvalidElementId
    for existing_col in existing_collections:
        if existing_col.Name == name:
            print("# Sheet Collection '{}' already exists (ID: {}). Using existing.".format(name, existing_col.Id))
            created_collections[name] = existing_col.Id
            found_existing = True
            break

    if not found_existing:
        try:
            # Transaction is handled by the C# wrapper
            new_collection = SheetCollection.Create(doc, name)
            if new_collection:
                created_collections[name] = new_collection.Id
                print("# Successfully created Sheet Collection: '{}' (ID: {})".format(name, new_collection.Id))
            else:
                # This case might be rare if Create doesn't throw exceptions but returns null
                print("# Error: SheetCollection.Create returned None for name '{}'.".format(name))
                created_collections[name] = ElementId.InvalidElementId # Mark as failed
                creation_errors = True
        except System.Exception as create_ex:
            # Catch Revit API exceptions or general exceptions
            print("# Error creating Sheet Collection '{}': {}".format(name, create_ex.Message))
            created_collections[name] = ElementId.InvalidElementId # Mark as failed
            creation_errors = True

# Check if any collections failed creation or were not found/created
if not created_collections or any(col_id == ElementId.InvalidElementId for col_id in created_collections.values()):
    print("# Warning: Not all requested Sheet Collections could be created or found. Assignment might be incomplete.")
    # Proceed with assignment for the collections that were successfully created/found

# --- Step 2: Assign Sheets to Collections ---
print("# Attempting to assign sheets based on parameter '{}'...".format(custom_parameter_name))
# Collect all ViewSheet elements in the project
sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)
assigned_count = 0
skipped_count = 0
error_count = 0

# Iterate through all sheets in the project
for sheet in sheet_collector:
    # Ensure it's a ViewSheet instance (though FilteredElementCollector should handle this)
    if not isinstance(sheet, ViewSheet):
        continue

    try:
        # Find the custom parameter on the sheet
        # Using LookupParameter is generally faster if the parameter name is unique
        param = sheet.LookupParameter(custom_parameter_name)
        # Alternative if multiple parameters could have the same name:
        # params = sheet.GetParameters(custom_parameter_name)
        # param = params[0] if params else None

        if param and param.HasValue:
            # Get the parameter value as a string.
            # Assumption: The 'Building Area' parameter stores the exact name of the target Sheet Collection as a string.
            param_value_obj = param.AsObject() # Get as object first to handle different storage types potentially
            param_value_str = ""
            if param_value_obj is not None:
                 # Convert ElementId value (if lookup parameter) to element name or handle string directly
                 if isinstance(param_value_obj, ElementId):
                     linked_element = doc.GetElement(param_value_obj)
                     if linked_element:
                         param_value_str = linked_element.Name
                     else:
                         param_value_str = "" # ID doesn't point to a valid element
                 elif isinstance(param_value_obj, str):
                     param_value_str = param_value_obj
                 else:
                     # Attempt to convert other types to string, might need specific handling
                     param_value_str = str(param_value_obj)

            # Clean up potential whitespace
            param_value_str = param_value_str.strip() if param_value_str else ""

            # Check if the parameter value matches one of the target collection names
            if param_value_str and param_value_str in created_collections:
                target_collection_id = created_collections[param_value_str]

                # Ensure the target collection was successfully created/found
                if target_collection_id != ElementId.InvalidElementId:
                    # Check if the sheet is already assigned to the correct collection
                    current_collection_id = sheet.SheetCollectionId
                    if current_collection_id != target_collection_id:
                        try:
                            # Assign the sheet to the target collection
                            # Transaction is handled by the C# wrapper
                            sheet.SheetCollectionId = target_collection_id
                            # print("# Assigned Sheet '{}' (ID: {}) to Collection '{}'".format(sheet.SheetNumber, sheet.Id, param_value_str)) # Debug / Verbose
                            assigned_count += 1
                        except System.ArgumentException as assign_arg_ex:
                            # Handle cases like trying to assign Assembly Sheets, which is not allowed
                            print("# Error assigning sheet '{}' (ID: {}): {}. May be an Assembly Sheet or invalid ID.".format(sheet.SheetNumber, sheet.Id, assign_arg_ex.Message))
                            error_count += 1
                        except Exception as assign_ex:
                            print("# Unexpected error assigning sheet '{}' (ID: {}): {}".format(sheet.SheetNumber, sheet.Id, assign_ex))
                            error_count += 1
                    # else: # Optional: log sheets already correctly assigned
                    #    skipped_count += 1
                else:
                    # The collection this sheet should belong to was not created successfully
                    # print("# Skipping assignment for Sheet '{}': Target collection '{}' was not created or found.".format(sheet.SheetNumber, param_value_str)) # Debug / Verbose
                    skipped_count += 1
            else:
                # Parameter value does not match any target collection name or is empty
                # print("# Sheet '{}' parameter value ('{}') does not match any target collection name or is empty.".format(sheet.SheetNumber, param_value_str)) # Debug / Verbose
                skipped_count += 1
        else:
            # Sheet does not have the parameter, or the parameter has no value
            # print("# Sheet '{}' does not have parameter '{}' or it has no value.".format(sheet.SheetNumber, custom_parameter_name)) # Debug / Verbose
            skipped_count += 1

    except Exception as process_ex:
        # Catch any other errors during sheet processing
        print("# Error processing sheet '{}' (ID: {}): {}".format(sheet.SheetNumber, sheet.Id, process_ex))
        error_count += 1

# --- Final Summary ---
print("# Sheet assignment process finished.")
print("# Successfully assigned sheets: {}".format(assigned_count))
print("# Sheets skipped (no match, no param, already assigned): {}".format(skipped_count))
print("# Errors during assignment: {}".format(error_count))
if creation_errors:
    print("# Note: There were errors during Sheet Collection creation.")

# No data export is required for this task.