# Purpose: This script retrieves and prints the insertion points of family instances of a specified type in a Revit document.

# Purpose: This script retrieves and prints the insertion points of all family instances of a specified type in a Revit document.

﻿import clr
clr.AddReference('System.Collections') # Required for IList<T>
from System.Collections.Generic import IList

# Import necessary Revit API classes
from Autodesk.Revit.DB import FilteredElementCollector, FamilyInstance, FamilySymbol, LocationPoint, XYZ, Transform, FamilyPointPlacementReference

# Define the target family type name
target_family_type_name = "Desk"

# Collect all FamilyInstance elements in the document
collector = FilteredElementCollector(doc).OfClass(FamilyInstance).WhereElementIsNotElementType()

print("Location points for Family Instances of type '{}':".format(target_family_type_name)) # Escaped format

found_instances = False

for instance in collector:
    if isinstance(instance, FamilyInstance):
        try:
            # Get the FamilySymbol (type) of the instance
            symbol = instance.Symbol
            if symbol is not None and symbol.Name == target_family_type_name:
                found_instances = True
                # --- Method 1: Get standard insertion point ---
                location = instance.Location
                if isinstance(location, LocationPoint):
                    point = location.Point
                    print("  Instance ID: {} - Insertion Point: ({:.3f}, {:.3f}, {:.3f})".format(instance.Id, point.X, point.Y, point.Z)) # Escaped format and variables

                # --- Method 2: Get Family Point Placement References (Relevant for specific family types like panels, adaptive components) ---
                # Uncomment the following lines if you need placement points instead of the standard insertion point
                # placement_references = instance.GetFamilyPointPlacementReferences()
                # if placement_references is not None and placement_references.Count > 0:
                #     print("  Instance ID: {} - Placement Points:".format(instance.Id)) # Escaped format
                #     for i, placement_ref in enumerate(placement_references):
                #         if isinstance(placement_ref, FamilyPointPlacementReference):
                #             transform = placement_ref.Location # This is a Transform
                #             origin = transform.Origin # This is an XYZ point
                #             print("    Point {}: ({:.3f}, {:.3f}, {:.3f})".format(i + 1, origin.X, origin.Y, origin.Z)) # Escaped format and variables
                # else:
                #    # Handle cases where the primary location might not be LocationPoint
                #    # or if placement references are expected but not found.
                #    if not isinstance(location, LocationPoint):
                #         print("  Instance ID: {} - Location is not a Point (Type: {})".format(instance.Id, location.GetType().Name)) # Escaped format
        except Exception as e:
            print("# Error processing instance {}: {}".format(instance.Id, e)) # Escaped format

if not found_instances:
    print("# No Family Instances of type '{}' found in the document.".format(target_family_type_name)) # Escaped format