# Purpose: This script places a specified family instance at a given location on a specified level within a Revit project.

# Purpose: This script places a specific family instance at a designated location on a specified level in Revit.

﻿# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilySymbol,
    FamilyInstance,
    Level,
    XYZ,
    Element,
    BuiltInCategory,
    BuiltInParameter
)
# Import StructuralType for placing family instances
from Autodesk.Revit.DB.Structure import StructuralType

# --- Define Inputs ---
target_family_symbol_name = "Standard Desk"
target_level_name = "Level 1"
# Assuming the coordinates are provided in Revit's internal units (decimal feet).
# If these are intended to be millimeters or another unit, conversion is needed.
target_x = 10000.0
target_y = 5000.0
target_z = 0.0 # Note: Z coordinate is often relative to the Level's elevation

# --- Find the Family Symbol ---
target_symbol = None
collector_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol)
for symbol in collector_symbols:
    if symbol.Name == target_family_symbol_name:
        target_symbol = symbol
        # Ensure the symbol is active before placing an instance
        if not target_symbol.IsActive:
            try:
                target_symbol.Activate()
                # print(f"# Activated FamilySymbol: {target_symbol.Name}") # Escaped optional debug
            except Exception as activation_ex:
                print("# Error activating FamilySymbol '{}': {}".format(target_family_symbol_name, activation_ex))
                target_symbol = None # Prevent placement if activation failed
        break

# --- Find the Level ---
target_level = None
collector_levels = FilteredElementCollector(doc).OfClass(Level)
for level in collector_levels:
    # Access level name via parameter for robustness
    level_name_param = level.get_Parameter(BuiltInParameter.DATUM_TEXT)
    if level_name_param is None:
         level_name_param = level.get_Parameter(BuiltInParameter.LEVEL_NAME)
    if level_name_param is None:
         level_name_param = level.LookupParameter("Name") # Fallback

    if level_name_param and level_name_param.AsString() == target_level_name:
        target_level = level
        break

# --- Create the location point ---
# The Z coordinate is relative to the project origin, NOT the level elevation usually.
# To place it ON the level, we should use the level's elevation for Z.
# However, NewFamilyInstance overload taking a Level handles this.
# So, the input Z (0.0) might place it at project Z=0, not Level 1 elevation.
# For clarity, let's explicitly use the level's elevation if found.

if target_level:
    target_point = XYZ(target_x, target_y, target_level.Elevation)
else:
    # Fallback if level not found - use the provided Z coordinate relative to project origin
    target_point = XYZ(target_x, target_y, target_z)
    print("# Warning: Target level '{}' not found. Using Z coordinate {} relative to project origin.".format(target_level_name, target_z))


# --- Place the Family Instance ---
if target_symbol and target_level:
    try:
        # Use the overload that takes XYZ, FamilySymbol, Level, and StructuralType
        # This ensures the instance is associated with the correct level.
        # The XYZ point here defines the insertion point's coordinates.
        new_instance = doc.Create.NewFamilyInstance(target_point, target_symbol, target_level, StructuralType.NonStructural)

        if new_instance:
            # print(f"# Successfully placed instance of '{target_family_symbol_name}' (ID: {new_instance.Id}) on level '{target_level_name}' at ({target_point.X:.2f}, {target_point.Y:.2f}, {target_point.Z:.2f})") # Escaped optional success message
            pass # Success, no output needed unless requested
        else:
            print("# Error: Failed to create FamilyInstance. NewFamilyInstance returned None.")

    except Exception as e:
        print("# Error placing FamilyInstance: {}".format(e))
        # Possible reasons: Symbol not placeable, location issues, licensing, etc.

elif not target_symbol:
    print("# Error: Family Symbol '{}' not found or could not be activated in the document. Instance not placed.".format(target_family_symbol_name))
# Error message for level not found was handled during point creation