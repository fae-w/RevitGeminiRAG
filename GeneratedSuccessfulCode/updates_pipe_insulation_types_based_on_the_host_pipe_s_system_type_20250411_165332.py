# Purpose: This script updates pipe insulation types based on the host pipe's system type.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    Parameter,
    BuiltInParameter,
    Element,
    ElementType # Added for broader type check
)
# Import Plumbing specific classes
from Autodesk.Revit.DB.Plumbing import (
    PipeInsulation,
    Pipe,
    PipeInsulationType,
    PipingSystemType
)

# --- Configuration ---
# Built-in parameter for the Pipe's System Type
PIPE_SYSTEM_TYPE_BIP = BuiltInParameter.RBS_PIPING_SYSTEM_TYPE_PARAM
# Built-in parameter for the instance's Type (which controls Pipe Insulation Type for a PipeInsulation instance)
INSULATION_TYPE_BIP = BuiltInParameter.ELEM_FAMILY_AND_TYPE_PARAM # Corrected BuiltInParameter

# --- Pre-processing: Collect Pipe Insulation Types ---
insulation_type_collector = FilteredElementCollector(doc).OfClass(PipeInsulationType)
insulation_types_map = {}
for ins_type in insulation_type_collector:
    if ins_type and isinstance(ins_type, PipeInsulationType) and ins_type.IsValidObject:
        # Store mapping: Insulation Type Name -> ElementId
        # Assuming the PipeInsulationType name should match the PipingSystemType name
        try:
            type_name = Element.Name.__get__(ins_type) # Use Element.Name for robustness
            if type_name:
                insulation_types_map[type_name] = ins_type.Id
        except Exception as e:
            print("# Warning: Could not get name for PipeInsulationType ID {}: {}".format(ins_type.Id, e))


if not insulation_types_map:
    print("# Error: No Pipe Insulation Types found in the document. Cannot proceed.")
else:
    # --- Main Logic: Process Pipe Insulation ---
    pipe_insulation_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PipeInsulation).WhereElementIsNotElementType()

    updated_count = 0
    skipped_no_host = 0
    skipped_host_not_pipe = 0
    skipped_no_system_type_param = 0
    skipped_no_system_type_element = 0
    skipped_no_matching_insulation_type = 0
    skipped_already_correct = 0
    skipped_param_readonly = 0
    error_count = 0
    processed_count = 0

    insulation_list = list(pipe_insulation_collector) # Convert to list for potentially safer iteration if modifying elements indirectly affects collector
    total_to_check = len(insulation_list)

    for insulation in insulation_list:
        processed_count += 1
        if not isinstance(insulation, PipeInsulation):
            # Should not happen with the filter, but good practice
            continue

        try:
            # 1. Get the host pipe element
            host_id = insulation.HostElementId
            if host_id == ElementId.InvalidElementId:
                skipped_no_host += 1
                continue

            host_element = doc.GetElement(host_id)
            if not host_element or not isinstance(host_element, Pipe):
                skipped_host_not_pipe += 1
                continue

            pipe = host_element

            # 2. Get the 'System Type' of the host pipe
            system_type_param = pipe.get_Parameter(PIPE_SYSTEM_TYPE_BIP)
            if not system_type_param or not system_type_param.HasValue:
                # Try lookup by name as a fallback (less reliable)
                system_type_param = pipe.LookupParameter("System Type")
                if not system_type_param or not system_type_param.HasValue:
                    skipped_no_system_type_param += 1
                    continue

            system_type_id = system_type_param.AsElementId()
            if system_type_id == ElementId.InvalidElementId:
                skipped_no_system_type_param += 1 # Treat invalid ID as missing param value
                continue

            system_type_element = doc.GetElement(system_type_id)
            # Check if the element is valid and is a PipingSystemType or at least an ElementType
            if not system_type_element or not system_type_element.IsValidObject:
                 skipped_no_system_type_element += 1
                 continue
            # Ensure it's a type we can get a name from
            if not isinstance(system_type_element, ElementType):
                 skipped_no_system_type_element += 1
                 continue

            try:
                 # Use the robust Element.Name getter
                 system_type_name = Element.Name.__get__(system_type_element)
            except Exception:
                 print("# Warning: Could not get name for System Type ID {} on Pipe {}".format(system_type_id, pipe.Id))
                 skipped_no_system_type_element += 1
                 continue

            if not system_type_name:
                skipped_no_system_type_element += 1
                continue

            # 3. Find a matching PipeInsulationType
            target_insulation_type_id = insulation_types_map.get(system_type_name)

            if not target_insulation_type_id or target_insulation_type_id == ElementId.InvalidElementId:
                skipped_no_matching_insulation_type += 1
                # print("# Info: No matching PipeInsulationType found for system type '{}' from Pipe ID {}".format(system_type_name, pipe.Id)) # Optional Debug
                continue

            # 4. Update the 'Insulation Type' parameter of the PipeInsulation
            # The parameter that controls the Type is ELEM_FAMILY_AND_TYPE_PARAM
            insulation_type_param = insulation.get_Parameter(INSULATION_TYPE_BIP)
            if not insulation_type_param:
                # Fallback to LookupParameter("Type") if BuiltInParameter fails
                insulation_type_param = insulation.LookupParameter("Type")
                if not insulation_type_param:
                     error_count += 1
                     print("# Error: Could not find Type parameter on insulation element ID {}".format(insulation.Id))
                     continue

            if insulation_type_param.IsReadOnly:
                skipped_param_readonly += 1
                continue

            current_insulation_type_id = insulation_type_param.AsElementId()

            if current_insulation_type_id == target_insulation_type_id:
                skipped_already_correct += 1
                continue

            # Set the parameter (Transaction handled externally)
            try:
                # Setting the ELEM_FAMILY_AND_TYPE_PARAM is equivalent to changing the type in the UI
                success = insulation_type_param.Set(target_insulation_type_id)
                if success:
                    updated_count += 1
                else:
                    # Set returned false, indicating potential issue (e.g., type incompatible?)
                    error_count += 1
                    print("# Warning: Setting Insulation Type parameter for insulation ID {} returned false.".format(insulation.Id))
            except Exception as e_set:
                error_count += 1
                print("# Error setting Insulation Type for insulation ID {}: {}".format(insulation.Id, e_set))

        except Exception as e:
            error_count += 1
            try:
                ins_id_str = str(insulation.Id)
            except:
                ins_id_str = "UNKNOWN"
            print("# Error processing Pipe Insulation element ID {}: {}".format(ins_id_str, e))

    # --- Summary ---
    print("--- Pipe Insulation Type Update Summary ---")
    print("Total Pipe Insulation elements checked: {}".format(processed_count)) # Use processed count
    print("Successfully updated: {}".format(updated_count))
    print("Skipped (Already correct type): {}".format(skipped_already_correct))
    print("Skipped (No host element found): {}".format(skipped_no_host))
    print("Skipped (Host element not a Pipe): {}".format(skipped_host_not_pipe))
    print("Skipped (Host Pipe missing System Type parameter/value): {}".format(skipped_no_system_type_param))
    print("Skipped (Could not find/resolve Host Pipe's System Type element/name): {}".format(skipped_no_system_type_element))
    print("Skipped (No matching Pipe Insulation Type found for host's System Type name): {}".format(skipped_no_matching_insulation_type))
    print("Skipped (Insulation Type parameter is read-only): {}".format(skipped_param_readonly))
    print("Errors during processing: {}".format(error_count))
    print("Total Pipe Insulation Types available for matching: {}".format(len(insulation_types_map)))