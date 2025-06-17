# Purpose: This script updates the 'Manufacturer' parameter of door instances based on their 'Mark' value using a provided mapping.

﻿# Ensure necessary assemblies are referenced
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often needed, good practice to include
clr.AddReference('System')
clr.AddReference('System.Collections') # For List

# Import necessary namespaces and classes
# Assume 'doc' and other Revit objects are pre-defined in the execution scope
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Parameter,
    BuiltInParameter,
    StorageType,
    Element
)
# Removed 'Door' from direct import as it caused ImportError.
# We rely on the collector category filter.

from System.Collections.Generic import List
from System import String, Exception as SystemException

# --- Input Data ---
# Multi-line string containing the Mark/Manufacturer mapping
# Format: Mark,Mfr (header is ignored)
data_string = """Mark,Mfr
D-EXT-01,SecureDoors Inc.
D-INT-01,Standard Doors
D-INT-02,Standard Doors"""

# --- Parse Input Data ---
mark_to_mfr_map = {}
lines = data_string.strip().split('\n')
# Skip header line (index 0)
for line in lines[1:]:
    parts = line.strip().split(',', 1) # Split only on the first comma
    if len(parts) == 2:
        mark_value = parts[0].strip()
        mfr_value = parts[1].strip()
        if mark_value: # Ensure mark is not empty
            mark_to_mfr_map[mark_value] = mfr_value
        else:
            print("# Warning: Skipping line with empty Mark value: '{}'".format(line))
    else:
        print("# Warning: Skipping malformed line: '{}'".format(line))

if not mark_to_mfr_map:
    print("# Error: No valid Mark/Manufacturer pairs found in the input data.")
