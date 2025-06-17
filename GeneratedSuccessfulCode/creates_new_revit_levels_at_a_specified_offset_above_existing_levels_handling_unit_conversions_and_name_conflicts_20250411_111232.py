# Purpose: This script creates new Revit levels at a specified offset above existing levels, handling unit conversions and name conflicts.

# Purpose: This script creates new Revit levels at a specified offset above existing levels, handling unit conversions and name conflicts robustly.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    UnitUtils,
    UnitTypeId, # Assumed available in Autodesk.Revit.DB
    BuiltInParameter,
    StorageType
)

# Define the levels to create: dictionary mapping base level name to new level name
level_creation_info = {
    "Level 1": "Level 1 Mezzanine",
    "Level 2": "Level 2 Mezzanine"
}

# Height offset in millimeters
height_offset_mm = 5000.0

# Convert height offset from mm to feet
height_offset_feet = 0.0
try:
    # Try using UnitTypeId constants (preferred)
    mm_unit_id = UnitTypeId.Millimeters
    feet_unit_id = UnitTypeId.Feet
    height_offset_feet = UnitUtils.Convert(height_offset_mm, mm_unit_id, feet_unit_id)
    # print(f"# Debug: Offset converted using UnitTypeId: {{height_offset_mm}} mm = {{height_offset_feet:.4f}} ft") # Escaped
except AttributeError:
    print("# Warning: UnitTypeId.Millimeters or UnitTypeId.Feet not found. Using manual conversion.")
    # Manual conversion: 1 inch = 25.4 mm, 1 foot = 12 inches
    mm_to_feet_conversion = 1.0 / (25.4 * 12.0)
    height_offset_feet = height_offset_mm * mm_to_feet_conversion
    # print(f"# Debug: Offset converted manually: {{height_offset_mm}} mm = {{height_offset_feet:.4f}} ft") # Escaped
except Exception as e:
    print("# Error during unit conversion using UnitTypeId: {0}. Falling back to manual conversion.".format(e))
    # Fallback manual conversion
    mm_to_feet_conversion = 1.0 / (25.4 * 12.0)
    height_offset_feet = height_offset_mm * mm_to_feet_conversion
    # print(f"# Debug: Offset converted manually after error: {{height_offset_mm}} mm = {{height_offset_feet:.4f}} ft") # Escaped


# Helper function to get level name robustly
def get_level_name(level):
    if not isinstance(level, Level):
        return None
    try:
        # Prefer DATUM_TEXT for level name
        name_param = level.get_Parameter(BuiltInParameter.DATUM_TEXT)
        if name_param and name_param.HasValue:
            return name_param.AsString()
        # Fallback to LEVEL_NAME
        name_param = level.get_Parameter(BuiltInParameter.LEVEL_NAME)
        if name_param and name_param.HasValue:
            return name_param.AsString()
        # Generic Name parameter as another fallback
        name_param = level.LookupParameter("Name")
        if name_param and name_param.HasValue:
            return name_param.AsString()
        # Direct .Name property as last resort (might differ from DATUM_TEXT)
        # Check if Name property exists before accessing
        if hasattr(level, 'Name'):
             return level.Name
        return None # Cannot determine name
    except Exception as e:
        # print(f"# Debug: Error getting name for Level ID {{level.Id}}: {{e}}") # Escaped
        return None # Error retrieving name

# Collect all existing levels and store them in a dictionary by name
existing_levels = {}
collector = FilteredElementCollector(doc).OfClass(Level)
for lvl in collector:
    level_name = get_level_name(lvl)
    if level_name:
        # Handle potential duplicate names by storing a list, though less likely for levels
        if level_name not in existing_levels:
             existing_levels[level_name] = []
        existing_levels[level_name].append(lvl)
    # else: # Optional debug for levels without names
        # print(f"# Debug: Could not get name for Level ID {{lvl.Id}}") # Escaped

