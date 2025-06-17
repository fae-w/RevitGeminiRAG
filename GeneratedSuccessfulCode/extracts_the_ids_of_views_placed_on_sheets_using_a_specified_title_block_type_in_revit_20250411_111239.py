# Purpose: This script extracts the IDs of views placed on sheets using a specified title block type in Revit.

# Purpose: This script extracts the IDs of views placed on sheets using a specific title block type in Revit.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for HashSet, List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilySymbol,
    FamilyInstance,
    BuiltInCategory,
    ViewSheet,
    Viewport,
    ElementId
)
from System.Collections.Generic import List, HashSet

# --- Configuration ---
target_titleblock_type_name = "A1 Metric Titleblock"

# --- Step 1: Find the Target Title Block Family Type ID ---
target_symbol_id = ElementId.InvalidElementId
collector_types = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)

# Iterate through title block types to find the matching one
for symbol in collector_types:
    # Ensure the element is valid and is a FamilySymbol
    if symbol and symbol.IsValidObject and isinstance(symbol, FamilySymbol):
        try:
            # Compare the type name (FamilySymbol.Name)
            if symbol.Name == target_titleblock_type_name:
                target_symbol_id = symbol.Id
                break # Found the target type, exit loop
        except Exception as e:
            # print("# DEBUG: Could not process FamilySymbol {}. Error: {}".format(symbol.Id, e)) # Escaped debug print
            pass # Continue searching other symbols

if target_symbol_id == ElementId.InvalidElementId:
    print("# Error: Title block type '{}' not found in the document.".format(target_titleblock_type_name))
else:
    # print("# Found Title Block Type ID: {}".format(target_symbol_id)) # Escaped debug print

    # --- Step 2: Find Sheets with the Target Title Block Instance ---
    matching_sheet_ids = HashSet[ElementId]()
    # Collect all title block instances in the document
    collector_instances = FilteredElementCollector(doc).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_TitleBlocks)

    for instance in collector_instances:
        # Ensure the element is valid and is a FamilyInstance
        if instance and instance.IsValidObject and isinstance(instance, FamilyInstance):
            try:
                # Check if the instance's type matches the target type ID
                # Comparing Symbol.Id is correct here. GetTypeId() also works.
                if instance.Symbol.Id == target_symbol_id:
                    owner_view_id = instance.OwnerViewId
                    # Ensure the owner view ID is valid
                    if owner_view_id != ElementId.InvalidElementId:
                        owner_view = doc.GetElement(owner_view_id)
                        # Ensure the owner element exists, is valid, and is a ViewSheet
                        if owner_view and owner_view.IsValidObject and isinstance(owner_view, ViewSheet):
                            matching_sheet_ids.Add(owner_view_id)
            except Exception as e:
                # print("# DEBUG: Could not process Title Block instance {}. Error: {}".format(instance.Id, e)) # Escaped debug print
                pass # Continue processing other instances

    # --- Step 3: Collect View IDs from Matching Sheets ---
    placed_view_ids = List[ElementId]() # Using List to store results

    if matching_sheet_ids.Count > 0:
        # print("# Found {} sheets using the target title block.".format(matching_sheet_ids.Count)) # Escaped debug print
        for sheet_id in matching_sheet_ids:
            try:
                sheet = doc.GetElement(sheet_id)
                # Ensure the sheet element is valid and is a ViewSheet
                if sheet and sheet.IsValidObject and isinstance(sheet, ViewSheet):
                    # Get all viewport IDs placed on this sheet
                    viewport_ids = sheet.GetAllViewports()
                    for vp_id in viewport_ids:
                        # Ensure the viewport ID is valid
                        if vp_id != ElementId.InvalidElementId:
                             viewport = doc.GetElement(vp_id)
                             # Ensure the viewport element exists, is valid, and is a Viewport
                             if viewport and viewport.IsValidObject and isinstance(viewport, Viewport):
                                 view_id = viewport.ViewId
                                 # Ensure the view ID obtained from the viewport is valid
                                 if view_id != ElementId.InvalidElementId:
                                     # Add the valid ViewId to our list
                                     placed_view_ids.Add(view_id)
            except Exception as e:
                # print("# Warning: Could not process viewports for sheet {}. Error: {}".format(sheet_id, e)) # Escaped warning
                pass # Continue with the next sheet
    # else:
        # print("# No sheets found using the target title block.") # Escaped info print

    # --- Step 4: Output the View IDs ---
    if placed_view_ids.Count > 0:
        # print("# Found {} views placed on sheets with title block '{}':".format(placed_view_ids.Count, target_titleblock_type_name)) # Escaped info print
        for view_id in placed_view_ids:
            print(view_id.ToString()) # Print each Element ID as a string
    else:
        # Check if sheets were found but no views were placed on them
        if matching_sheet_ids.Count > 0:
             print("# Found sheets using title block '{}', but no views were placed on them.".format(target_titleblock_type_name))
        # else: # This case is implicitly handled by the initial check for target_symbol_id
             # print("# No sheets found using title block '{}'.".format(target_titleblock_type_name)) # Escaped info print
             # pass