# Purpose: This script changes the type of a selected Revit section view to a specified view family type.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewFamilyType,
    ViewSection,
    ElementId,
    ViewType
)
import System

# Define the target View Family Type name
target_view_type_name = "Wall Section Detail" # Or potentially just "Wall Section" depending on exact project setup

# 1. Get Selected Elements
selected_ids = uidoc.Selection.GetElementIds()

# 2. Check if exactly one element is selected
if not selected_ids or selected_ids.Count != 1:
    print("# Error: Please select exactly one Section View.")
else:
    selected_id = selected_ids[0]
    selected_element = doc.GetElement(selected_id)

    # 3. Check if the selected element is a ViewSection
    if not isinstance(selected_element, ViewSection):
        print("# Error: The selected element is not a Section View (ViewSection). It is a '{0}'.".format(selected_element.GetType().Name))
    else:
        current_section_view = selected_element
        print("# Selected Section View: '{0}' (ID: {1})".format(current_section_view.Name, current_section_view.Id))

        # 4. Find the target View Family Type
        target_vft_id = ElementId.InvalidElementId
        vfts = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()

        found_vft = None
        for vft in vfts:
            # Check if the name matches and it's a Section or Detail type (Wall Section Detail could be either)
            if vft.Name == target_view_type_name and (vft.ViewFamily == ViewType.Section or vft.ViewFamily == ViewType.Detail):
                 # Additional check: Ensure the new type is compatible with the current view's type.
                 # Generally, changing between Section types or Section->Detail is allowed.
                 # This basic check assumes compatibility if the name matches.
                 # A more robust check might involve API checks if they existed.
                found_vft = vft
                target_vft_id = vft.Id
                break # Stop searching once found

        # 5. Change the View Type if found
        if target_vft_id != ElementId.InvalidElementId and found_vft is not None:
            try:
                # Check if the type is already the target type
                if current_section_view.GetTypeId() == target_vft_id:
                     print("# The selected view is already of type '{0}'.".format(target_view_type_name))
                else:
                    # Attempt to change the type ID
                    current_section_view.ChangeTypeId(target_vft_id)
                    print("# Successfully changed the View Type of '{0}' to '{1}'.".format(current_section_view.Name, target_view_type_name))

            except System.Exception as e:
                print("# Error changing view type for '{0}'. Exception: {1}".format(current_section_view.Name, e))
                # Provide more context if possible
                print("# Ensure the target type '{0}' (Family: {1}) is compatible with the original Section View.".format(target_view_type_name, found_vft.ViewFamily.ToString()))


        else:
            print("# Error: View Family Type named '{0}' (compatible with Section/Detail) not found in the document.".format(target_view_type_name))