# Purpose: This script assigns electrical load classifications to electrical equipment based on type names.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    ElementType
)
# Import ElectricalLoadClassification if needed (might require specific assembly reference)
try:
    from Autodesk.Revit.DB.Electrical import ElectricalLoadClassification
except ImportError:
    # Attempt to load the assembly if the class isn't found
    try:
        clr.AddReference("RevitAPI") # Typically already loaded, but try again
        clr.AddReference("RevitAPIElectrical") # Might be needed for Electrical namespace
        from Autodesk.Revit.DB.Electrical import ElectricalLoadClassification
    except Exception as e:
        print("# Error: Could not load ElectricalLoadClassification. Ensure RevitAPIElectrical assembly is available.")
        print("# Details: {}".format(e)) # Escaped format
        # Stop script if essential class is missing
        raise ImportError("Failed to import ElectricalLoadClassification")

# --- Configuration: Map Type Names to Load Classification Names ---
# IMPORTANT: Modify this dictionary to match your project's Type Names
#            and the desired Load Classification names.
#            Keys: Exact 'Type Name' of the Electrical Equipment Type.
#            Values: Exact 'Name' of the ElectricalLoadClassification element.
#            Case-sensitive.
type_name_to_load_class_map = {
    # --- Example Mappings - Replace with your actual data ---
    "Panelboard - 208V MLO": "Lighting",
    "Panelboard - 480V MLO": "Lighting",
    "Switchboard - 480V": "Power",
    "Transformer - Dry Type 480-208Y/120": "Power",
    "Motor - Generic 5HP": "Motor",
    "VAV Box Controller": "HVAC",
    "Disconnect Switch - Fused": "Power",
    "Receptacle - Duplex": "Receptacle",
    "Lighting Fixture Power Feed": "Lighting"
    # --- Add all necessary mappings for your project ---
}

# --- Main Script ---

# 1. Get all available Load Classification elements in the project
load_class_collector = FilteredElementCollector(doc).OfClass(ElectricalLoadClassification)
load_class_dict = {}
for lc in load_class_collector:
    if isinstance(lc, ElectricalLoadClassification):
        load_class_dict[lc.Name] = lc.Id
    # else: # Could be other element types if collector isn't perfect, ignore them
    #     pass

if not load_class_dict:
    print("# Error: No ElectricalLoadClassification elements found in the project. Cannot proceed.")
    # Exit gracefully if no load classifications exist
    # (Alternatively, raise an exception if preferred)
    # raise ValueError("No Load Classifications found.")


# 2. Get all Electrical Equipment instances
equipment_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ElectricalEquipment).WhereElementIsNotElementType()

# Counters for summary
updated_count = 0
skipped_no_type = 0
skipped_type_not_mapped = 0
skipped_load_class_not_found = 0
skipped_param_not_found = 0
skipped_param_read_only = 0
error_count = 0

# 3. Iterate and update
for equipment in equipment_collector:
    try:
        # Get the ElementType (FamilySymbol) of the instance
        type_id = equipment.GetTypeId()
        if type_id == ElementId.InvalidElementId:
            skipped_no_type += 1
            continue

        elementType = doc.GetElement(type_id)
        if not elementType or not isinstance(elementType, ElementType):
            # This case should be rare if GetTypeId returned valid ID
            skipped_no_type += 1
            continue

        type_name = elementType.Name

        # Check if the type name is in our mapping
        if type_name in type_name_to_load_class_map:
            target_load_class_name = type_name_to_load_class_map[type_name]

            # Check if the target Load Classification name exists in the project
            if target_load_class_name in load_class_dict:
                target_load_class_id = load_class_dict[target_load_class_name]

                # Get the 'Load Classification' parameter on the instance
                # BuiltInParameter.CIRCUIT_LOAD_CLASSIFICATION_PARAM is common for elements on circuits
                load_class_param = equipment.get_Parameter(BuiltInParameter.CIRCUIT_LOAD_CLASSIFICATION_PARAM)

                if load_class_param:
                    if not load_class_param.IsReadOnly:
                        # Check if update is needed
                        current_load_class_id = load_class_param.AsElementId()
                        if current_load_class_id != target_load_class_id:
                            load_class_param.Set(target_load_class_id)
                            updated_count += 1
                        # else: # Already has the correct value, no action needed
                            # pass
                    else:
                        skipped_param_read_only += 1
                        # print(f"# INFO: Equipment ID {equipment.Id} skipped - 'Load Classification' parameter is read-only.") # Escaped
                else:
                    skipped_param_not_found += 1
                    # print(f"# INFO: Equipment ID {equipment.Id} skipped - 'Load Classification' parameter (BIP) not found.") # Escaped
            else:
                skipped_load_class_not_found += 1
                # print(f"# INFO: Equipment Type '{type_name}' mapped to '{target_load_class_name}', but this Load Classification doesn't exist in the project.") # Escaped
        else:
            skipped_type_not_mapped += 1
            # print(f"# INFO: Equipment Type '{type_name}' (ID: {equipment.Id}) not found in the mapping dictionary.") # Escaped

    except Exception as e:
        error_count += 1
        # print(f"# ERROR processing Equipment ID {equipment.Id}: {e}") # Escaped

# Optional: Print summary report (commented out as per standard format)
# print("--- Load Classification Update Summary ---")
# print("Successfully updated: {}".format(updated_count)) # Escaped
# print("Skipped (Type Name not in map): {}".format(skipped_type_not_mapped)) # Escaped
# print("Skipped (Mapped Load Class not found): {}".format(skipped_load_class_not_found)) # Escaped
# print("Skipped (Load Class Param not found): {}".format(skipped_param_not_found)) # Escaped
# print("Skipped (Load Class Param read-only): {}".format(skipped_param_read_only)) # Escaped
# print("Skipped (No valid Type found): {}".format(skipped_no_type)) # Escaped
# print("Errors during processing: {}".format(error_count)) # Escaped
# print("Total Equipment Instances processed: {}".format(equipment_collector.GetElementCount())) # Escaped