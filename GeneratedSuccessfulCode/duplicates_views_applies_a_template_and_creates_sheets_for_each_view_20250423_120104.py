# Purpose: This script duplicates views, applies a template, and creates sheets for each view.

﻿# Imports
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List # Keep if generic List needed, otherwise remove

# Revit API References
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Potentially needed if interacting with UI elements later, good practice to include
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    View,
    ViewPlan,
    # ViewSection, # Not explicitly needed unless differentiating strongly
    # View3D, # Not explicitly needed unless differentiating strongly
    ViewType,
    ElevationMarker,
    ViewSheet,
    Viewport,
    # FamilySymbol, # Not used
    ElementId,
    ViewDuplicateOption,
    BuiltInCategory,
    XYZ,
    # BoundingBoxUV, # Accessed via properties, direct import not needed
    # ViewFamily, # Not used
    ViewFamilyType,
    BuiltInParameter
)

# --- Configuration ---
target_level_name = "R1"
# target_view_type_name = "Roof Presentation Plan" # Cannot change type after duplication, skipping this part of the request.
target_template_name = "High Quality Render"
new_sheet_name_prefix = "Presentation - "
duplicate_option = ViewDuplicateOption.WithDetailing # Options: .Duplicate, .WithDetailing, .AsDependent

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels = FilteredElementCollector(doc_param).OfClass(Level).WhereElementIsNotElementType().ToElements()
    for level in levels:
        if level.Name == level_name:
            return level
    print("# Error: Level named '{}' not found.".format(level_name))
    return None

def find_view_template_by_name(doc_param, template_name):
    """Finds a View Template element by its exact name."""
    templates = FilteredElementCollector(doc_param).OfClass(View).WhereElementIsNotElementType().ToElements()
    for v in templates:
        if v.IsTemplate and v.Name == template_name:
            return v
    print("# Error: View Template named '{}' not found.".format(template_name))
    return None

def find_first_titleblock_type(doc_param):
    """Finds the first available Title Block Type."""
    collector = FilteredElementCollector(doc_param).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
    first_tb_type = collector.FirstElement()
    if not first_tb_type:
        print("# Error: No Title Block Types found in the project.")
        return ElementId.InvalidElementId
    # print("# Info: Using Title Block Type '{}'".format(first_tb_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())) # Optional Info using correct API
    return first_tb_type.Id

def get_views_for_level(doc_param, level_id):
    """Finds views associated with the specified Level ID."""
    views_on_level = []
    all_views = FilteredElementCollector(doc_param).OfClass(View).WhereElementIsNotElementType().ToElements()
    processed_ids = set() # Keep track of views already added

    for v in all_views:
        if v.Id in processed_ids:
            continue # Skip if already added

        # Skip templates and views that cannot be placed on sheets or duplicated robustly
        if v.IsTemplate or not v.CanBePrinted() or v.ViewType == ViewType.Schedule or v.ViewType == ViewType.Legend:
            continue

        associated = False
        try:
            # Primary check: LevelId property (most reliable for Plan Views)
            if hasattr(v, 'LevelId') and v.LevelId == level_id:
                 # Further check: Ensure it's a plan view if using LevelId directly
                 if isinstance(v, ViewPlan):
                     associated = True

            # Secondary check: Associated Level Parameter (for Sections, Elevations etc.)
            if not associated:
                level_param = v.get_Parameter(BuiltInParameter.ASSOCIATED_LEVEL) # Correct parameter name
                if level_param and not level_param.IsReadOnly and level_param.AsElementId() == level_id:
                    associated = True
                else: # Check older parameter as fallback for some view types
                    level_param_old = v.get_Parameter(BuiltInParameter.VIEW_ASSOCIATED_LEVEL)
                    if level_param_old and level_param_old.AsElementId() == level_id:
                         associated = True

            # Tertiary check for Elevations (check the marker's level)
            if not associated and v.ViewType == ViewType.Elevation:
                 # Find the marker associated with this elevation view
                 elev_markers = FilteredElementCollector(doc_param).OfClass(ElevationMarker).WhereElementIsNotElementType().ToElements()
                 for marker in elev_markers:
                     # Check if the marker itself is on the target level
                     if marker.LevelId == level_id:
                         # Check if this view belongs to this marker
                         for i in range(marker.MaximumViewCount):
                             try:
                                 view_id_at_index = marker.GetViewId(i)
                                 if view_id_at_index == v.Id:
                                      associated = True
                                      break # Found the view on this marker
                             except: # Handle potential errors if index is invalid etc.
                                 pass
                     if associated:
                         break # Found association via marker, stop checking markers

            if associated:
                views_on_level.append(v)
                processed_ids.add(v.Id)

        except Exception as e:
            # print("# Warning: Error checking level for view '{}' (ID: {}). Error: {}".format(v.Name, v.Id, e)) # Optional debug
            pass # Ignore views that cause errors during check
    return views_on_level


