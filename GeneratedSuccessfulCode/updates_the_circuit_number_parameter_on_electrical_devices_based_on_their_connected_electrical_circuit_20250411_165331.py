# Purpose: This script updates the 'Circuit Number' parameter on electrical devices based on their connected electrical circuit.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
# Add reference for Electrical classes
try:
    clr.AddReference("RevitAPIElectrical")
except:
    print("# Warning: Could not load RevitAPIElectrical assembly. ElectricalSystem access might fail.")

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementMulticategoryFilter,
    Element,
    MEPModel,
    ConnectorManager,
    Connector,
    ConnectorSet,
    Domain,
    Parameter,
    BuiltInParameter,
    StorageType
)
# Import ElectricalSystem explicitly
try:
    from Autodesk.Revit.DB.Electrical import ElectricalSystem, ElectricalSystemType
except ImportError:
    # Handle case where assembly didn't load or class isn't available
    print("# Error: Cannot import ElectricalSystem. Script cannot function.")
    # Set a flag or raise an error if critical
    ElectricalSystem = None # Ensure checks fail gracefully later

from System.Collections.Generic import List
import System # For exception handling

# --- Configuration ---
# Define the categories of elements to check
target_categories = List[BuiltInCategory]()
target_categories.Add(BuiltInCategory.OST_LightingFixtures)
target_categories.Add(BuiltInCategory.OST_ElectricalFixtures)
target_categories.Add(BuiltInCategory.OST_ElectricalEquipment)
# Add other categories if needed, e.g., OST_MechanicalEquipment, OST_DataDevices etc.
# target_categories.Add(BuiltInCategory.OST_MechanicalEquipment)

# The parameter on the device to update
circuit_number_param_bip = BuiltInParameter.RBS_ELEC_CIRCUIT_NUMBER

# --- Helper Function (Optional, can be integrated) ---
def get_device_circuit_info(element):
    """
    Attempts to find the connected electrical circuit for a given element.
    Returns the ElectricalSystem object if found, otherwise None.
    """
    if not ElectricalSystem: # Check if import failed
        return None

    system = None
    try:
        # Check if the element itself is an ElectricalSystem (e.g., Wire) - skip
        if isinstance(element, ElectricalSystem):
             return None

        # Try accessing MEPModel directly first
        mep_model = None
        if hasattr(element, "MEPModel") and element.MEPModel:
             mep_model = element.MEPModel

        # Fallback for elements like Lighting Fixtures that might not expose MEPModel directly
        # but have connectors accessible via FamilyInstance properties
        if not mep_model and hasattr(element, "GetMEPModel"):
             mep_model = element.GetMEPModel()

        if mep_model and mep_model.ConnectorManager:
            connector_manager = mep_model.ConnectorManager
            if connector_manager.Connectors:
                for connector in connector_manager.Connectors:
                    # Check if it's an electrical connector and connected
                    if connector.Domain == Domain.DomainElectrical and connector.IsConnected:
                        # Get the system the connector belongs to
                        # MEPSystem property directly refers to the system (circuit)
                        system_candidate = connector.MEPSystem
                        if system_candidate and isinstance(system_candidate, ElectricalSystem):
                            # Older API versions might need ElectricalSystemType check
                            # if hasattr(system_candidate, 'SystemType') and system_candidate.SystemType == ElectricalSystemType.Circuit:
                            # For modern API, just checking if it's an ElectricalSystem is usually enough for circuits
                            system = system_candidate
                            break # Found the circuit, stop checking connectors for this device
                        # else: # Check refs if MEPSystem is not direct
                        #    for ref_conn in connector.AllRefs:
                        #        # Check if the referenced connector belongs to an Electrical System
                        #        owner = ref_conn.Owner
                        #        if hasattr(owner, 'MEPSystem') and owner.MEPSystem and isinstance(owner.MEPSystem, ElectricalSystem):
                        #             system = owner.MEPSystem
                        #             break
                        #    if system: break

    except Exception as e:
        # print("Error checking connectors for element {}: {}".format(element.Id, e)) # Debugging
        pass # Ignore elements that cause errors during connector check
    return system

