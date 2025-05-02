# Purpose: This script identifies and modifies duplicate door Mark values in a Revit model.

﻿import clr
clr.AddReference('System.Collections')
clr.AddReference('RevitAPI')
from System.Collections.Generic import Dictionary, List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    ElementId,
    BuiltInParameter,
    Parameter,
    Element
)

# Dictionary to store Mark values and the corresponding Element IDs
mark_map = Dictionary[str, List[ElementId]]()

# Collect all door instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

# Populate the dictionary with Mark values and Element IDs
for door in collector:
    # Ensure it's a FamilyInstance to have Mark parameter readily accessible in typical scenarios
    # Note: Some doors might be other types, but Mark is common on FamilyInstances
    if isinstance(door, FamilyInstance):
        try:
            mark_param = door.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            if mark_param and mark_param.HasValue:
                mark_value = mark_param.AsString()
                # Only process non-empty/non-whitespace Mark values
                if mark_value and mark_value.strip():
                    mark_value_str = mark_value.strip() # Use stripped value as key
                    if mark_value_str not in mark_map:
                        mark_map[mark_value_str] = List[ElementId]()
                    mark_map[mark_value_str].Add(door.Id)
        except Exception as e:
            # Log error getting mark parameter for an element (optional, can be logged by wrapper)
            # print("# Error getting Mark for element {{}}: {{}}".format(door.Id, e)) # Escaped
            pass # Continue with the next element

# Iterate through the dictionary to find duplicates and modify
elements_modified_count = 0
# Corrected iteration over .NET Dictionary
for kvp in mark_map:
    mark_value = kvp.Key
    element_ids = kvp.Value

    if element_ids.Count > 1:
        # Found duplicate Mark values
        highest_id_element = None
        highest_id_value = -1

        # Find the element with the highest ElementId.IntegerValue among the duplicates
        for element_id in element_ids:
            try:
                element = doc.GetElement(element_id)
                if element:
                    # Compare IntegerValues to find the highest
                    current_id_int_value = element_id.IntegerValue # Use property directly
                    if current_id_int_value > highest_id_value:
                        highest_id_value = current_id_int_value
                        highest_id_element = element
            except Exception as e:
                 # print("# Error retrieving element {{}}: {{}}".format(element_id, e)) # Escaped
                 pass # Skip this element if retrieval fails

        # Modify the Mark of the element with the highest ID
        if highest_id_element:
            try:
                mark_param = highest_id_element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
                if mark_param and not mark_param.IsReadOnly:
                    current_mark = mark_param.AsString()
                    # Check if already appended to prevent multiple appends on re-runs
                    # Also check if current_mark matches the key we are processing (in case it was changed externally)
                    if current_mark and current_mark.strip() == mark_value and not current_mark.endswith("_Duplicate"):
                        new_mark = current_mark + "_Duplicate"
                        mark_param.Set(new_mark)
                        elements_modified_count += 1
                    # else:
                        # print("# Skipping element {{}} - Mark already ends with _Duplicate, is empty, or differs from initial.".format(highest_id_element.Id)) # Escaped Optional info
                # else:
                    # print("# Skipping element {{}} - Mark parameter not found or read-only".format(highest_id_element.Id)) # Escaped Optional info
            except Exception as e:
                # print("# Error modifying Mark for element {{}}: {{}}".format(highest_id_element.Id, e)) # Escaped
                pass # Continue processing other duplicate groups

# Optional: Print summary of changes (will be captured by the C# wrapper's log if uncommented)
# print("# Processed duplicate Marks. Modified {{}} elements.".format(elements_modified_count)) # Escaped