# Purpose: This script updates the 'Website' and 'Warranty Length' parameters of Revit furniture types based on a provided data mapping.

﻿import clr
# Import necessary Revit DB classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilySymbol, # Represents Family Type in the API
    ElementType, # FamilySymbol inherits from ElementType
    Parameter,
    StorageType,
    BuiltInParameter # Might be useful for name, but not directly for Website/Warranty
)
from System import String, Exception as SystemException

# --- Input Data ---
# Multi-line string containing the TypeName/URL/Warranty mapping
# Format: TypeName,URL,Warranty (header is ignored)
data_string = """TypeName,URL,Warranty
ExecChair-Leather,www.mfgy.com/ec01,5 Years
StdDesk-1500,www.mfgx.com/sd15,1 Year"""

# --- Parameters to Update ---
# Exact names of the TYPE parameters to update (case-sensitive)
website_param_name = "Website"
warranty_param_name = "Warranty Length"

# --- Parse Input Data ---
type_data_map = {}
lines = data_string.strip().split('\n')
# Skip header line (index 0)
for line in lines[1:]:
    parts = line.strip().split(',', 2) # Split into max 3 parts: TypeName, URL, Warranty
    if len(parts) == 3:
        type_name = parts[0].strip()
        url_value = parts[1].strip()
        warranty_value = parts[2].strip()
        if type_name: # Ensure type name is not empty
            type_data_map[type_name] = (url_value, warranty_value)
        else:
            print("# Warning: Skipping line with empty TypeName value: '{{}}'".format(line))
    else:
        print("# Warning: Skipping malformed line: '{{}}'".format(line))

if not type_data_map:
    print("# Error: No valid TypeName/URL/Warranty data found in the input.")
