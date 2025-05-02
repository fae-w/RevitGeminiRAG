# Purpose: This script creates a new ceiling plan view in Autodesk Revit for a specified level.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewFamilyType,
    ViewPlan,
    ElementId,
    ViewType,
    BuiltInParameter
)

# --- Configuration ---
target_level_name = "L2"
# Optional: Specify a ViewFamilyType name if needed, otherwise finds the first ceiling plan type.
# target_vft_name = "Ceiling Plan"
view_name_prefix = "" # Optional: Add a prefix to the default view name

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels_collector = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    for level in levels_collector:
        try:
            # Using Name property is generally reliable
            if level.Name == level_name:
                return level.Id
        except Exception as e:
            print("# Warning: Error accessing level name for ID {}: {}".format(level.Id, e))
            continue
    print("# Error: Level named '{}' not found.".format(level_name))
    return ElementId.InvalidElementId

def find_ceiling_plan_vft(doc_param, specific_name=None):
    """Finds a Ceiling Plan ViewFamilyType, optionally by name."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    first_found_vft_id = ElementId.InvalidElementId
    for vft in vfts:
        # Check if it's a CeilingPlan ViewType
        if vft.ViewFamily == ViewType.CeilingPlan:
            if specific_name:
                if vft.Name == specific_name:
                    return vft.Id # Found specific name
            elif first_found_vft_id == ElementId.InvalidElementId:
                 first_found_vft_id = vft.Id # Store the first one found

    if specific_name:
        print("# Error: Ceiling Plan View Family Type named '{}' not found.".format(specific_name))
        return ElementId.InvalidElementId
    elif first_found_vft_id != ElementId.InvalidElementId:
         # print("# Info: Using the first available Ceiling Plan View Family Type found.") # Optional info
         return first_found_vft_id
    else:
        print("# Error: No Ceiling Plan View Family Type found in the document.")
        return ElementId.InvalidElementId

# --- Main Logic ---

# 1. Find the specified Level
level_id = find_level_by_name(doc, target_level_name)

# 2. Find a suitable Ceiling Plan ViewFamilyType
# Use None to find the first available ceiling plan VFT, or specify target_vft_name
ceiling_plan_vft_id = find_ceiling_plan_vft(doc) # Find first available
# ceiling_plan_vft_id = find_ceiling_plan_vft(doc, target_vft_name) # Find by specific name if needed

# 3. Proceed only if level and VFT are found
if level_id != ElementId.InvalidElementId and ceiling_plan_vft_id != ElementId.InvalidElementId:
    new_view_plan = None
    try:
        # Create the new ceiling plan view using ViewPlan.Create
        # ViewPlan.Create works for FloorPlan, CeilingPlan, AreaPlan, or StructuralPlan ViewTypes
        new_view_plan = ViewPlan.Create(doc, ceiling_plan_vft_id, level_id)

        # Optional: Rename the view (Revit usually names it based on level initially)
        if view_name_prefix:
            try:
                 # Construct the desired name
                 level_element = doc.GetElement(level_id)
                 base_name = level_element.Name if level_element else "Unknown Level"
                 view_name = view_name_prefix + base_name

                 # Check if the name already exists and adjust if needed (basic example)
                 existing_view_names = [v.Name for v in FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()]
                 counter = 1
                 final_view_name = view_name
                 while final_view_name in existing_view_names:
                     final_view_name = "{}_{}".format(view_name, counter)
                     counter += 1

                 if new_view_plan.Name != final_view_name: # Only rename if necessary or prefix used
                     new_view_plan.Name = final_view_name
                     # print("# Renamed view to '{}'".format(final_view_name)) # Optional debug
            except Exception as name_ex:
                 print("# Warning: Could not rename the new view for level '{}'. Error: {}".format(target_level_name, name_ex))

        print("# Successfully created ceiling plan view '{}' for level '{}'.".format(new_view_plan.Name, target_level_name))

    except Exception as create_ex:
        print("# Error creating ceiling plan view for level '{}'. Error: {}".format(target_level_name, create_ex))

else:
    # Print messages about which prerequisite failed
    if level_id == ElementId.InvalidElementId:
        print("# Failed: Could not find Level '{}'.".format(target_level_name))
    if ceiling_plan_vft_id == ElementId.InvalidElementId:
        print("# Failed: Could not find a suitable Ceiling Plan View Family Type.")
    print("# View creation aborted due to missing prerequisites.")