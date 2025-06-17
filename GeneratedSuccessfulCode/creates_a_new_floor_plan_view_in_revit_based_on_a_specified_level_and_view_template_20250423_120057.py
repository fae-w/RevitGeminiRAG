# Purpose: This script creates a new floor plan view in Revit based on a specified level and view template.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Not strictly needed for this specific script, but good practice
# from System.Collections.Generic import Dictionary # Not used here

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewFamilyType,
    ViewPlan,
    View,
    ElementId,
    ViewType,
    BuiltInParameter
)

# --- Configuration ---
target_level_name = "L4"
view_template_name = "Architectural Plan"
view_name_prefix = "" # Optional: Set a prefix for the new view name, e.g., "New FP - "

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels_collector = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    for level in levels_collector:
        try:
            # Using Name property is generally reliable
            if level.Name == level_name:
                return level.Id
            # Alternative using BuiltInParameter:
            # name_param = level.get_Parameter(BuiltInParameter.DATUM_TEXT) # Or LEVEL_NAME
            # if name_param and name_param.AsString() == level_name:
            #     return level.Id
        except Exception as e:
            print("# Warning: Error accessing level name for ID {{}}: {{}}".format(level.Id, e))
            continue
    print("# Error: Level named '{{}}' not found.".format(level_name))
    return ElementId.InvalidElementId

def find_view_template_by_name(doc_param, template_name):
    """Finds a View Template by its exact name."""
    templates_collector = FilteredElementCollector(doc_param).OfClass(View).ToElements()
    for view in templates_collector:
        if view.IsTemplate and view.Name == template_name:
            return view.Id
    print("# Error: View Template named '{{}}' not found.".format(template_name))
    return ElementId.InvalidElementId

def find_floor_plan_vft(doc_param):
    """Finds the first available Floor Plan ViewFamilyType."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        # Check if it's a FloorPlan ViewType
        if vft.ViewFamily == ViewType.FloorPlan:
            return vft.Id
    print("# Error: No Floor Plan View Family Type found in the document.")
    return ElementId.InvalidElementId

# --- Main Logic ---

# 1. Find the specified Level
level_id = find_level_by_name(doc, target_level_name)

# 2. Find the View Template
template_id = find_view_template_by_name(doc, view_template_name)

# 3. Find a Floor Plan ViewFamilyType
floor_plan_vft_id = find_floor_plan_vft(doc)

# 4. Proceed only if level, template, and VFT are found
if level_id != ElementId.InvalidElementId and template_id != ElementId.InvalidElementId and floor_plan_vft_id != ElementId.InvalidElementId:
    new_view_plan = None
    try:
        # Create the new floor plan view
        new_view_plan = ViewPlan.Create(doc, floor_plan_vft_id, level_id)
        # print("# Successfully created view for level '{{}}' (ID: {{}})".format(target_level_name, new_view_plan.Id)) # Optional debug message

        # Apply the view template immediately after creation
        try:
            # Ensure the template ID is valid before applying
            if template_id != ElementId.InvalidElementId:
                new_view_plan.ViewTemplateId = template_id
                # print("# Applied template '{{}}' to new view.".format(view_template_name)) # Optional debug message
            else:
                # This case should technically be caught by the outer if, but good to be explicit
                print("# Warning: Invalid template ID found, skipping template application.")

        except Exception as template_ex:
             print("# Warning: Failed to apply template '{{}}' to view for level '{{}}'. Error: {{}}".format(view_template_name, target_level_name, template_ex))

        # Optionally rename the view (Revit usually names it based on level initially)
        try:
             # Construct the desired name
             base_name = doc.GetElement(level_id).Name if level_id != ElementId.InvalidElementId else "Unknown Level"
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
                 # print("# Renamed view to '{{}}'".format(final_view_name)) # Optional debug

        except Exception as name_ex:
             print("# Warning: Could not rename the new view for level '{{}}'. Error: {{}}".format(target_level_name, name_ex))

        print("# Successfully created floor plan view '{{}}' for level '{{}}' and applied template '{{}}'.".format(new_view_plan.Name, target_level_name, view_template_name))

    except Exception as create_ex:
        print("# Error creating floor plan view for level '{{}}'. Error: {{}}".format(target_level_name, create_ex))
        # If creation failed but new_view_plan object exists, try to delete it?
        # This is complex within the no-transaction constraint, usually better to let the wrapper rollback.
        # if new_view_plan and new_view_plan.IsValidObject:
        #    try: doc.Delete(new_view_plan.Id) # Requires transaction
        #    except: pass
else:
    # Print messages about which prerequisite failed
    if level_id == ElementId.InvalidElementId:
        print("# Failed: Could not find Level '{{}}'.".format(target_level_name))
    if template_id == ElementId.InvalidElementId:
        print("# Failed: Could not find View Template '{{}}'.".format(view_template_name))
    if floor_plan_vft_id == ElementId.InvalidElementId:
        print("# Failed: Could not find a Floor Plan View Family Type.")
    print("# View creation aborted due to missing prerequisites.")