# Purpose: This script updates a 'Subject To Vandalism' parameter on Revit elements based on their associated space and input data.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # For string processing
import System
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    Parameter,
    StorageType,
    Element,
    ElementId,
    Phase # Needed for GetSpaceAtPoint
)
# Import Space from the correct namespace for MEP Spaces
from Autodesk.Revit.DB.Mechanical import Space

# --- Input Data ---
# Format: SpaceNumber,VandalismRisk (Yes/No)
input_data = """SpaceNumber,VandalismRisk
коридор-01,Yes
офис-101,No
туалет-01,Yes"""

# --- Configuration ---
vandalism_param_name = "Subject To Vandalism" # Case sensitive parameter name

# --- Processing ---

# 1. Parse input data into a dictionary
space_vandalism_map = {} # Use standard braces
lines = input_data.strip().split('\n')
header = lines[0]
data_lines = lines[1:]

for line in data_lines:
    try:
        parts = line.strip().split(',')
        if len(parts) == 2:
            space_number = parts[0].strip()
            vandalism_risk_str = parts[1].strip().lower()
            # Convert Yes/No to 1/0 for Yes/No parameters
            vandalism_risk_value = 1 if vandalism_risk_str == 'yes' else 0
            space_vandalism_map[space_number] = vandalism_risk_value
        else:
            print("# Warning: Skipping invalid line format: {}".format(line))
    except Exception as parse_ex:
        print("# Error parsing line '{}': {}".format(line, parse_ex))

if not space_vandalism_map:
    print("# Error: No valid data parsed from input.")
