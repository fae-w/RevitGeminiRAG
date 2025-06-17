# Purpose: This script creates a floor plan view for the lowest level and places it on a new sheet.

# Purpose: This script creates a new floor plan view of the lowest level in the model and places it on a newly created sheet.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewFamilyType,
    ViewPlan,
    ViewSheet,
    Viewport,
    ElementId,
    BuiltInCategory,
    ViewType,
    XYZ,
    BoundingBoxXYZ,
    BuiltInParameter
)

# 1. Find the lowest level
levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
if not levels:
    print("# Error: No levels found in the document.")
else:
    # Sort levels by elevation
    sorted_levels = sorted(levels, key=lambda l: l.Elevation)
    lowest_level = sorted_levels[0]
    lowest_level_id = lowest_level.Id
    lowest_level_name = lowest_level.Name
    # print(f"# Found lowest level: {lowest_level_name} (ID: {lowest_level_id})") # Escaped

    # 2. Find a suitable ViewFamilyType for Floor Plans
    floor_plan_vft_id = ElementId.InvalidElementId
    vfts = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        # Check if it's a FloorPlan ViewType
        if vft.ViewFamily == ViewType.FloorPlan:
            floor_plan_vft_id = vft.Id
            break # Use the first one found

    if floor_plan_vft_id == ElementId.InvalidElementId:
        print("# Error: No Floor Plan View Family Type found in the document.")
    else:
        # 3. Create the Floor Plan view
        new_view_plan = None
        try:
            # Check if a view for this level already exists with a common naming convention
            existing_view = None
            potential_view_name = lowest_level_name # A common default name
            all_views = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()
            for view in all_views:
                if view.Name == potential_view_name and view.GenLevel.Id == lowest_level_id:
                     existing_view = view
                     # print(f"# Found existing floor plan named '{potential_view_name}' for level '{lowest_level_name}'. Using existing view.") # Escaped
                     break

            if existing_view:
                 new_view_plan = existing_view
            else:
                 # Create the new view plan if no suitable existing one is found
                 new_view_plan = ViewPlan.Create(doc, floor_plan_vft_id, lowest_level_id)
                 # Optionally rename the view
                 try:
                     new_view_name = "Floor Plan - " + lowest_level_name
                     new_view_plan.Name = new_view_name
                     # print(f"# Created new floor plan: {new_view_name} (ID: {new_view_plan.Id})") # Escaped
                 except Exception as name_ex:
                     print("# Warning: Could not rename the new floor plan view. Error: {0}".format(name_ex))

        except Exception as create_ex:
            print("# Error creating floor plan view: {0}".format(create_ex))

        if new_view_plan:
            # 4. Find a Title Block Type
            title_block_type_id = ElementId.InvalidElementId
            collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
            first_title_block_type = collector.FirstElement()
            if first_title_block_type:
                title_block_type_id = first_title_block_type.Id
                # print(f"# Found title block type: {first_title_block_type.Name} (ID: {title_block_type_id})") # Escaped
            else:
                print("# Error: No Title Block types found in the project. Cannot create sheet.")

            if title_block_type_id != ElementId.InvalidElementId:
                # 5. Create a new Sheet
                new_sheet = None
                try:
                    new_sheet = ViewSheet.Create(doc, title_block_type_id)
                    if new_sheet:
                        # Try to set a unique sheet number and name
                        sheet_num = "A101" # Default start
                        sheet_name = lowest_level_name + " Plan"
                        counter = 1
                        max_attempts = 100 # Prevent infinite loop
                        existing_sheet_numbers = [s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()]

                        while sheet_num in existing_sheet_numbers and counter < max_attempts:
                             counter += 1
                             sheet_num = "A" + str(100 + counter)

                        if counter < max_attempts:
                             try:
                                 new_sheet.SheetNumber = sheet_num
                                 new_sheet.Name = sheet_name
                                 # print(f"# Created new sheet: {sheet_num} - {sheet_name} (ID: {new_sheet.Id})") # Escaped
                             except Exception as set_name_num_ex:
                                 print("# Warning: Could not set sheet number/name. Error: {0}".format(set_name_num_ex))
                        else:
                             print("# Warning: Could not find an unused sheet number after {0} attempts. Sheet created with default number.".format(max_attempts))
                    else:
                        print("# Error: ViewSheet.Create returned None.")

                except Exception as sheet_ex:
                    print("# Error creating sheet: {0}".format(sheet_ex))

                if new_sheet and new_view_plan:
                    # 6. Place the View on the Sheet
                    try:
                        # Check if the view can be added
                        if Viewport.CanAddViewToSheet(doc, new_sheet.Id, new_view_plan.Id):
                             # Calculate center point for placement (approximate)
                             sheet_bb = new_sheet.get_BoundingBox(None) # Pass None for view to get sheet bounds
                             if sheet_bb and sheet_bb.Min and sheet_bb.Max:
                                  center_point = (sheet_bb.Min + sheet_bb.Max) / 2.0
                             else:
                                  # Fallback placement if bounding box fails
                                  center_point = XYZ(1, 1, 0) # Arbitrary non-zero point near origin
                                  print("# Warning: Could not get sheet bounding box. Placing viewport at default location.")

                             # Create the viewport
                             viewport = Viewport.Create(doc, new_sheet.Id, new_view_plan.Id, center_point)
                             if viewport:
                                 # print(f"# Successfully placed view '{new_view_plan.Name}' on sheet '{new_sheet.SheetNumber}'.") # Escaped
                                 pass # Success
                             else:
                                 print("# Error: Viewport.Create returned None.")
                        else:
                            print("# Error: View '{0}' cannot be added to sheet '{1}'. It might already be on a sheet.".format(new_view_plan.Name, new_sheet.SheetNumber))
                    except Exception as vp_ex:
                        print("# Error placing view on sheet: {0}".format(vp_ex))