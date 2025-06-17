# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException

# Import DB classes and the DB namespace itself
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Parameter,
    UnitUtils,
    ForgeTypeId, # For modern unit handling (Revit 2021+)
    BuiltInParameter,
    ElementId,
    StorageType
)
# Import Structure specific classes
from Autodesk.Revit.DB.Structure import (
    RebarBarType
)

# Attempt to import unit types - handle potential errors gracefully
UnitTypeId = None
DisplayUnitType = None
try:
    # Revit 2021+ preferred method
    from Autodesk.Revit.DB import UnitTypeId
except ImportError:
    pass # UnitTypeId will remain None

try:
    # Pre-Revit 2021 method
    from Autodesk.Revit.DB import DisplayUnitType
except ImportError:
    pass # DisplayUnitType will remain None

# --- Configuration ---
target_value_mm = 12000.0
# The user specified 'Maximum Length'. This typically corresponds to the built-in parameter REBAR_MAX_LENGTH on RebarBarType.
parameter_bip = BuiltInParameter.REBAR_MAX_LENGTH
parameter_name_fallback = "Maximum Bar Length" # Fallback if BIP lookup fails

# --- Initialization ---
target_value_internal = None
updated_count = 0
skipped_no_change = 0
skipped_not_found = 0
skipped_read_only = 0
error_count = 0
processed_count = 0
output_messages = [] # Use a list to collect messages

# --- Step 1: Convert Target Value to Internal Units (Feet) ---
conversion_success = False
try:
    # Try Revit 2021+ ForgeTypeId/UnitTypeId method first
    if UnitTypeId and hasattr(UnitTypeId, "Millimeters"):
        target_value_internal = UnitUtils.ConvertToInternalUnits(target_value_mm, UnitTypeId.Millimeters)
        conversion_success = True
        # output_messages.append("# Debug: Using UnitTypeId for conversion.") # Optional Debug
    # Fallback for older API versions (pre-2021) using DisplayUnitType accessed via DB namespace
    elif DisplayUnitType and hasattr(DB, 'DisplayUnitType') and hasattr(DB.DisplayUnitType, 'DUT_MILLIMETERS') and DB.DisplayUnitType.DUT_MILLIMETERS is not None:
        # Access DisplayUnitType via the imported DB namespace
        target_value_internal = UnitUtils.ConvertToInternalUnits(target_value_mm, DB.DisplayUnitType.DUT_MILLIMETERS)
        conversion_success = True
        # output_messages.append("# Debug: Using DisplayUnitType for conversion.") # Optional Debug
    else:
         # This case handles scenarios where neither modern nor legacy unit types are found/usable
         output_messages.append("# Error: Could not find necessary unit types (UnitTypeId.Millimeters or DB.DisplayUnitType.DUT_MILLIMETERS).")

except SystemException as conv_e:
    output_messages.append("# Error converting target value {}mm to internal units: {}".format(target_value_mm, conv_e))
except AttributeError as attr_e:
     # This might happen if UnitTypeId or DisplayUnitType classes/members don't exist as expected
     output_messages.append("# Error accessing unit types: {}. Check API version compatibility.".format(attr_e))

if not conversion_success or target_value_internal is None:
    output_messages.append("# Error: Unit conversion failed. Cannot proceed.")
    # Print collected messages if conversion failed early
    for msg in output_messages:
        print(msg)
