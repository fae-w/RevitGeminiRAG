# Purpose: This script creates a specified number of new Revit sheets using the first available title block type found in the project.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Exception handling and ArgumentException
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, BuiltInCategory, ViewSheet, ElementId
import System # For Exception handling

# --- Configuration ---
number_of_sheets_to_create = 3

# --- Step 1: Find a suitable Title Block Type ID ---
# Revit doesn't have a single "default" title block setting accessible via API.
# We will find the first available Title Block type loaded in the project.
default_title_block_type_id = ElementId.InvalidElementId
collector_types = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()

# Get the elements and take the first one found
title_block_types = collector_types.ToElements()

if title_block_types:
    first_title_block_type = title_block_types[0]
    default_title_block_type_id = first_title_block_type.Id
    # print("# Using first found title block type: '{{}}' (ID: {{}})".format(first_title_block_type.Name, default_title_block_type_id)) # Debug
else:
    # If no title block types are loaded, we cannot create a sheet *with* a title block.
    # We could alternatively create sheets without title blocks using ElementId.InvalidElementId,
    # but the request specifically asked for the 'default project titleblock'.
    print("# Error: No Title Block types found in the project. Cannot create sheets with a title block.")
    # Set to None to prevent creation loop
    default_title_block_type_id = None

# --- Step 2: Create the new sheets ---
sheets_created_count = 0
if default_title_block_type_id and default_title_block_type_id != ElementId.InvalidElementId:
    for i in range(number_of_sheets_to_create):
        new_sheet = None
        try:
            # Transaction is handled by the C# wrapper
            new_sheet = ViewSheet.Create(doc, default_title_block_type_id)
            if new_sheet:
                sheets_created_count += 1
                # print("# Successfully created sheet {{}} of {{}}".format(i + 1, number_of_sheets_to_create)) # Debug
            else:
                print("# Error: ViewSheet.Create returned None on attempt {}.".format(i + 1))
                # Stop if one creation fails, as subsequent ones likely will too.
                break
        except System.ArgumentException as arg_ex:
            print("# Error creating sheet on attempt {}: {}. The title block ID might be invalid.".format(i + 1, arg_ex.Message))
            break # Stop if error occurs
        except Exception as create_ex:
            print("# Error creating sheet on attempt {}: {}".format(i + 1, create_ex))
            break # Stop if error occurs
    # print("# Finished attempting to create {{}} sheets. {{}} sheets created.".format(number_of_sheets_to_create, sheets_created_count)) # Optional final message

# No specific output or data export is required for this task.