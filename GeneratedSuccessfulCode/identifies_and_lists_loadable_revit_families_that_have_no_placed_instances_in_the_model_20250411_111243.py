# Purpose: This script identifies and lists loadable Revit families that have no placed instances in the model.

# Purpose: This script identifies and lists loadable Revit families that have no placed instances in the model.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, Family, FamilySymbol, FamilyInstance, ElementId

# --- Step 1: Find all used FamilySymbol IDs ---

# Collect all placed FamilyInstance elements in the document
all_instances_collector = FilteredElementCollector(doc).OfClass(FamilyInstance).WhereElementIsNotElementType()

# Create a set to store the ElementIds of the FamilySymbols that are actually used by instances
used_symbol_ids = set()

# Iterate through all instances and collect their symbol IDs
for inst in all_instances_collector:
    try:
        # Get the FamilySymbol associated with the instance
        symbol = inst.Symbol
        if symbol and symbol.Id != ElementId.InvalidElementId:
            used_symbol_ids.add(symbol.Id)
    except Exception as e:
        # Silently ignore instances where the symbol cannot be retrieved
        # print(f"# Debug: Could not get symbol for instance {inst.Id}. Error: {e}") # Escaped
        pass

# --- Step 2: Find families where NONE of their symbols are used ---

# Collect all Family elements in the document
all_families_collector = FilteredElementCollector(doc).OfClass(Family)

# List to store the names of families that have no placed instances
unused_family_names = []

# Iterate through each family
for family in all_families_collector:
    try:
        # Consider only loadable families (typically editable)
        # This helps filter out some system families implicitly, although the main check is instance usage.
        if not family.IsEditable:
            continue

        is_used = False
        # Get all FamilySymbol IDs belonging to this family
        symbol_ids_in_family = family.GetFamilySymbolIds()

        # If the family has no symbols, it can be considered unused in terms of placement
        if not symbol_ids_in_family or symbol_ids_in_family.Count == 0:
             # Decide if families with zero symbols should be listed.
             # Let's assume they shouldn't be listed as 'unused placable' families.
             # If they should, uncomment the next line and handle the is_used logic.
             # is_used = False # Or treat as unused depending on definition
             continue # Skip families with no symbols

        # Check if ANY symbol from this family is in the set of used symbol IDs
        for symbol_id in symbol_ids_in_family:
            if symbol_id in used_symbol_ids:
                is_used = True
                break  # Found a used symbol, this family is used, move to the next family

        # If the loop finished without setting is_used to True, the family is unused
        if not is_used:
            unused_family_names.append(family.Name)

    except Exception as e:
        # Silently ignore families that cause errors during processing
        # print(f"# Debug: Error processing family '{family.Name}' ({family.Id}). Error: {e}") # Escaped
        pass

# --- Step 3: Prepare and print the output ---

# Sort the list alphabetically for better readability
unused_family_names.sort()

# Check if any unused families were found
if unused_family_names:
    # Prepare the text content for export
    output_lines = []
    output_lines.append("Unused Loadable Families (No Instances Placed)")
    output_lines.append("==============================================")
    output_lines.extend(unused_family_names)

    # Join lines into a single string
    file_content = "\n".join(output_lines)

    # Print the export header and the formatted data
    print("EXPORT::TXT::unused_families.txt")
    print(file_content)
else:
    # Print a message if no unused families are found
    print("# No unused loadable families found in the project.")