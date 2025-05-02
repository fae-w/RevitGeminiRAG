# Purpose: This script selects generic annotation instances based on a case-insensitive family name search.

# Purpose: This script selects generic annotation family instances based on a case-insensitive search of their family names.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    FamilySymbol,
    Family,
    ElementId
)

# Search text (case-insensitive)
search_text = "tbc"

# List to store the ElementIds of the matching generic annotation instances
matching_instance_ids = []

# Collect all FamilyInstance elements in the document
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType()

# Iterate through the generic annotation instances
for instance in collector:
    if isinstance(instance, FamilyInstance):
        try:
            # Get the FamilySymbol associated with the instance
            symbol = instance.Symbol
            if symbol and isinstance(symbol, FamilySymbol):
                # Get the Family from the FamilySymbol
                family = symbol.Family
                if family and isinstance(family, Family):
                    family_name = family.Name
                    # Check if the family name contains the search text (case-insensitive)
                    if search_text in family_name.lower():
                        matching_instance_ids.append(instance.Id)
        except Exception as e:
            # Silently ignore elements that cause errors during processing
            # print(f"# Debug: Error processing instance {instance.Id}. Error: {e}") # Escaped
            pass

# Check if any matching instances were found
if matching_instance_ids:
    # Convert the Python list to a .NET List<ElementId>
    selection_list = List[ElementId](matching_instance_ids)
    try:
        # Set the selection in the UI
        uidoc.Selection.SetElementIds(selection_list)
        # Optional: print confirmation
        # print(f"# Selected {len(matching_instance_ids)} generic annotation instances whose family name contains '{search_text.upper()}'.") # Escaped
    except Exception as sel_ex:
        print(f"# Error setting selection: {sel_ex}") # Escaped
#else:
    # Optional: print message if none found
    # print(f"# No generic annotation instances found whose family name contains '{search_text.upper()}'.") # Escaped
    # pass