else:
    # --- Collect Furniture Types (Family Symbols) ---
    furniture_types = []
    collection_failed = False
    try:
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsElementType()
        # Ensure we get FamilySymbol objects
        furniture_types = [ft for ft in collector.ToElements() if isinstance(ft, FamilySymbol)]
    except SystemException as e:
        print("# Error collecting furniture types: {{}}".format(e.Message))
        collection_failed = True # Mark collection as failed

    # --- Counters for Summary ---
    processed_types = 0
    updated_types = 0
    skipped_type_not_in_list = 0
    skipped_param_not_found = 0
    skipped_param_read_only = 0
    skipped_param_wrong_type = 0
    error_count = 0

    if furniture_types:
        print("# Processing {{}} Furniture types (Family Symbols) found.".format(len(furniture_types)))
        print("# Looking for Type Names: {{}}".format(", ".join(type_data_map.keys())))

        # --- Iterate and Update ---
        # Transaction is handled externally by the C# wrapper
        for family_symbol in furniture_types:
            processed_types += 1
            type_id = family_symbol.Id
            type_info = "ID: {{}}".format(type_id)

            try:
                # Get the Type Name (FamilySymbol Name)
                # Element.Name is obsolete, use Element.Name property or GetName() if available,
                # or BuiltInParameter.SYMBOL_NAME_PARAM
                type_name_param = family_symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.HasValue:
                    current_type_name = type_name_param.AsString()
                else:
                    # Fallback using FamilySymbol.Name if available and reliable
                    try:
                        current_type_name = Element.Name.__get__(family_symbol) # Recommended way post Revit 2016
                    except:
                         print("# Warning: Could not get name for Type {{}}. Skipping.".format(type_info))
                         skipped_type_not_in_list += 1 # Count as skipped
                         continue

                if not current_type_name:
                    print("# Warning: Type {{}} has an empty name. Skipping.".format(type_info))
                    skipped_type_not_in_list += 1 # Count as skipped
                    continue

                # Check if this type name is in our target list
                if current_type_name in type_data_map:
                    target_url, target_warranty = type_data_map[current_type_name]
                    update_applied = False # Track if any update was made for this type

                    # --- Update 'Website' Parameter ---
                    website_param = family_symbol.LookupParameter(website_param_name)
                    if website_param:
                        if not website_param.IsReadOnly:
                            if website_param.StorageType == StorageType.String:
                                try:
                                    current_url = website_param.AsString()
                                    if current_url != target_url:
                                        set_result = website_param.Set(target_url)
                                        if set_result:
                                            update_applied = True
                                            # print("# Updated Website for Type '{{}}'".format(current_type_name)) # Verbose
                                        else:
                                            error_count += 1
                                            print("# Error setting Website for Type '{{}}'. Set returned false.".format(current_type_name))
                                except SystemException as set_ex:
                                    error_count += 1
                                    print("# Error setting Website for Type '{{}}': {{}}".format(current_type_name, set_ex.Message))
                            else:
                                skipped_param_wrong_type += 1
                                print("# Skipping Website for Type '{{}}' - Parameter is not String type (Type: {{}}).".format(current_type_name, website_param.StorageType))
                        else:
                            skipped_param_read_only += 1
                            print("# Skipping Website for Type '{{}}' - Parameter is read-only.".format(current_type_name))
                    else:
                        skipped_param_not_found += 1
                        print("# Skipping Website for Type '{{}}' - Parameter '{{}}' not found.".format(current_type_name, website_param_name))

                    # --- Update 'Warranty Length' Parameter ---
                    warranty_param = family_symbol.LookupParameter(warranty_param_name)
                    if warranty_param:
                        if not warranty_param.IsReadOnly:
                            if warranty_param.StorageType == StorageType.String:
                                try:
                                    current_warranty = warranty_param.AsString()
                                    if current_warranty != target_warranty:
                                        set_result = warranty_param.Set(target_warranty)
                                        if set_result:
                                            update_applied = True
                                            # print("# Updated Warranty for Type '{{}}'".format(current_type_name)) # Verbose
                                        else:
                                            error_count += 1
                                            print("# Error setting Warranty Length for Type '{{}}'. Set returned false.".format(current_type_name))
                                except SystemException as set_ex:
                                    error_count += 1
                                    print("# Error setting Warranty Length for Type '{{}}': {{}}".format(current_type_name, set_ex.Message))
                            else:
                                skipped_param_wrong_type += 1
                                print("# Skipping Warranty Length for Type '{{}}' - Parameter is not String type (Type: {{}}).".format(current_type_name, warranty_param.StorageType))
                        else:
                            skipped_param_read_only += 1
                            print("# Skipping Warranty Length for Type '{{}}' - Parameter is read-only.".format(current_type_name))
                    else:
                        skipped_param_not_found += 1
                        print("# Skipping Warranty Length for Type '{{}}' - Parameter '{{}}' not found.".format(current_type_name, warranty_param_name))

                    if update_applied:
                        updated_types += 1

                else:
                    # This type name is not in our update list
                    skipped_type_not_in_list += 1
                    # print("# Skipping Type - Name '{{}}' not in the update list.".format(current_type_name)) # Verbose

            except SystemException as proc_ex:
                error_count += 1
                # Try getting name for better error message if possible
                name_for_error = "N/A"
                try: name_for_error = Element.Name.__get__(family_symbol)
                except: pass
                print("# Error processing Type {{}} (Name: '{{}}'): {{}}".format(type_info, name_for_error, proc_ex.Message))
        # End of loop

    elif collection_failed:
         print("# Furniture Type collection failed. Cannot process.")
    else:
         print("# No Furniture types (Family Symbols) found in the project (Category OST_Furniture).")

    # --- Summary ---
    print("--- Furniture Type Parameter Update Summary ---")
    print("Target Type/Data Pairs Parsed: {{}}".format(len(type_data_map)))
    print("Total Furniture Types Found: {{}}".format(len(furniture_types) if furniture_types else 0))
    print("Total Types Processed: {{}}".format(processed_types))
    print("Types Successfully Updated (at least one parameter): {{}}".format(updated_types))
    print("Skipped (Type Name Not in List or Empty/Unreadable): {{}}".format(skipped_type_not_in_list))
    # Note: Parameter skips are counted per parameter, not per type
    print("Skipped Parameter Updates (Not Found): {{}}".format(skipped_param_not_found))
    print("Skipped Parameter Updates (Read-Only): {{}}".format(skipped_param_read_only))
    print("Skipped Parameter Updates (Wrong Type): {{}}".format(skipped_param_wrong_type))
    print("Errors Encountered During Processing/Update: {{}}".format(error_count))
    print("--- Script Finished ---")