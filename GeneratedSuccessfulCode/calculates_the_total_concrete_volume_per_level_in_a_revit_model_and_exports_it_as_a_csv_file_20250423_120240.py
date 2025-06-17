# Purpose: This script calculates the total concrete volume per level in a Revit model and exports it as a CSV file.

﻿# Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Level, Material, ElementId,
    ElementLevelFilter, UnitUtils, ForgeTypeId, UnitTypeId
)

# --- Configuration ---
# Case-insensitive search string for concrete materials
CONCRETE_SEARCH_TERM = "concrete"

# --- Find Concrete Material IDs ---
concrete_material_ids = []
mat_collector = FilteredElementCollector(doc).OfClass(Material)
for material in mat_collector:
    # Check if the material name contains the search term (case-insensitive)
    if CONCRETE_SEARCH_TERM in material.Name.lower():
        concrete_material_ids.append(material.Id)

if not concrete_material_ids:
    print("# Warning: No materials found containing '{}'. Cannot calculate volume.".format(CONCRETE_SEARCH_TERM))
    # Script will proceed but likely generate an empty report.

# --- Get All Levels ---
level_collector = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()
# Ensure levels is a list for sorting
levels = list(level_collector)
# Sort levels by elevation for ordered output
levels.sort(key=lambda l: l.Elevation)

# --- Calculate Concrete Volume per Level ---
level_concrete_volumes_ft3 = {} # Dictionary to store {Level Name: Volume in ft3}

if concrete_material_ids: # Only proceed if concrete materials were found
    for level in levels:
        level_id = level.Id
        level_name = level.Name
        level_total_volume_ft3 = 0.0

        # Filter elements associated with the current level
        # Assumption: Elements are associated with the level specified by their 'Level' parameter
        # (or equivalent base constraint). Multi-story elements' total volume might be attributed
        # entirely to their base level using this filter.
        level_filter = ElementLevelFilter(level_id)
        element_collector = FilteredElementCollector(doc)\
            .WherePasses(level_filter)\
            .WhereElementIsNotElementType() # Exclude element types

        for element in element_collector:
            try:
                # Check if the element supports material queries
                if not hasattr(element, "GetMaterialIds") or not hasattr(element, "GetMaterialVolume"):
                    continue

                # Get material IDs present in the element's geometry (not paint)
                element_material_ids = element.GetMaterialIds(False)

                if not element_material_ids: # Skip if element has no materials assigned
                    continue

                # Check if any of the identified concrete materials are in this element
                element_concrete_volume_ft3 = 0.0
                for mat_id in element_material_ids:
                    if mat_id in concrete_material_ids:
                        # Get the volume of this specific concrete material in this element
                        # Volume is returned in Revit's internal units (cubic feet)
                        material_volume = element.GetMaterialVolume(mat_id)
                        element_concrete_volume_ft3 += material_volume

                level_total_volume_ft3 += element_concrete_volume_ft3

            except Exception as e:
                # Handle potential errors during material/volume retrieval for specific elements
                # print("# Skipping Element ID {}: Error processing - {}".format(element.Id, e)) # Optional debug message
                pass # Silently skip problematic elements

        # Store the total volume for the level, even if it's zero
        level_concrete_volumes_ft3[level_name] = level_total_volume_ft3

# --- Prepare CSV Output ---
csv_lines = []
csv_lines.append("Level Name,Total Concrete Volume (m³)")

# Convert volumes and add to CSV lines only if concrete materials were found
if concrete_material_ids:
    volume_unit_type_found = True
    try:
        # Try accessing UnitTypeId - available in Revit 2021+
        _ = UnitTypeId.CubicMeters
    except AttributeError:
        volume_unit_type_found = False
        ft3_to_m3 = 0.0283168466 # Manual conversion factor as fallback
        print("# Warning: UnitTypeId.CubicMeters not found (requires Revit 2021+). Using manual conversion factor.")

    for level_name, volume_ft3 in level_concrete_volumes_ft3.items():
        # Convert volume from internal units (cubic feet) to cubic meters
        if volume_unit_type_found:
             volume_m3 = UnitUtils.ConvertFromInternalUnits(volume_ft3, UnitTypeId.CubicMeters)
        else:
             volume_m3 = volume_ft3 * ft3_to_m3 # Use fallback factor

        # Escape commas/quotes in level name for CSV robustness
        safe_level_name = level_name.replace('"', '""') # Double up existing quotes
        if ',' in safe_level_name or '"' in safe_level_name:
            safe_level_name = '"{}"'.format(safe_level_name) # Enclose in quotes if needed

        csv_lines.append("{},{:.3f}".format(safe_level_name, volume_m3))

# --- Print for Export ---
if len(csv_lines) > 1: # Check if we have data beyond the header
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::level_concrete_volume_summary.csv")
    print(file_content)
elif not concrete_material_ids:
     # Warning about missing materials was already printed
     print("# No concrete materials found, CSV export skipped.")
else:
    # Concrete materials existed, but no volume was found/calculated (or all levels had 0 volume)
    print("# No concrete volume found for any level, or all level volumes are zero.")
    # Still export the header row for consistency if needed
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::level_concrete_volume_summary.csv")
    print(file_content)