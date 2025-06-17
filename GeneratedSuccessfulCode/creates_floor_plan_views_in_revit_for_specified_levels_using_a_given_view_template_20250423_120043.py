# Purpose: This script creates floor plan views in Revit for specified levels using a given view template.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import Dictionary, List

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
target_level_names = ["L2", "L3", "L4", "L5"]
view_template_name = "Architectural Plan"
view_name_prefix = "FP - " # Optional prefix for the new view names

# --- Helper Functions ---

def find_levels_by_name(doc_param, level_names):
    """Finds Level elements by their exact names."""
    level_dict = Dictionary[str, ElementId]()
    levels_collector = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    found_names = set()

    for level in levels_collector:
        try:
            level_name = level.Name
            # Alternative using BuiltInParameter:
            # name_param = level.get_Parameter(BuiltInParameter.DATUM_TEXT) # Or LEVEL_NAME
            # if name_param: level_name = name_param.AsString() else: continue

            if level_name in level_names:
                if level_name not in found_names:
                    level_dict[level_name] = level.Id
                    found_names.add(level_name)
                # else: # Optional: Handle duplicate level names if necessary
                #     print("# Warning: Duplicate level name found: {}".format(level_name))
        except Exception as e:
            print("# Warning: Error accessing level name for ID {}: {}".format(level.Id, e))
            continue

    missing_levels = [name for name in level_names if name not in found_names]
    if missing_levels:
        print("# Warning: Could not find Levels with the following names: {}".format(", ".join(missing_levels)))

    return level_dict

def find_view_template_by_name(doc_param, template_name):
    """Finds a View Template by its exact name."""
    templates_collector = FilteredElementCollector(doc_param).OfClass(View).ToElements()
    for view in templates_collector:
        if view.IsTemplate and view.Name == template_name:
            return view.Id
    print("# Error: View Template named '{}' not found.".format(template_name))
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

# 1. Find the specified Levels
levels_to_create_views_for = find_levels_by_name(doc, target_level_names)
if not levels_to_create_views_for or levels_to_create_views_for.Count == 0:
    print("# Error: No target levels found. Stopping script.")
    # Exit gracefully if no levels were found matching the names
else:
    # 2. Find the View Template
    template_id = find_view_template_by_name(doc, view_template_name)

    # 3. Find a Floor Plan ViewFamilyType
    floor_plan_vft_id = find_floor_plan_vft(doc)

    # Proceed only if template and VFT are found
    if template_id != ElementId.InvalidElementId and floor_plan_vft_id != ElementId.InvalidElementId:
        created_view_count = 0
        # 4. Iterate through found levels and create views
        for level_name in levels_to_create_views_for.Keys:
            level_id = levels_to_create_views_for[level_name]
            new_view_plan = None
            try:
                # Create the new floor plan view
                new_view_plan = ViewPlan.Create(doc, floor_plan_vft_id, level_id)
                # print("# Successfully created view for level '{}' (ID: {})".format(level_name, new_view_plan.Id)) # Optional debug

                # Apply the view template
                try:
                    new_view_plan.ViewTemplateId = template_id
                    # print("# Applied template '{}' to view for level '{}'".format(view_template_name, level_name)) # Optional debug
                except Exception as template_ex:
                     print("# Warning: Failed to apply template '{}' to view for level '{}'. Error: {}".format(view_template_name, level_name, template_ex))

                # Optionally rename the view
                try:
                     view_name = view_name_prefix + level_name
                     # Check if name already exists - Revit might handle duplicates, but good practice to check or make unique
                     # existing_view_names = [v.Name for v in FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()]
                     # if view_name in existing_view_names: view_name += " - New" # Basic uniqueness
                     new_view_plan.Name = view_name
                     # print("# Renamed view to '{}'".format(view_name)) # Optional debug
                except Exception as name_ex:
                     print("# Warning: Could not rename the new view for level '{}'. Error: {}".format(level_name, name_ex))

                created_view_count += 1

            except Exception as create_ex:
                print("# Error creating floor plan view for level '{}' (ID: {}). Error: {}".format(level_name, level_id, create_ex))

        if created_view_count > 0:
            print("# Successfully created {} floor plan views.".format(created_view_count))
        else:
            print("# No floor plan views were created.")

    else:
        print("# Prerequisite missing: View Template or Floor Plan View Family Type not found. Stopping script.")