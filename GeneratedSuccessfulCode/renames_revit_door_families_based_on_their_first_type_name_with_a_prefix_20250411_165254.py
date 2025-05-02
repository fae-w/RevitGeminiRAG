# Purpose: This script renames Revit door families based on their first type name with a prefix.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Family,
    FamilySymbol,
    ElementId,
    Element
)

# --- Script Core Logic ---

# Assumption: The request is to rename the parent 'Family' element.
# The 'Type Name' used for the new family name will be the name of the *first* FamilySymbol (type) found within that family.
# If a family contains no types (unlikely for loadable families like doors), it will be skipped.

TARGET_PREFIX = "DR_"
families_processed = 0
families_renamed = 0
families_skipped_no_types = 0
families_already_correct = 0
families_error = 0

# Collect all Family elements of the 'Doors' category
family_collector = FilteredElementCollector(doc).OfClass(Family)

# Filter for the correct category (Family elements don't directly have a Category property like instances/types)
# We need to check the category of their types or use the FamilyCategory property if available and reliable.
# A safer way is often to collect types (FamilySymbol) and get their parent Family.
door_family_ids = set()
symbol_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).OfClass(FamilySymbol).WhereElementIsElementType()
for symbol in symbol_collector:
    try:
        # Check if symbol and its family are valid
        if symbol and symbol.Family:
             door_family_ids.add(symbol.Family.Id)
    except Exception as e:
        # print("# Warning: Could not process symbol ID {}. Error: {}".format(symbol.Id, e)) # Debug
        pass # Ignore symbols that cause issues

# Now iterate through the unique Family IDs collected
for family_id in door_family_ids:
    try:
        family = doc.GetElement(family_id)
        if not isinstance(family, Family):
            # print("# Warning: Element ID {} is not a Family.".format(family_id)) # Debug
            continue # Skip if it's somehow not a family

        families_processed += 1
        current_family_name = family.Name

        # Get the IDs of the types (FamilySymbol) within this family
        type_ids = family.GetFamilySymbolIds() # Returns ICollection<ElementId>

        if not type_ids or type_ids.Count == 0:
            # print("# Info: Family '{}' (ID: {}) has no types, skipping.".format(current_family_name, family.Id)) # Debug
            families_skipped_no_types += 1
            continue

        # Get the name of the first type found
        first_type_id = list(type_ids)[0] # Convert ICollection to list to get first element
        first_type = doc.GetElement(first_type_id)

        if not isinstance(first_type, FamilySymbol):
            # print("# Warning: First type ID {} for Family '{}' is not a FamilySymbol.".format(first_type_id, current_family_name)) # Debug
            families_error += 1
            continue

        first_type_name = first_type.Name
        new_family_name = TARGET_PREFIX + first_type_name

        # Check if renaming is needed
        if current_family_name != new_family_name:
            try:
                # Rename the family
                family.Name = new_family_name
                families_renamed += 1
                # print("# Renamed Family '{}' to '{}'".format(current_family_name, new_family_name)) # Debug
            except Exception as rename_err:
                # Handle potential errors during renaming (e.g., duplicate names)
                # print("# Error renaming Family '{}' (ID: {}) to '{}': {}".format(current_family_name, family.Id, new_family_name, rename_err)) # Debug
                families_error += 1
        else:
            # print("# Info: Family '{}' already has the desired name format.".format(current_family_name)) # Debug
            families_already_correct += 1

    except Exception as family_proc_err:
        # print("# Error processing Family ID {}: {}".format(family_id, family_proc_err)) # Debug
        families_error += 1

# Optional: Print summary (will appear in RevitPythonShell output window)
# print("--- Door Family Renaming Summary ---")
# print("Families Processed: {}".format(families_processed))
# print("Families Renamed: {}".format(families_renamed))
# print("Families Already Correct: {}".format(families_already_correct))
# print("Families Skipped (No Types): {}".format(families_skipped_no_types))
# print("Errors Encountered: {}".format(families_error))
# print("Total Unique Door Families Found: {}".format(len(door_family_ids)))