# Purpose: This script applies a specific view template to floor plan views associated with specified levels that do not already have a template assigned.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewPlan,
    Level,
    ElementId,
    ViewType
)
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

# --- Configuration ---
target_level_names = ['L1 - Block 35', 'L1 - Block 43', 'L2', 'L3', 'L4', 'L5']
target_template_name = 'Life Safety Plan'

# --- Helper Function: Find View Template ---
def find_view_template_by_name(doc_param, template_name):
    """Finds a View Template by its exact name."""
    collector = FilteredElementCollector(doc_param).OfClass(View)
    for view in collector:
        # Check if it's a template and the name matches
        if view.IsTemplate and view.Name == template_name:
            return view.Id
    print("# Error: View Template named '{}' not found.".format(template_name))
    return ElementId.InvalidElementId

# --- Main Logic ---

# 1. Find the target View Template
template_id = find_view_template_by_name(doc, target_template_name)

if template_id == ElementId.InvalidElementId:
    print("# Script stopped: Target view template '{}' could not be found.".format(target_template_name))
else:
    # 2. Find relevant Floor Plan views
    views_to_modify = []
    all_views = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements() # More efficient to start with ViewPlan

    print("# Searching for Floor Plan views associated with levels: {}...".format(", ".join(target_level_names)))

    for view in all_views:
        # Ensure it's a Floor Plan and not a template itself
        if view.ViewType == ViewType.FloorPlan and not view.IsTemplate:
            associated_level = None
            level_name = None
            try:
                # View.GenLevel property returns the Level element directly
                associated_level = view.GenLevel
                if associated_level:
                     level_name = associated_level.Name
                else:
                    # print("# Debug: View '{}' (ID: {}) has no associated level.".format(view.Name, view.Id)) # Optional debug
                    continue # Skip views without an associated level
            except Exception as e:
                # print("# Warning: Could not get level for view '{}' (ID: {}). Error: {}".format(view.Name, view.Id, e)) # Optional debug
                continue # Skip views where level cannot be determined

            # Check if the level name is in our target list
            if level_name in target_level_names:
                # Check if the view currently has NO template assigned
                # ElementId.InvalidElementId represents no template assigned
                if view.ViewTemplateId == ElementId.InvalidElementId:
                    views_to_modify.append(view)
                    # print("# Debug: Found candidate view '{}' on level '{}' with no template.".format(view.Name, level_name)) # Optional debug
                # else:
                    # existing_template = doc.GetElement(view.ViewTemplateId)
                    # existing_template_name = existing_template.Name if existing_template else "Invalid ID"
                    # print("# Debug: Skipping view '{}' on level '{}' because it already has template '{}' assigned.".format(view.Name, level_name, existing_template_name)) # Optional debug


    # 3. Apply the template to the found views
    modified_count = 0
    if not views_to_modify:
        print("# No floor plan views found matching the criteria (correct level AND no existing view template).")
    else:
        print("# Found {} floor plan views matching criteria. Applying template '{}'...".format(len(views_to_modify), target_template_name))
        for view in views_to_modify:
            try:
                # Apply the template by setting the ViewTemplateId property
                view.ViewTemplateId = template_id
                modified_count += 1
                # print("# Applied template '{}' to view '{}'".format(target_template_name, view.Name)) # Optional Debug
            except Exception as e:
                print("# Warning: Failed to apply template to view '{}' (ID: {}). Error: {}".format(view.Name, view.Id, e))

        print("# Successfully applied template '{}' to {} views.".format(target_template_name, modified_count))
        if modified_count < len(views_to_modify):
             print("# Note: {} views could not have the template applied due to errors.".format(len(views_to_modify) - modified_count))