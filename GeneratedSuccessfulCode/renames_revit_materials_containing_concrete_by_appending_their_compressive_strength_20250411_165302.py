# Purpose: This script renames Revit materials containing 'Concrete' by appending their compressive strength.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for string checks

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Material,
    Element,
    ElementId,
    PropertySetElement,
    StructuralAsset,
    StructuralAssetClass,
    UnitTypeId, # Assumes Revit 2021+ for ForgeTypeId based units
    UnitUtils
)
# No user interaction needed, so no RevitAPIUI import

# --- Script Core Logic ---

target_keyword = "Concrete"
renamed_count = 0
skipped_no_concrete = 0
skipped_no_asset = 0
skipped_not_concrete_asset = 0
skipped_no_strength = 0
skipped_already_named = 0
error_count = 0

# Collect all Material elements
collector = FilteredElementCollector(doc).OfClass(Material)
materials = collector.ToElements()
total_materials = len(materials)

# Define the unit type for Megapascals
try:
    mpa_unit_type = UnitTypeId.Megapascals
except AttributeError:
    # Fallback or error handling for older Revit versions if needed
    # For simplicity, we assume UnitTypeId.Megapascals exists.
    # If this fails, the script might need adjustment for older UnitType/DisplayUnitType usage.
    print("# Error: Could not find UnitTypeId.Megapascals. This script might require Revit 2021+.")
    mpa_unit_type = None # Indicate failure

if mpa_unit_type:
    # Iterate through the collected materials
    for material in materials:
        if not isinstance(material, Material):
            continue

        try:
            current_name = Element.Name.GetValue(material)

            # Check if the material name contains the target keyword (case-insensitive)
            if target_keyword.lower() in current_name.lower():
                # Get the Structural Asset associated with the material
                structural_asset_id = material.StructuralAssetId
                structural_asset = None

                if structural_asset_id != ElementId.InvalidElementId:
                    prop_set_elem = doc.GetElement(structural_asset_id)
                    # Check if it's a PropertySetElement and retrieve the StructuralAsset
                    if isinstance(prop_set_elem, PropertySetElement):
                        structural_asset = prop_set_elem.GetStructuralAsset()

                if structural_asset:
                    # Check if the asset class is Concrete
                    if structural_asset.StructuralAssetClass == StructuralAssetClass.Concrete:
                        try:
                            # Get the concrete compressive strength (Fc') in internal units (psi)
                            fc_prime_internal = structural_asset.ConcreteCompression

                            # Convert the strength to Megapascals (MPa)
                            fc_prime_mpa = UnitUtils.ConvertFromInternalUnits(fc_prime_internal, mpa_unit_type)

                            # Round the MPa value to the nearest integer
                            fc_prime_mpa_rounded = int(round(fc_prime_mpa))

                            # Format the strength suffix (e.g., " C30")
                            # Note: This only adds the cylinder strength (Fc'). The '/Fck,cube' part (e.g., '/37')
                            # is not directly available from a single property and is omitted here.
                            strength_suffix = " C{}".format(fc_prime_mpa_rounded)

                            # Check if the current name already contains the exact strength suffix
                            if strength_suffix not in current_name:
                                # Construct the new name
                                new_name = current_name + strength_suffix
                                try:
                                    # Rename the material
                                    material.Name = new_name
                                    renamed_count += 1
                                    # print("# Renamed '{}' to '{}'".format(current_name, new_name)) # Debug
                                except Exception as rename_ex:
                                    error_count += 1
                                    # print("# ERROR renaming '{}' (ID: {}): {}".format(current_name, material.Id, rename_ex)) # Debug
                            else:
                                # Name already contains the calculated strength suffix
                                skipped_already_named += 1
                                # print("# Skipped '{}' (ID: {}): Already contains '{}'".format(current_name, material.Id, strength_suffix)) # Debug

                        except Exception as strength_ex:
                            # Error getting or converting strength
                            skipped_no_strength += 1
                            # print("# Skipped '{}' (ID: {}): Could not get/convert concrete strength. Error: {}".format(current_name, material.Id, strength_ex)) # Debug
                    else:
                        # Asset found, but it's not a concrete asset
                        skipped_not_concrete_asset += 1
                        # print("# Skipped '{}' (ID: {}): Structural asset is not Concrete type.".format(current_name, material.Id)) # Debug
                else:
                    # No valid structural asset found for this material
                    skipped_no_asset += 1
                    # print("# Skipped '{}' (ID: {}): No valid structural asset found.".format(current_name, material.Id)) # Debug
            else:
                # Name does not contain 'Concrete'
                skipped_no_concrete += 1

        except Exception as loop_ex:
            # Catch-all for errors processing a specific material
            error_count += 1
            try:
                name_for_error = Element.Name.GetValue(material)
            except:
                name_for_error = "ID: {}".format(material.Id)
            # print("# ERROR processing Material '{}': {}".format(name_for_error, loop_ex)) # Debug

# Optional: Print a summary (commented out by default)
# print("--- Material Renaming Summary ---")
# print("Total Materials Checked: {}".format(total_materials))
# print("Successfully Renamed: {}".format(renamed_count))
# print("Skipped (Name doesn't contain '{}'): {}".format(target_keyword, skipped_no_concrete))
# print("Skipped (No valid structural asset): {}".format(skipped_no_asset))
# print("Skipped (Asset not Concrete type): {}".format(skipped_not_concrete_asset))
# print("Skipped (Could not get/convert strength): {}".format(skipped_no_strength))
# print("Skipped (Name already includes calculated strength): {}".format(skipped_already_named))
# print("Errors Encountered: {}".format(error_count))