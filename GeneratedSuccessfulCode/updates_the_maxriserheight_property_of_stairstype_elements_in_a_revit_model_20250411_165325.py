# Purpose: This script updates the MaxRiserHeight property of StairsType elements in a Revit model.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Although not used directly, good practice
clr.AddReference('System') # Required for Exception handling
from System import Exception as SystemException

# Import DB classes and the DB namespace itself
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementType, # StairsType inherits from ElementType
    Parameter,
    UnitUtils,
    ForgeTypeId, # For modern unit handling (Revit 2021+)
    UnitTypeId, # For modern unit handling (Revit 2021+)
    # DisplayUnitType removed from here to avoid import error
)
# Import Architecture specific classes
from Autodesk.Revit.DB.Architecture import (
    StairsType
)

# --- Configuration ---
target_value_mm = 180.0
# The user specified 'Max Rise'. Based on API documentation and common usage,
# this corresponds to the MaxRiserHeight property on StairsType.
parameter_property_name = "MaxRiserHeight" # Direct property name

# --- Initialization ---
target_value_internal = None
updated_count = 0
skipped_no_change = 0
skipped_not_found = 0
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
    elif hasattr(DB, 'DisplayUnitType') and hasattr(DB.DisplayUnitType, 'DUT_MILLIMETERS') and DB.DisplayUnitType.DUT_MILLIMETERS is not None:
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
    # --- Step 2: Collect StairsType Elements ---
    collector = FilteredElementCollector(doc).OfClass(StairsType)
    stair_types = list(collector) # Convert iterator to list

    if not stair_types:
        output_messages.append("# No Stairs Types found in the document.")
    else:
        # --- Step 3: Iterate and Update Parameter ---
        for stair_type in stair_types:
            processed_count += 1
            type_name = "Unknown Type Name"
            try:
                type_name = stair_type.Name # Get name early for error messages
            except:
                pass # Keep default name if access fails

            try:
                # Access the MaxRiserHeight property directly
                if hasattr(stair_type, parameter_property_name):
                    # Check bounds (MaxRiserHeight must be positive)
                    if target_value_internal <= 0:
                         output_messages.append("# Warning: Target value {:.4f} ft ({}mm) is not positive. Skipping type '{}'.".format(target_value_internal, target_value_mm, type_name))
                         error_count += 1
                         continue

                    # Check if the current value is already the target value
                    current_value = stair_type.MaxRiserHeight
                    tolerance = 0.0001 # Tolerance for floating point comparison
                    if abs(current_value - target_value_internal) < tolerance:
                        # output_messages.append("# Info: MaxRiserHeight already set for type '{}' (ID: {}). Skipping.".format(type_name, stair_type.Id)) # Optional Info
                        skipped_no_change += 1
                        continue

                    # Set the value using the property setter
                    stair_type.MaxRiserHeight = target_value_internal
                    updated_count += 1
                    # output_messages.append("# Debug: Updated MaxRiserHeight for type '{}' (ID: {})".format(type_name, stair_type.Id)) # Optional Debug
                else:
                    output_messages.append("# Warning: Property '{}' not found on StairsType '{}' (ID: {}). Skipping.".format(parameter_property_name, type_name, stair_type.Id))
                    skipped_not_found += 1

            except SystemException as set_ex:
                 output_messages.append("# Error updating MaxRiserHeight for Stairs Type '{}' (ID: {}): {}".format(type_name, stair_type.Id, set_ex.Message))
                 error_count += 1

        # --- Final Summary ---
        output_messages.append("# --- Stairs Type Max Riser Height Update Summary ---")
        output_messages.append("# Target Value: {}mm (Internal: {:.4f} ft)".format(target_value_mm, target_value_internal))
        output_messages.append("# Total Stairs Types Found/Processed: {}".format(processed_count))
        output_messages.append("# Successfully Updated: {}".format(updated_count))
        output_messages.append("# Skipped (No Change Needed): {}".format(skipped_no_change))
        output_messages.append("# Skipped (Property Not Found): {}".format(skipped_not_found))
        output_messages.append("# Errors Encountered: {}".format(error_count))
        if error_count > 0:
            output_messages.append("# Review errors printed above for details.")

    # Print all collected messages at the end
    for msg in output_messages:
        print(msg)