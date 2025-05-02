# Purpose: This script calculates and exports the total area of materials in selected Revit elements to a CSV file.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
# clr.AddReference('System.Collections') # Might not be strictly necessary but safe

from Autodesk.Revit.DB import Element, ElementId, Material, UnitUtils, SpecTypeId
# from System.Collections.Generic import List # List<> return type handled by IronPython usually
import System # For String.Format

# Dictionary to store aggregated material areas {material_name: total_area_sqft}
material_areas = {}

# Get selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids or len(selected_ids) == 0:
    print("# No elements selected.")
else:
    # Iterate through selected elements
    for element_id in selected_ids:
        element = doc.GetElement(element_id)
        if not element:
            continue

        try:
            # Get material IDs (non-paint and paint)
            non_paint_ids = element.GetMaterialIds(False)
            paint_ids = element.GetMaterialIds(True)
            processed_material_ids_for_element = set() # Track IDs processed for this element to avoid double counting

            # Process non-paint materials first
            if non_paint_ids:
                for mat_id in non_paint_ids:
                    # Check for invalid ID (sometimes returned)
                    if mat_id != ElementId.InvalidElementId:
                        material = doc.GetElement(mat_id)
                        # Ensure it's actually a Material object
                        if isinstance(material, Material):
                            mat_name = material.Name
                            try:
                                # Get area for this material on this element (non-paint)
                                area_sqft = element.GetMaterialArea(mat_id, False)
                                # Add to total if area is significant (use tolerance)
                                if area_sqft > 1e-6:
                                    material_areas[mat_name] = material_areas.get(mat_name, 0.0) + area_sqft
                                processed_material_ids_for_element.add(mat_id) # Mark as processed
                            except Exception as area_ex:
                                # Failed to get area for this material/element combination
                                # print("# Could not get non-paint area for material {0} on element {1}: {2}".format(mat_id, element_id, area_ex)) # Debugging
                                pass # Skip area calculation if it fails

            # Process paint materials, avoid double counting if ID was already processed as non-paint
            if paint_ids:
                for mat_id in paint_ids:
                    # Check for invalid ID and if it was already processed (e.g., as a non-paint material)
                    if mat_id != ElementId.InvalidElementId and mat_id not in processed_material_ids_for_element:
                        material = doc.GetElement(mat_id)
                        # Ensure it's a Material object
                        if isinstance(material, Material):
                            mat_name = material.Name
                            try:
                                # Get area for this material on this element (paint)
                                area_sqft_paint = element.GetMaterialArea(mat_id, True)
                                # Add to total if area is significant (use tolerance)
                                if area_sqft_paint > 1e-6:
                                    material_areas[mat_name] = material_areas.get(mat_name, 0.0) + area_sqft_paint
                                # No need to add to processed_material_ids_for_element again here
                            except Exception as area_ex_paint:
                                # Failed to get paint area
                                # print("# Could not get paint area for material {0} on element {1}: {2}".format(mat_id, element_id, area_ex_paint)) # Debugging
                                pass # Skip area calculation if it fails

        except Exception as e:
            # Error processing a specific element, e.g., getting material IDs failed
            # print("# Error processing element {0}: {1}".format(element_id.ToString(), e)) # Debugging
            pass # Continue with the next element

    # Prepare CSV output if any materials were found and processed
    if material_areas:
        csv_lines = []
        # Add header row, ensure quotes for safety
        csv_lines.append('"Material Name","Area (sq m)"')

        # Sort items by material name for consistent output
        sorted_materials = sorted(material_areas.items())

        for mat_name, total_area_sqft in sorted_materials:
            # Only include materials with a calculated area greater than tolerance
            if total_area_sqft > 1e-6:
                try:
                    # Convert total area from internal units (sq ft) to square meters
                    # Use SpecTypeId.Area for the conversion unit type
                    area_sq_m = UnitUtils.ConvertFromInternalUnits(total_area_sqft, SpecTypeId.Area)

                    # Format area string to "XXX.XX sq m"
                    # Using System.String.Format for reliable decimal formatting in IronPython
                    area_str = System.String.Format("{0:.2f} sq m", area_sq_m)

                    # Escape double quotes in material name for CSV compatibility
                    safe_mat_name = '"' + mat_name.replace('"', '""') + '"'

                    # Add the formatted row to the list
                    # Quote the area string as well just in case unit names ever contain commas (unlikely but safe)
                    csv_lines.append(safe_mat_name + ',"' + area_str + '"')

                except Exception as format_ex:
                    # Log error during conversion/formatting (optional)
                    # print("# Error formatting data for material '{0}': {1}".format(mat_name, format_ex)) # Debugging
                    pass # Skip materials that cause formatting errors

        # Check if any data rows were actually generated (more than just the header)
        if len(csv_lines) > 1:
            # Join lines into a single string for export
            file_content = "\n".join(csv_lines)
            # Print the export marker and data
            print("EXPORT::CSV::selected_material_areas_sqm.csv")
            print(file_content)
        else:
            # Message if processing happened but resulted in no valid output rows (e.g., all areas were too small)
            print("# No materials with area greater than tolerance found or processed successfully for export.")

    else:
        # Message if no materials were found at all across selected elements
        print("# No materials with calculable area found on the selected elements.")