# Process each requested level creation
for base_name, new_name in level_creation_info.items():

    # Find the base level
    base_level_list = existing_levels.get(base_name)
    if not base_level_list:
        print("# Error: Base level '{0}' not found. Skipping creation of '{1}'.".format(base_name, new_name))
        continue
    if len(base_level_list) > 1:
        print("# Warning: Multiple levels found named '{0}'. Using the first one found (ID: {1}).".format(base_name, base_level_list[0].Id))
        # Potentially add logic here to select based on elevation if needed, but using the first is simplest
    base_level = base_level_list[0]


    # Check if the new level name already exists
    if new_name in existing_levels:
        # Get the ID of the first existing level with that name for the error message
        existing_id = existing_levels[new_name][0].Id if existing_levels[new_name] else "Unknown"
        print("# Error: A level named '{0}' already exists (ID: {1}). Skipping creation.".format(new_name, existing_id))
        continue

    # Calculate the elevation for the new level
    try:
        base_elevation_feet = base_level.Elevation
        new_elevation_feet = base_elevation_feet + height_offset_feet
    except Exception as e:
        print("# Error calculating elevation for '{0}' based on '{1}': {2}".format(new_name, base_name, e))
        continue

    # Create the new level
    new_level = None
    try:
        # Check if a level exists at nearly the same elevation
        elevation_tolerance = 0.001 # feet, adjust as needed
        found_existing_at_elevation = False
        for level_list in existing_levels.values():
            for lvl in level_list:
                if abs(lvl.Elevation - new_elevation_feet) < elevation_tolerance:
                    print("# Error: A level (ID: {0}, Name: '{1}') already exists at or very close to the target elevation {2:.4f} ft for '{3}'. Skipping creation.".format(
                          lvl.Id, get_level_name(lvl) or "Unnamed", new_elevation_feet, new_name))
                    found_existing_at_elevation = True
                    break
            if found_existing_at_elevation:
                break

        if found_existing_at_elevation:
            continue # Skip to next level creation defined in dictionary

        # Proceed with creation if no elevation conflict found
        new_level = Level.Create(doc, new_elevation_feet)
        if new_level:
            # Set the name of the new level
            try:
                # Use DATUM_TEXT parameter first
                name_param = new_level.get_Parameter(BuiltInParameter.DATUM_TEXT)
                if name_param is None or not name_param.StorageType == StorageType.String or name_param.IsReadOnly:
                     # Fallback to LEVEL_NAME
                     name_param = new_level.get_Parameter(BuiltInParameter.LEVEL_NAME)
                if name_param is None or not name_param.StorageType == StorageType.String or name_param.IsReadOnly:
                     # Fallback to generic "Name"
                     name_param = new_level.LookupParameter("Name")

                if name_param and name_param.StorageType == StorageType.String and not name_param.IsReadOnly:
                     name_param.Set(new_name)
                     print("# Successfully created level '{0}' (ID: {1}) at elevation {2:.4f} ft.".format(new_name, new_level.Id, new_elevation_feet))
                     # Add the newly created level to our dictionary for subsequent checks
                     if new_name not in existing_levels:
                         existing_levels[new_name] = []
                     existing_levels[new_name].append(new_level)
                else:
                     print("# Warning: Could not find writable name parameter (DATUM_TEXT, LEVEL_NAME, or 'Name') for the new level '{0}' (ID: {1}). Name might be default.".format(new_name, new_level.Id))

            except Exception as name_ex:
                 print("# Error setting name for new level (intended: '{0}', ID: {1}): {2}".format(new_name, new_level.Id, name_ex))
        else:
            # Level.Create might return None if elevation is too close to existing (though checked above) or other API internal reasons
             print("# Error: Level.Create returned None for '{0}' at elevation {1:.4f} ft. Check Revit logs for details.".format(new_name, new_elevation_feet))

    except Exception as create_ex:
        # Catch exceptions specifically from Level.Create (e.g., duplicate elevation if check fails, or other API errors)
        print("# Error during Level.Create for '{0}' at elevation {1:.4f} ft: {2}".format(new_name, new_elevation_feet, create_ex))