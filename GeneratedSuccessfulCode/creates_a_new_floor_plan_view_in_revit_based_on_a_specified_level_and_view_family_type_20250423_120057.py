# Purpose: This script creates a new floor plan view in Revit based on a specified level and view family type.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewFamilyType,
    ViewPlan,
    ElementId,
    ViewType,
    BuiltInParameter,
    View
)

# --- Configuration ---
target_level_name = "M1"
target_vft_name = "Mezzanine Plan" # Specific View Family Type name requested
# view_name_prefix = "" # Optional: Add a prefix to the default view name (not requested)

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

def find_floor_plan_vft_by_name(doc_param, specific_name):
    """Finds a Floor Plan ViewFamilyType by its exact name."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        # Check if it's a FloorPlan ViewType AND matches the specified name
        if vft.ViewFamily == ViewType.FloorPlan and vft.Name == specific_name:
             return vft.Id # Found specific name

    print("# Error: Floor Plan View Family Type named '{}' not found.".format(specific_name))
    return ElementId.InvalidElementId

# --- Main Logic ---

# 1. Find the specified Level
level_id = find_level_by_name(doc, target_level_name)

# 2. Find the specified Floor Plan ViewFamilyType
floor_plan_vft_id = find_floor_plan_vft_by_name(doc, target_vft_name)

# 3. Proceed only if level and VFT are found
if level_id != ElementId.InvalidElementId and floor_plan_vft_id != ElementId.InvalidElementId:
    new_view_plan = None
    try:
        # Create the new floor plan view
        new_view_plan = ViewPlan.Create(doc, floor_plan_vft_id, level_id)

        # Revit usually names the view based on the level by default.
        # Optional: Rename if needed, e.g., add a prefix or ensure uniqueness.
        # Since no prefix was requested, we'll rely on Revit's default naming unless it clashes.
        # We can check for clashes and append a number if needed, but keeping it simple for now.
        # existing_view_names = [v.Name for v in FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()]
        # base_name = new_view_plan.Name # Get the default name assigned by Revit
        # final_view_name = base_name
        # counter = 1
        # while final_view_name in existing_view_names:
        #     final_view_name = "{}_{}".format(base_name, counter)
        #     counter += 1
        # if new_view_plan.Name != final_view_name:
        #     new_view_plan.Name = final_view_name

        print("# Successfully created floor plan view '{}' for level '{}' using type '{}'.".format(new_view_plan.Name, target_level_name, target_vft_name))

    except Exception as create_ex:
        print("# Error creating floor plan view for level '{}' using type '{}'. Error: {}".format(target_level_name, target_vft_name, create_ex))

else:
    # Print messages about which prerequisite failed
    if level_id == ElementId.InvalidElementId:
        print("# Failed: Could not find Level '{}'.".format(target_level_name))
    if floor_plan_vft_id == ElementId.InvalidElementId:
        print("# Failed: Could not find Floor Plan View Family Type named '{}'.".format(target_vft_name))
    print("# View creation aborted due to missing prerequisites.")