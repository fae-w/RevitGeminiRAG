# Purpose: This script creates a new level in Revit at a specified offset above an existing level.

# Purpose: This script creates a new level in Revit at a specified offset above an existing level.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    UnitUtils,
    UnitTypeId, # Assumed available in Autodesk.Revit.DB
    BuiltInParameter
)

# Constants
new_level_name = "Test Level"
base_level_name = "Level 1"
height_offset_meters = 4.0

# Find the base level ("Level 1")
base_level = None
collector = FilteredElementCollector(doc).OfClass(Level)
for level in collector:
    # Use Element.Name property common to many elements including Level
    # Check if the element is actually a Level and has a Name property before comparing
    if isinstance(level, Level):
        try:
            # Using GetName() method which is more robust than direct .Name access sometimes
            element_name_param = level.get_Parameter(BuiltInParameter.DATUM_TEXT) # Preferred parameter for Level name
            if element_name_param is None:
                 element_name_param = level.get_Parameter(BuiltInParameter.LEVEL_NAME) # Fallback parameter
            if element_name_param is None:
                 element_name_param = level.LookupParameter("Name") # Generic fallback

            if element_name_param and element_name_param.AsString() == base_level_name:
                 base_level = level
                 break
        except Exception as e:
             # print(f"# Debug: Error checking level name for ID {level.Id}: {e}") # Escaped
             pass # Skip problematic elements

if base_level:
    # Get the elevation of the base level (in feet)
    base_elevation_feet = base_level.Elevation

    # Convert the height offset from meters to feet using UnitUtils
    height_offset_feet = 0.0 # Initialize
    try:
        # Get ForgeTypeId constants for units from UnitTypeId
        meters_unit_id = UnitTypeId.Meters
        feet_unit_id = UnitTypeId.Feet
        height_offset_feet = UnitUtils.Convert(height_offset_meters, meters_unit_id, feet_unit_id)

    except AttributeError:
         print("# Warning: UnitTypeId.Meters or UnitTypeId.Feet not found. Using manual conversion.")
         meters_to_feet_conversion = 3.2808399 # More precise factor
         height_offset_feet = height_offset_meters * meters_to_feet_conversion
    except Exception as e:
        print("# Error during unit conversion using UnitTypeId: {0}. Falling back to manual conversion.".format(e))
        # Fallback manual conversion
        meters_to_feet_conversion = 3.2808399
        height_offset_feet = height_offset_meters * meters_to_feet_conversion

    # Calculate the elevation for the new level
    new_elevation_feet = base_elevation_feet + height_offset_feet

    # Check if a level with the target name already exists
    existing_level_with_name = None
    collector_check = FilteredElementCollector(doc).OfClass(Level)
    for lvl in collector_check:
         if isinstance(lvl, Level):
            try:
                elem_name_param = lvl.get_Parameter(BuiltInParameter.DATUM_TEXT)
                if elem_name_param is None:
                     elem_name_param = lvl.get_Parameter(BuiltInParameter.LEVEL_NAME)
                if elem_name_param is None:
                     elem_name_param = lvl.LookupParameter("Name")

                if elem_name_param and elem_name_param.AsString() == new_level_name:
                     existing_level_with_name = lvl
                     break
            except Exception:
                pass # Skip elements where name cannot be retrieved

    if existing_level_with_name:
         print("# Error: A level named '{0}' already exists (ID: {1}).".format(new_level_name, existing_level_with_name.Id))
    else:
        # Create the new level
        try:
            new_level = Level.Create(doc, new_elevation_feet)
            if new_level:
                # Set the name of the new level using the correct parameter
                try:
                    # Use DATUM_TEXT parameter first, then fall back
                    name_param = new_level.get_Parameter(BuiltInParameter.DATUM_TEXT)
                    if name_param is None:
                         name_param = new_level.get_Parameter(BuiltInParameter.LEVEL_NAME)
                    if name_param is None:
                         # Less reliable fallback, but sometimes works if others fail
                         name_param = new_level.LookupParameter("Name")

                    if name_param and name_param.StorageType == StorageType.String and not name_param.IsReadOnly:
                         name_param.Set(new_level_name)
                         # print(f"# Successfully created level '{new_level_name}' (ID: {new_level.Id}) at elevation {new_elevation_feet:.4f} ft.") # Escaped
                    else:
                         print("# Warning: Could not find writable name parameter (DATUM_TEXT, LEVEL_NAME, or 'Name') for the new level. Name might be default.")

                except Exception as name_ex:
                     print("# Error setting name for new level {0}: {1}".format(new_level.Id, name_ex))
            else:
                print("# Error: Level.Create returned None. Possible elevation conflict or other issue.")
        except Exception as create_ex:
            # More specific error check for duplicate elevation could be added if API supports it easily,
            # but generally the API exception is informative enough.
            print("# Error creating level: {0}. Check if the elevation {1:.4f} ft conflicts with existing levels.".format(create_ex, new_elevation_feet))

else:
    print("# Error: Base level '{0}' not found in the document.".format(base_level_name))

# Note: StorageType needed importing if used. Let's import it.
from Autodesk.Revit.DB import StorageType # Import added for the check name_param.StorageType == StorageType.String