else:
    # --- Collect Door Instances ---
    # Assume 'doc' is pre-defined in the execution environment
    doors = [] # Initialize to empty list
    collection_failed = False
    try:
        door_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()
        # Using ToElements() is generally safer than direct iteration/casting
        doors = door_collector.ToElements()
    except SystemException as e:
        print("# Error collecting doors: {}".format(e.Message))
        collection_failed = True # Mark collection as failed

    # --- Counters for Summary ---
    processed_elements = 0 # Changed from processed_doors as we removed the explicit type check
    updated_doors = 0
    skipped_no_mark_param = 0
    skipped_mark_not_in_list = 0
    skipped_no_mfr_param = 0
    skipped_mfr_wrong_type = 0
    error_count = 0

    if doors:
        print("# Processing {} elements found in OST_Doors category.".format(len(doors)))
        print("# Looking for Marks: {}".format(", ".join(mark_to_mfr_map.keys())))

        # --- Iterate and Update ---
        # Transaction is handled externally by the C# wrapper
        for element in doors:
            # Removed 'isinstance(element, Door)' check to avoid the import issue.
            # We rely on the collector filtering by BuiltInCategory.OST_Doors.
            processed_elements += 1
            element_id = element.Id
            element_info = "ID: {}".format(element_id) # Basic info for logging

            try:
                # Get 'Mark' parameter
                mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)

                if not mark_param or not mark_param.HasValue:
                    skipped_no_mark_param += 1
                    # print("# Skipping Element {} - Mark parameter not found or has no value.".format(element_info)) # Verbose
                    continue

                mark_value = mark_param.AsString()
                if not mark_value: # Check if AsString returned None or empty string
                     skipped_no_mark_param += 1
                     # print("# Skipping Element {} - Mark parameter exists but value is empty.".format(element_info)) # Verbose
                     continue

                # Check if this element's mark is in our target list
                if mark_value in mark_to_mfr_map:
                    target_mfr = mark_to_mfr_map[mark_value]

                    # Get 'Manufacturer' parameter (Prioritize Instance parameter)
                    mfr_param = element.LookupParameter("Manufacturer")
                    if not mfr_param:
                         # Fallback to BuiltInParameter if LookupParameter failed
                         mfr_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MANUFACTURER)

                    # Verify if the found parameter is suitable for instance update
                    is_instance_param_suitable = False
                    if mfr_param and not mfr_param.IsReadOnly:
                         # Check if it's an instance parameter.
                         # If parameter definition is instance-binding or belongs directly to the element
                         # Using Element.Id check is a reasonable heuristic
                         if mfr_param.IsShared or mfr_param.Definition.Binding is None or not hasattr(mfr_param.Definition, 'Binding'): # Cannot easily check Binding type directly sometimes
                             # If shared or complex, assume instance if found via LookupParameter on element
                             # A safer check might involve Parameter.IsInstance but that doesn't exist.
                             # Checking Element.Id is often good enough.
                             if element.GetOrderedParameters(): # Check if the parameter is in the instance's list
                                 found_on_instance = False
                                 for p in element.GetOrderedParameters():
                                     if p.Id == mfr_param.Id:
                                         found_on_instance = True
                                         break
                                 if found_on_instance:
                                     is_instance_param_suitable = True
                                 else: # Parameter exists but maybe it's a Type parameter found via fallback?
                                      param_owner_id = -1
                                      try:
                                          # Parameter.Element is deprecated, try Definition source if available
                                          if hasattr(mfr_param, 'Element') and mfr_param.Element:
                                              param_owner_id = mfr_param.Element.Id
                                          # Add more robust check if needed, e.g., checking parameter definition binding
                                      except: pass # Ignore errors getting owner info

                                      if param_owner_id != element.Id:
                                           print("# Info: Element {} (Mark: '{}') Manufacturer parameter found, but might belong to the Type (OwnerID: {}). Skipping instance update.".format(element_info, mark_value, param_owner_id if param_owner_id != -1 else 'Unknown'))

                         elif mfr_param.Definition.Binding.GetType().Name == 'InstanceBinding': # More robust if accessible
                             is_instance_param_suitable = True
                         else: # Likely Type parameter
                              print("# Info: Element {} (Mark: '{}') Manufacturer parameter found, but it belongs to the Type. Skipping instance update.".format(element_info, mark_value))
                    #else: Parameter not found or is read-only

                    if not is_instance_param_suitable: # Consolidated check
                        skipped_no_mfr_param += 1
                        # print("# Skipping Element {} (Mark: '{}') - Instance Manufacturer parameter not found, not suitable, or read-only.".format(element_info, mark_value)) # Verbose
                        continue

                    # Check storage type
                    if mfr_param.StorageType != StorageType.String:
                        skipped_mfr_wrong_type += 1
                        print("# Skipping Element {} (Mark: '{}') - Manufacturer parameter is not a String type (Type: {}).".format(element_info, mark_value, mfr_param.StorageType))
                        continue

                    # Set the Manufacturer value (Transaction must be active outside this script)
                    try:
                        current_mfr = mfr_param.AsString()
                        # Check if update is actually needed
                        if current_mfr != target_mfr:
                            # Transaction must be started BEFORE this call by the external host
                            set_result = mfr_param.Set(target_mfr)
                            if set_result:
                                updated_doors += 1
                                # print("# Updated Element {} (Mark: '{}') Manufacturer to '{}'".format(element_info, mark_value, target_mfr)) # Verbose success
                            else:
                                error_count += 1
                                print("# Error setting Manufacturer for Element {} (Mark: '{}'). Set method returned false.".format(element_info, mark_value))
                        # else: # Optional: uncomment for verbose output if value is already correct
                            # print("# Element {} (Mark: '{}') Manufacturer already set to '{}'".format(element_info, mark_value, target_mfr))
                    except SystemException as set_ex:
                        error_count += 1
                        print("# Error setting Manufacturer for Element {} (Mark: '{}'): {}".format(element_info, mark_value, set_ex.Message))

                else:
                    # This element's mark is not one we need to update
                    skipped_mark_not_in_list += 1
                    # print("# Skipping Element {} - Mark '{}' not in the update list.".format(element_info, mark_value)) # Very Verbose

            except SystemException as proc_ex:
                error_count += 1
                # Try getting Mark value for better error message if possible
                mark_val_for_error = "N/A"
                try:
                    mp = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                    if mp and mp.HasValue: mark_val_for_error = mp.AsString()
                except: pass # Ignore errors getting mark during error handling
                print("# Error processing Element {} (Mark: '{}'): {}".format(element_info, mark_val_for_error, proc_ex.Message))
        # End of loop
    elif collection_failed:
         print("# Door collection failed. Cannot process.")
    else:
         print("# No door instances found in the project (Category OST_Doors) to process.")


    # --- Summary ---
    print("--- Door Manufacturer Update Summary ---")
    print("Target Mark/Manufacturer Pairs Parsed: {}".format(len(mark_to_mfr_map)))
    print("Total Elements Found (OST_Doors): {}".format(len(doors) if doors else 0))
    print("Total Elements Processed: {}".format(processed_elements))
    print("Doors Successfully Updated: {}".format(updated_doors))
    print("Skipped (Mark Param Missing/Empty): {}".format(skipped_no_mark_param))
    print("Skipped (Mark Value Not in List): {}".format(skipped_mark_not_in_list))
    print("Skipped (Instance Mfr Param Missing/Inapplicable/ReadOnly): {}".format(skipped_no_mfr_param))
    print("Skipped (Mfr Param Wrong Type): {}".format(skipped_mfr_wrong_type))
    print("Errors Encountered During Update: {}".format(error_count))
    print("--- Script Finished ---")