else:
    print("# Successfully parsed {} space number mappings.".format(len(space_vandalism_map)))

    # 2. Create a map of Space ElementId to desired Vandalism value
    space_id_vandalism_map = {} # Use standard braces
    try:
        # Use MEPSpaces category
        space_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MEPSpaces).WhereElementIsNotElementType()
        found_spaces_count = 0
        mapped_spaces_count = 0
        for space in space_collector:
            # Ensure it's actually a Space object (though collector should handle this)
            if isinstance(space, Space):
                found_spaces_count += 1
                num_param = space.get_Parameter(BuiltInParameter.SPACE_NUMBER)
                if num_param and num_param.HasValue:
                    current_space_number = num_param.AsString()
                    if current_space_number in space_vandalism_map:
                        target_value = space_vandalism_map[current_space_number]
                        space_id_vandalism_map[space.Id] = target_value
                        mapped_spaces_count += 1
                        # print("# Debug: Mapping Space ID {} (Number: '{}') to Vandalism Value: {}".format(space.Id, current_space_number, target_value))

        print("# Found {} MEP Spaces in the model. Mapped {} spaces from input data.".format(found_spaces_count, mapped_spaces_count))

    except Exception as space_ex:
        print("# Error collecting or processing Spaces: {}".format(space_ex))

    # 3. Iterate through elements potentially hosted by these spaces and update the parameter
    if space_id_vandalism_map:
        updated_elements_count = 0
        elements_checked_count = 0
        param_errors = []
        param_not_found_assoc = [] # Parameter not found on associated elements
        param_read_only = []
        param_wrong_type = []
        already_set_count = 0
        associated_elements_count = 0

        try:
            # Collect all non-ElementType instances
            element_collector = FilteredElementCollector(doc).WhereElementIsNotElementType()

            # Determine a suitable phase (e.g., the last phase in the project)
            # A more robust approach might involve getting the phase from the active view or user input.
            doc_phases = doc.Phases
            phase = None
            if doc_phases.Size > 0:
                 phase = doc_phases.get_Item(doc_phases.Size - 1) # Use last phase by default


            print("# Starting element parameter update...")
            for element in element_collector:
                elements_checked_count += 1
                try:
                    associated_space_id = ElementId.InvalidElementId
                    found_association = False

                    # Method 1: Use GetSpaceAtPoint (often good for furniture, etc.)
                    location_point = None
                    if element.Location and hasattr(element.Location, 'Point') and element.Location.Point:
                         location_point = element.Location.Point

                    if location_point and phase:
                        try:
                            space_at_point = doc.GetSpaceAtPoint(location_point, phase)
                            if space_at_point and space_at_point.Id in space_id_vandalism_map:
                                associated_space_id = space_at_point.Id
                                found_association = True
                        except Exception as get_space_ex:
                            # Ignore errors from GetSpaceAtPoint if it fails for an element type
                            # print("# Debug: GetSpaceAtPoint failed for Element ID {}: {}".format(element.Id, get_space_ex))
                            pass

                    # Method 2: Fallback to SPACE_PARAM (common for MEP elements)
                    if not found_association:
                        space_param = element.get_Parameter(BuiltInParameter.SPACE_PARAM)
                        if space_param and space_param.StorageType == StorageType.ElementId and space_param.HasValue:
                            space_id_from_param = space_param.AsElementId()
                            if space_id_from_param in space_id_vandalism_map:
                                associated_space_id = space_id_from_param
                                found_association = True

                    # If the element is associated with a target space by either method
                    if found_association:
                        associated_elements_count += 1
                        target_value = space_id_vandalism_map[associated_space_id]

                        # Find the 'Subject To Vandalism' parameter by name
                        vandalism_param = element.LookupParameter(vandalism_param_name)

                        if vandalism_param:
                            if not vandalism_param.IsReadOnly:
                                if vandalism_param.StorageType == StorageType.Integer: # Yes/No parameters are Integers
                                    current_value = vandalism_param.AsInteger()
                                    if current_value != target_value:
                                        # --- Modification Start (Requires Transaction - handled externally) ---
                                        set_success = vandalism_param.Set(target_value)
                                        # --- Modification End ---
                                        if set_success:
                                            # print("  - Updated Element ID {}: Set '{}' to {} (from {})".format(element.Id, vandalism_param_name, target_value, current_value))
                                            updated_elements_count += 1
                                        else:
                                            msg = "Element ID {}: Failed to set '{}' using Set().".format(element.Id, vandalism_param_name)
                                            if msg not in param_errors: param_errors.append(msg)
                                    else:
                                        already_set_count +=1
                                else:
                                    msg = "Element ID {}: Parameter '{}' is not Integer type (found {}).".format(element.Id, vandalism_param_name, vandalism_param.StorageType.ToString())
                                    if msg not in param_wrong_type: param_wrong_type.append(msg)
                            else:
                                msg = "Element ID {}: Parameter '{}' is read-only.".format(element.Id, vandalism_param_name)
                                if msg not in param_read_only: param_read_only.append(msg)
                        else: # Parameter not found on this element associated with a target space
                            msg = "Element ID {}: Parameter '{}' not found.".format(element.Id, vandalism_param_name)
                            if msg not in param_not_found_assoc: param_not_found_assoc.append(msg)

                except Exception as elem_ex:
                    # Avoid overly verbose errors for elements that commonly lack location or space params
                    if "Location" not in str(elem_ex) and "SPACE_PARAM" not in str(elem_ex):
                         print("# Error processing Element ID {}: {}".format(element.Id, elem_ex))

            print("# Finished element processing.")
            print("# Report:")
            print("  - Elements Checked: {}".format(elements_checked_count))
            print("  - Elements Associated with Target Spaces: {}".format(associated_elements_count))
            print("  - Elements Updated: {}".format(updated_elements_count))
            print("  - Elements Already Correct: {}".format(already_set_count))
            if param_not_found_assoc:
                 print("  - Errors (Param '{}' Not Found on associated elements): {}".format(vandalism_param_name, len(param_not_found_assoc)))
            if param_read_only:
                 print("  - Errors (Parameter Read-Only): {}".format(len(param_read_only)))
            if param_wrong_type:
                 print("  - Errors (Parameter Wrong Type): {}".format(len(param_wrong_type)))
            if param_errors:
                 print("  - Errors (Set Failed): {}".format(len(param_errors)))

        except Exception as collector_ex:
            print("# Error collecting or iterating through elements: {}".format(collector_ex))
    else:
        print("# No spaces found matching the input data, no elements updated.")