# --- Main Script ---
updated_count = 0
skipped_not_circuited = 0
skipped_param_not_found = 0
skipped_param_read_only = 0
skipped_already_correct = 0
skipped_no_mep_model = 0
error_count = 0
processed_count = 0

# Check if ElectricalSystem is available before starting
if not ElectricalSystem:
    print("# Error: ElectricalSystem class not loaded. Aborting script.")
else:
    try:
        # Create filter for the specified categories
        multi_cat_filter = ElementMulticategoryFilter(target_categories)

        # Collect element instances in the document for the specified categories
        collector = FilteredElementCollector(doc).WherePasses(multi_cat_filter).WhereElementIsNotElementType()

        for element in collector:
            processed_count += 1
            circuit_system = None
            target_circuit_number = None

            try:
                # Find the electrical system (circuit) this element is connected to
                circuit_system = get_device_circuit_info(element)

                if circuit_system:
                    # Get the circuit number string from the system
                    target_circuit_number = circuit_system.CircuitNumber
                    if target_circuit_number is None or target_circuit_number == "":
                        # Circuit exists but has no number assigned yet, skip update
                         skipped_not_circuited += 1 # Count as 'not circuited' for simplicity
                         continue

                    # Get the 'Circuit Number' parameter on the device itself
                    param = element.get_Parameter(circuit_number_param_bip)

                    if param:
                        if not param.IsReadOnly:
                            # Ensure parameter stores a string
                            if param.StorageType == StorageType.String:
                                current_value = param.AsString()
                                if current_value != target_circuit_number:
                                    param.Set(target_circuit_number)
                                    updated_count += 1
                                else:
                                    skipped_already_correct += 1
                            else:
                                # Handle cases where the parameter is unexpectedly not a string
                                # print("# Warning: Parameter 'Circuit Number' on Element {} is not StorageType.String.".format(element.Id))
                                skipped_param_read_only += 1 # Reuse counter for simplicity or add new one
                        else:
                            skipped_param_read_only += 1
                    else:
                        skipped_param_not_found += 1
                else:
                    # Element does not have MEPModel or is not connected to a circuit
                    # Check if MEPModel exists at all to differentiate reasons for skipping
                     has_mep = False
                     if hasattr(element, "MEPModel") and element.MEPModel: has_mep = True
                     if not has_mep and hasattr(element, "GetMEPModel"):
                         try:
                             if element.GetMEPModel(): has_mep = True
                         except: pass # Ignore errors getting MEP Model

                     if not has_mep:
                          skipped_no_mep_model += 1
                     else:
                          skipped_not_circuited += 1


            except System.Exception as e:
                error_count += 1
                try:
                    element_info = element.Id.ToString()
                    if hasattr(element, "Name"):
                        element_info = "'{}' (ID: {})".format(element.Name, element.Id)
                except:
                    pass # Keep simple ID if name access fails
                print("# Error processing element {}: {}".format(element_info, e))

    except System.Exception as ex:
        print("# Error during element collection or main loop: {}".format(ex))
        error_count += 1

# --- Summary ---
print("--- Circuit Number Update Summary ---")
print("Total Elements Processed (Matching Categories): {}".format(processed_count))
print("Successfully Updated 'Circuit Number': {}".format(updated_count))
print("Skipped (Already Correct): {}".format(skipped_already_correct))
print("Skipped (Not Connected to a Numbered Circuit): {}".format(skipped_not_circuited))
print("Skipped (Parameter '{}' Not Found): {}".format(circuit_number_param_bip.ToString(), skipped_param_not_found))
print("Skipped (Parameter Read-Only or Wrong Type): {}".format(skipped_param_read_only))
print("Skipped (No MEP Model / Connectors): {}".format(skipped_no_mep_model))
print("Errors Encountered: {}".format(error_count))
print("--- Script Finished ---")