else:
    # --- Step 2: Collect RebarBarType Elements ---
    collector = FilteredElementCollector(doc).OfClass(RebarBarType)
    rebar_types = list(collector) # Convert iterator to list

    if not rebar_types:
        output_messages.append("# No Rebar Bar Types found in the document.")
    else:
        # --- Step 3: Iterate and Update Parameter ---
        for rebar_type in rebar_types:
            processed_count += 1
            type_name = "Unknown Type Name"
            param_to_set = None
            param_found = False

            try:
                # Element.Name can fail for some obscure types, handle it
                type_name = Element.Name.__get__(rebar_type)
            except Exception as name_ex:
                type_name = "Type ID: {}".format(rebar_type.Id)
                # output_messages.append("# Debug: Could not get name for element ID {}: {}".format(rebar_type.Id, name_ex))

            try:
                # 1. Try getting the BuiltInParameter first
                param_to_set = rebar_type.get_Parameter(parameter_bip)

                # 2. If BIP not found, try looking up by name (fallback)
                if not param_to_set:
                    param_to_set = rebar_type.LookupParameter(parameter_name_fallback)

                # Check if parameter was found by either method
                if param_to_set:
                    param_found = True
                    # Check if parameter is read-only
                    if param_to_set.IsReadOnly:
                        # output_messages.append("# Info: Parameter '{}' is read-only for type '{}' (ID: {}). Skipping.".format(param_to_set.Definition.Name, type_name, rebar_type.Id)) # Optional Info
                        skipped_read_only += 1
                        continue # Skip to the next rebar type

                    # Check if parameter storage type is suitable (Double for length)
                    if param_to_set.StorageType != StorageType.Double:
                        output_messages.append("# Warning: Parameter '{}' on type '{}' (ID: {}) has unexpected storage type '{}'. Skipping.".format(param_to_set.Definition.Name, type_name, rebar_type.Id, param_to_set.StorageType))
                        error_count += 1
                        continue

                    # Check if the current value is already the target value
                    current_value = param_to_set.AsDouble()
                    tolerance = 0.0001 # Tolerance for floating point comparison in feet
                    if abs(current_value - target_value_internal) < tolerance:
                        # output_messages.append("# Info: Parameter '{}' already set for type '{}' (ID: {}). Skipping.".format(param_to_set.Definition.Name, type_name, rebar_type.Id)) # Optional Info
                        skipped_no_change += 1
                        continue

                    # Set the value
                    set_result = param_to_set.Set(target_value_internal)
                    if set_result:
                        updated_count += 1
                        # output_messages.append("# Debug: Updated parameter '{}' for type '{}' (ID: {})".format(param_to_set.Definition.Name, type_name, rebar_type.Id)) # Optional Debug
                    else:
                         # This might happen due to constraints not checked (e.g., value out of bounds)
                         output_messages.append("# Warning: Failed to set parameter '{}' for type '{}' (ID: {}). Set() returned false.".format(param_to_set.Definition.Name, type_name, rebar_type.Id))
                         error_count += 1

                else:
                    # Parameter not found by BIP or name
                    output_messages.append("# Warning: Parameter '{}' (BIP: {}) not found on RebarBarType '{}' (ID: {}). Skipping.".format(parameter_name_fallback, parameter_bip, type_name, rebar_type.Id))
                    skipped_not_found += 1

            except SystemException as set_ex:
                 param_name_for_error = parameter_name_fallback
                 if param_to_set and hasattr(param_to_set, 'Definition'):
                      param_name_for_error = param_to_set.Definition.Name
                 output_messages.append("# Error updating parameter '{}' for Rebar Bar Type '{}' (ID: {}): {}".format(param_name_for_error, type_name, rebar_type.Id, set_ex.Message))
                 error_count += 1

        # --- Final Summary ---
        output_messages.append("# --- Rebar Bar Type Maximum Length Update Summary ---")
        output_messages.append("# Target Value: {}mm (Internal: {:.4f} ft)".format(target_value_mm, target_value_internal))
        output_messages.append("# Total Rebar Bar Types Found/Processed: {}".format(processed_count))
        output_messages.append("# Successfully Updated: {}".format(updated_count))
        output_messages.append("# Skipped (No Change Needed): {}".format(skipped_no_change))
        output_messages.append("# Skipped (Parameter Not Found): {}".format(skipped_not_found))
        output_messages.append("# Skipped (Read-Only): {}".format(skipped_read_only))
        output_messages.append("# Errors Encountered (Incl. Type/Set Issues): {}".format(error_count))
        if error_count > 0 or skipped_not_found > 0 or skipped_read_only > 0:
            output_messages.append("# Review warnings/errors printed above for details.")

    # Print all collected messages at the end
    for msg in output_messages:
        print(msg)