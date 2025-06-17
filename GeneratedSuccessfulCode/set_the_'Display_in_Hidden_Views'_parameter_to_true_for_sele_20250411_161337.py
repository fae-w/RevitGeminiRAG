# Import necessary classes
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import Element, Parameter, ElementId
from System import Exception

# --- Configuration ---
# *** Assumption: The parameter is named exactly "Display in Hidden Views" ***
# *** This is assumed to be a custom Shared or Project Parameter. ***
# *** This parameter is assumed to be of Yes/No type (integer internally). ***
parameter_name = "Display in Hidden Views"
target_value = 1 # 1 represents True/Yes for Yes/No parameters

# --- Get Selection ---
# uidoc is assumed to be pre-defined
selection_ids = uidoc.Selection.GetElementIds()

if not selection_ids or len(selection_ids) == 0:
    print("# No elements selected.")
else:
    print("# Processing {} selected elements...".format(len(selection_ids)))
    modified_count = 0
    not_found_count = 0
    read_only_count = 0
    wrong_type_count = 0
    error_count = 0
    already_set_count = 0

    # --- Iterate and Modify ---
    # doc is assumed to be pre-defined
    for element_id in selection_ids:
        element = None # Reset element for each iteration
        try:
            element = doc.GetElement(element_id)
            if not element:
                # print("# Skipping invalid element ID: {}".format(element_id)) # Optional Debug
                continue

            # Find the parameter by name - LookupParameter is generally best for instance parameters by name
            param = element.LookupParameter(parameter_name)

            # Fallback: Iterate through parameters if LookupParameter fails (e.g., for some type parameters accessed via instance)
            if param is None:
                found_in_iteration = False
                for p in element.Parameters:
                    if p.Definition.Name == parameter_name:
                        param = p
                        found_in_iteration = True
                        break
                if not found_in_iteration:
                     not_found_count += 1
                     # print("# Parameter '{}' not found on element ID: {}".format(parameter_name, element_id)) # Optional Debug
                     continue

            # Check if parameter is read-only
            if param.IsReadOnly:
                # Check if it's read-only but already has the desired value
                try:
                    current_value_check = param.AsInteger()
                    if current_value_check == target_value:
                        already_set_count += 1
                    else:
                        read_only_count += 1
                        # print("# Parameter '{}' is read-only on element ID: {}".format(parameter_name, element_id)) # Optional Debug
                except:
                    # Cannot even read as integer, still count as read-only issue
                    read_only_count += 1
                continue # Skip setting if read-only

            # Check current value before setting (assuming integer type for Yes/No)
            try:
                current_value = param.AsInteger()
                if current_value == target_value:
                    already_set_count += 1
                    continue # Already set correctly, no need to modify
            except Exception as type_ex:
                # Parameter exists but is not an integer type (e.g., Text, Length)
                wrong_type_count += 1
                # print("# Warning: Parameter '{}' on element ID {} is not an integer type (expected Yes/No). Cannot compare or set. Error: {}".format(parameter_name, element_id, type_ex)) # Optional Debug
                continue

            # Set the parameter value
            try:
                success = param.Set(target_value)
                if success:
                    modified_count += 1
                else:
                    # Set() returned False, indicating failure for some reason
                    error_count += 1
                    # print("# Failed to set parameter '{}' on element ID: {} (Set returned False)".format(parameter_name, element_id)) # Optional Debug
            except Exception as set_ex:
                 error_count += 1
                 print("# Error setting parameter '{}' on element ID {}: {}".format(parameter_name, element_id, set_ex))

        except Exception as e:
            error_count += 1
            element_info = element.Name if element else "N/A"
            print("# Error processing element ID {}: {} (Element Name: {})".format(element_id, e, element_info))

    # --- Summary ---
    print("\n# --- Parameter Modification Summary ---")
    print("# Parameter Name Assumed: '{}'".format(parameter_name))
    print("# Target Value: {} (True/Yes)".format(target_value))
    print("# Selected elements attempted: {}".format(len(selection_ids)))
    print("# Elements successfully modified: {}".format(modified_count))
    print("# Elements where parameter was already set correctly: {}".format(already_set_count))
    print("# Elements where parameter was not found: {}".format(not_found_count))
    print("# Elements where parameter was read-only: {}".format(read_only_count))
    print("# Elements where parameter had wrong data type (not Yes/No): {}".format(wrong_type_count))
    print("# Errors encountered during processing/setting: {}".format(error_count))

    if not_found_count > 0:
        print("# Note: Parameter '{}' must exist on the selected elements.".format(parameter_name))
        print("#       This might be a custom Shared or Project parameter.")