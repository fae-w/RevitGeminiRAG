# Purpose: This script selects Revit elements created by a specific user in a workshared model.

# Purpose: This script selects all Revit elements created by a specified user in a workshared model.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Required for List<T>
from Autodesk.Revit.DB import FilteredElementCollector, ElementId, WorksharingUtils, WorksharingTooltipInfo
from System.Collections.Generic import List

# Define the target username
target_user = "JohnDoe"

# List to store the IDs of elements created by the target user
created_element_ids = []

# Check if the document is workshared, as creator info relies on worksharing
if not doc.IsWorkshared:
    print("# Document is not workshared. Cannot determine element creator.")
else:
    # Collect all elements in the document (excluding element types)
    collector = FilteredElementCollector(doc).WhereElementIsNotElementType()

    # Iterate through elements and check the creator
    for element in collector:
        try:
            # Get worksharing tooltip information for the element
            tooltip_info = WorksharingUtils.GetWorksharingTooltipInfo(doc, element.Id)
            
            # Check if the creator matches the target user
            if tooltip_info and tooltip_info.Creator == target_user:
                created_element_ids.append(element.Id)
        except Exception as e:
            # Some elements might not have worksharing info or cause errors
            # print(f"# Debug: Could not get worksharing info for element {element.Id}. Error: {e}") # Escaped
            pass # Silently skip elements that cause issues

    # Select the found elements
    if created_element_ids:
        selection_list = List[ElementId](created_element_ids)
        try:
            uidoc.Selection.SetElementIds(selection_list)
            # print(f"# Selected {len(created_element_ids)} elements created by {target_user}.") # Escaped Optional output
        except Exception as sel_ex:
            print(f"# Error setting selection: {sel_ex}") # Escaped
    else:
        print(f"# No elements found created by user '{target_user}'.") # Escaped