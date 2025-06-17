# Purpose: This script extracts and lists the Element IDs of mullion types used in a Revit project.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Mullion, ElementId

# Initialize a set to store unique Element IDs of used mullion types
used_mullion_type_ids = set()

# Create a collector for Mullion instances in the entire project
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType()

# Iterate through all mullion instances
for mullion_instance in collector:
    # Double-check if the element is indeed a Mullion instance
    if isinstance(mullion_instance, Mullion):
        try:
            # Get the ElementId of the mullion's type
            type_id = mullion_instance.GetTypeId()
            # Add the type ID to the set (duplicates are automatically handled)
            if type_id is not None and type_id != ElementId.InvalidElementId:
                used_mullion_type_ids.add(type_id)
        except Exception as e:
            # Log potential errors accessing type ID for a specific instance
            print("# Warning: Could not get TypeId for Mullion ID {}: {}".format(mullion_instance.Id, e))

# Check if any used types were found
if used_mullion_type_ids:
    print("# List of Element IDs for Mullion Types currently used in the project:")
    # Print each unique Element ID found
    for type_id in used_mullion_type_ids:
        print("# MullionType ID: {}".format(type_id.IntegerValue))
    print("# Total unique used Mullion Types found: {}".format(len(used_mullion_type_ids)))
else:
    # Print a message if no mullion instances were found or types couldn't be retrieved
    print("# No used Mullion Types found in the project (no Mullion instances placed or types invalid).")