def get_unique_sheet_identifier(doc_param, base_value, is_name):
    """Generates a unique sheet name or number by appending numbers if necessary."""
    all_sheets = FilteredElementCollector(doc_param).OfClass(ViewSheet).ToElements()
    if is_name:
        existing_values = set(s.Name for s in all_sheets)
    else: # is_number
        existing_values = set(s.SheetNumber for s in all_sheets)

    final_value = base_value
    counter = 1
    # Limit loop to prevent infinite loops in edge cases
    max_attempts = 1000
    while final_value in existing_values and counter < max_attempts:
        final_value = "{}_{}".format(base_value, counter)
        counter += 1
    if counter >= max_attempts:
        print("# Warning: Could not find unique {} for base '{}' after {} attempts. Using last attempt.".format("name" if is_name else "number", base_value, max_attempts))
    return final_value

# --- Main Logic ---

# 1. Find necessary elements
target_level = find_level_by_name(doc, target_level_name)
view_template = find_view_template_by_name(doc, target_template_name)
title_block_type_id = find_first_titleblock_type(doc)

# Proceed only if level, template, and title block are found
if target_level and view_template and title_block_type_id != ElementId.InvalidElementId:
    level_id = target_level.Id
    template_id = view_template.Id

    # 2. Find views associated with the target level
    original_views = get_views_for_level(doc, level_id)
    if not original_views:
        print("# Info: No views found associated with Level '{}' that can be duplicated and placed.".format(target_level_name))

    # 3. Process each original view
    created_sheet_count = 0
    processed_view_count = 0
    failed_views = []

    for original_view in original_views:
        original_view_name = "Unnamed View"
        try:
            original_view_name = original_view.Name
        except:
            pass # Keep default name if access fails

        print("# Processing view: '{}' (ID: {})".format(original_view_name, original_view.Id))

        # Check if the view can be duplicated with the chosen option
        if not original_view.CanViewBeDuplicated(duplicate_option):
            print("# Warning: View '{}' cannot be duplicated with option '{}'. Skipping.".format(original_view_name, duplicate_option))
            failed_views.append(original_view_name + " (Cannot Duplicate)")
            continue

        try:
            processed_view_count += 1
            # a. Duplicate the view
            new_view_id = original_view.Duplicate(duplicate_option)
            new_view = doc.GetElement(new_view_id)
            if not new_view:
                print("# Error: Failed to retrieve duplicated view for '{}'.".format(original_view_name))
                failed_views.append(original_view_name + " (Duplication Failed)")
                continue

            new_view_name = "Unnamed Duplicated View"
            try:
                new_view_name = new_view.Name
            except:
                 pass # Use default name if retrieval fails

            print("# -> Duplicated '{}' to '{}'".format(original_view_name, new_view_name))

            # b. Change View Type - IMPOSSIBLE directly after duplication.
            # Applying a template is the closest viable alternative.
            print("# Info: Skipping 'Change View Type' step for '{}'. View Type cannot be changed after duplication.".format(new_view_name))

            # c. Apply the View Template
            try:
                if new_view.CanApplyViewTemplate(template_id): # Use CanApplyViewTemplate for better check
                    new_view.ViewTemplateId = template_id
                    print("# -> Applied template '{}' to '{}'".format(target_template_name, new_view_name))
                else:
                     # Try to get ViewFamilyType name for better logging
                     vt_name = "Unknown"
                     try:
                         vft = doc.GetElement(new_view.GetTypeId())
                         if vft and isinstance(vft, ViewFamilyType):
                             vt_name = vft.Name
                     except: pass
                     print("# Warning: Template '{}' cannot be applied to duplicated view '{}' (Type: {} / {}). Skipping template application.".format(target_template_name, new_view_name, new_view.ViewType, vt_name))
                     failed_views.append(new_view_name + " (Template Incompatible)")
            except Exception as template_ex:
                print("# Error applying template '{}' to view '{}'. Error: {}".format(target_template_name, new_view_name, template_ex))
                # Continue even if template application fails

            # d. Create a new Sheet
            sheet_base_name = new_sheet_name_prefix + original_view_name # Use original name for clarity in sheet title
            unique_sheet_name = get_unique_sheet_identifier(doc, sheet_base_name, True)

            # Generate a proposed sheet number based on original view name or count
            # Ensure uniqueness for sheet number separately
            sheet_number_base = "P-{}".format(processed_view_count) # Simple incrementing number
            unique_sheet_number = get_unique_sheet_identifier(doc, sheet_number_base, False)

            new_sheet = None
            try:
                new_sheet = ViewSheet.Create(doc, title_block_type_id)
                new_sheet.Name = unique_sheet_name
                new_sheet.SheetNumber = unique_sheet_number # Assign unique Sheet Number

                print("# -> Created sheet '{}' (Number: {})".format(unique_sheet_name, unique_sheet_number))
                created_sheet_count += 1
            except Exception as sheet_ex:
                print("# Error creating sheet for view '{}'. Error: {}".format(original_view_name, sheet_ex))
                # If sheet creation fails, the duplicated view still exists but isn't placed.
                failed_views.append(original_view_name + " (Sheet Creation Failed)")
                # Clean up duplicated view if sheet creation failed? Optional, depends on desired behavior.
                # try:
                #    doc.Delete(new_view_id)
                #    print("# -> Cleaned up duplicated view '{}' due to sheet creation failure.".format(new_view_name))
                # except Exception as del_ex:
                #    print("# Warning: Failed to clean up duplicated view '{}'. Error: {}".format(new_view_name, del_ex))
                continue # Skip placing if sheet creation failed

            # e. Place the duplicated view onto the new sheet
            try:
                if Viewport.CanAddViewToSheet(doc, new_sheet.Id, new_view_id):
                    # Calculate center point for placement
                    placement_point = XYZ(0, 0, 0) # Default to origin if outline fails
                    try:
                        # Use BoundingBoxXYZ of the sheet's graphics if available for better centering
                        sheet_gfx_bb = new_sheet.get_BoundingBox(None) # Pass None for view to get model coords BBox
                        if sheet_gfx_bb and sheet_gfx_bb.Min and sheet_gfx_bb.Max:
                            placement_point = (sheet_gfx_bb.Min + sheet_gfx_bb.Max) / 2.0
                        else:
                            # Fallback to Outline BBoxUV if graphics bbox fails
                            outline_bb = new_sheet.Outline
                            if outline_bb and outline_bb.Min and outline_bb.Max:
                                 center_u = (outline_bb.Min.U + outline_bb.Max.U) / 2.0
                                 center_v = (outline_bb.Min.V + outline_bb.Max.V) / 2.0
                                 placement_point = XYZ(center_u, center_v, 0)
                            else:
                                 print("# Warning: Could not get sheet Outline BBox or Graphics BBox for '{}'. Using default placement point (0,0,0).".format(new_sheet.Name))
                    except Exception as bb_ex:
                         print("# Warning: Error getting sheet BBox for '{}'. Using default placement point (0,0,0). Error: {}".format(new_sheet.Name, bb_ex))

                    viewport = Viewport.Create(doc, new_sheet.Id, new_view_id, placement_point)
                    if viewport:
                        print("# -> Placed view '{}' onto sheet '{}'".format(new_view_name, new_sheet.Name))
                    else:
                        print("# Error: Failed to create viewport for view '{}' on sheet '{}' after CanAddViewToSheet check.".format(new_view_name, new_sheet.Name))
                        failed_views.append(original_view_name + " (Viewport Creation Failed)")
                else:
                    # Check why it cannot be added
                    existing_viewport = None
                    # Attempt to find if view is already on ANY sheet
                    vports_col = FilteredElementCollector(doc).OfClass(Viewport).WhereElementIsNotElementType().ToElements()
                    for vp in vports_col:
                        if vp.ViewId == new_view_id:
                             existing_viewport = vp
                             break
                    reason = "Reason unknown"
                    if existing_viewport is not None:
                        sheet_hosting_view = doc.GetElement(existing_viewport.SheetId)
                        sheet_host_name = "Unknown Sheet"
                        if sheet_hosting_view:
                            try:
                                sheet_host_name = sheet_hosting_view.Name
                            except: pass
                        reason = "View already placed on sheet '{}' (ID: {})".format(sheet_host_name, existing_viewport.SheetId)
                    else:
                        reason = "View Type likely incompatible with Sheet placement"

                    print("# Warning: View '{}' cannot be added to sheet '{}' ({}). Skipping placement.".format(new_view_name, new_sheet.Name, reason))
                    failed_views.append(original_view_name + " (Cannot Add To Sheet)")
            except Exception as place_ex:
                print("# Error placing view '{}' onto sheet '{}'. Error: {}".format(new_view_name, new_sheet.Name, place_ex))
                failed_views.append(original_view_name + " (Placement Error)")

        except Exception as view_proc_ex:
            print("# Error processing view '{}'. Error: {}".format(original_view_name, view_proc_ex))
            failed_views.append(original_view_name + " (General Processing Error)")
            # Continue to the next view

    print("# --- Summary ---")
    print("# Found {} views associated with Level '{}' potentially suitable for processing.".format(len(original_views), target_level_name))
    print("# Attempted to process {} views.".format(processed_view_count))
    print("# Successfully created {} new sheets.".format(created_sheet_count))
    if failed_views:
        print("# Failed operations/views encountered:")
        # Use a set to avoid duplicate failure messages for the same original view
        unique_failures = set(failed_views)
        for failure in sorted(list(unique_failures)): # Sort for consistent output
            print("#   - {}".format(failure))
    else:
        print("# All detected views processed successfully.")

elif not target_level:
    print("# Execution stopped: Target Level '{}' not found.".format(target_level_name))
elif not view_template:
    print("# Execution stopped: View Template '{}' not found.".format(target_template_name))
elif title_block_type_id == ElementId.InvalidElementId:
    print("# Execution stopped: No Title Block Types found in the project.")
else:
    print("# Execution stopped: Unknown initialization error.")