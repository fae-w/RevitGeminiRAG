# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    OverrideGraphicSettings,
    View,
    ElementId,
    Material,
    FamilyInstance,
    Element
)
# Removed Structure namespace imports as StructuralMaterialId is on FamilyInstance directly

# --- Configuration ---
target_material_name = "Steel" # Case-insensitive comparison will be used

# --- Get Active View ---
active_view = doc.ActiveView

if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or the active view is a template.")
else:
    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()
    try:
        # Turn off visibility for both foreground and background cut patterns
        override_settings.SetCutForegroundPatternVisible(False)
        override_settings.SetCutBackgroundPatternVisible(False)
        # Optionally, ensure the patterns themselves are unset if desired
        # override_settings.SetCutForegroundPatternId(ElementId.InvalidElementId)
        # override_settings.SetCutBackgroundPatternId(ElementId.InvalidElementId)
        settings_valid = True
    except Exception as e:
        print("# Error creating OverrideGraphicSettings: {}".format(e))
        settings_valid = False

    if settings_valid:
        # --- Collect Structural Columns in Active View ---
        collector = FilteredElementCollector(doc, active_view.Id)
        column_collector = collector.OfCategory(BuiltInCategory.OST_StructuralColumns)\
                                   .WhereElementIsNotElementType()\
                                   .ToElements() # Get elements for easier type checking

        elements_overridden_count = 0
        elements_checked_count = 0
        elements_skipped_no_material_id = 0
        elements_skipped_material_not_found = 0
        elements_skipped_material_mismatch = 0
        elements_error_processing = 0
        elements_error_override = 0

        # --- Apply Overrides ---
        # Assumes transaction is handled externally by the C# wrapper.
        for column in column_collector:
            elements_checked_count += 1
            try:
                # Structural Columns are typically FamilyInstances
                if isinstance(column, FamilyInstance):
                    material_id = column.StructuralMaterialId
                    if material_id != ElementId.InvalidElementId:
                        material_element = doc.GetElement(material_id)
                        if isinstance(material_element, Material):
                            # Case-insensitive check for material name
                            if material_element.Name.lower() == target_material_name.lower():
                                try:
                                    active_view.SetElementOverrides(column.Id, override_settings)
                                    elements_overridden_count += 1
                                except Exception as override_err:
                                    # print("# Debug: Failed override for {}: {}".format(column.Id, override_err))
                                    elements_error_override += 1
                            else:
                                # Material name does not match
                                elements_skipped_material_mismatch += 1
                        else:
                            # Material ID found, but GetElement didn't return a Material
                            elements_skipped_material_not_found += 1
                            # print("# Debug: Material element not found or not a Material for ID {}".format(material_id))
                    else:
                        # Column does not have a StructuralMaterialId assigned
                        elements_skipped_no_material_id += 1
                        # print("# Debug: Column {} has no StructuralMaterialId".format(column.Id))
                #else:
                    # print("# Debug: Element {} is not a FamilyInstance".format(column.Id)) # Should not happen with OST_StructuralColumns filter
                    # elements_error_processing += 1 # Or count differently if needed
            except Exception as e:
                # print("# Debug: Error processing column {}: {}".format(column.Id, e))
                elements_error_processing += 1

        # --- Feedback ---
        if elements_overridden_count > 0:
            print("# Turned off cut pattern visibility for {} Structural Column(s) with '{}' material in view '{}'.".format(elements_overridden_count, target_material_name, active_view.Name))
        elif elements_checked_count > 0:
            print("# No Structural Columns found with '{}' material to override in view '{}'.".format(target_material_name, active_view.Name))
        else:
             print("# No Structural Column elements found in view '{}'.".format(active_view.Name))

        # Optional detailed summary (uncomment if needed)
        # print("# Summary: Checked: {}, Overridden: {}, Skipped (No Mat ID): {}, Skipped (Mat Not Found): {}, Skipped (Mat Mismatch): {}, Errors (Processing): {}, Errors (Override): {}".format(
        #     elements_checked_count, elements_overridden_count, elements_skipped_no_material_id,
        #     elements_skipped_material_not_found, elements_skipped_material_mismatch,
        #     elements_error_processing, elements_error_override))

    else:
        print("# Script did not run because OverrideGraphicSettings could not be configured.")