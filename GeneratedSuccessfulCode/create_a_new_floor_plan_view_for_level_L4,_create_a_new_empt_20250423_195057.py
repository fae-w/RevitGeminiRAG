# Import necessary classes
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

# --- Configuration ---
target_level_name = "L4"
new_view_name = "Level four plan"
new_sheet_number_base = "A201" # Base sheet number, will increment if exists
new_sheet_name_base = "Level Four Plan Sheet"

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels_collector = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    for level in levels_collector:
        if level.Name == level_name:
            return level
    print("# Error: Level named '{}' not found.".format(level_name))
    return None

def find_first_floor_plan_vft(doc_param):
    """Finds the first available Floor Plan ViewFamilyType."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        if vft.ViewFamily == ViewType.FloorPlan:
            return vft
    print("# Error: No Floor Plan View Family Type found in the document.")
    return None

def find_first_title_block_type(doc_param):
    """Finds the first available Title Block Type."""
    collector = FilteredElementCollector(doc_param).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType()
    first_title_block_type = collector.FirstElement()
    if first_title_block_type:
        return first_title_block_type
    print("# Warning: No Title Block types found in the project. Sheet will be created without a title block.")
    return None

# --- Main Logic ---

# 1. Find the target Level
target_level = find_level_by_name(doc, target_level_name)
if not target_level:
    print("# Aborting: Target level '{}' not found.".format(target_level_name))
else:
    target_level_id = target_level.Id

    # 2. Find a suitable ViewFamilyType for Floor Plans
    floor_plan_vft = find_first_floor_plan_vft(doc)
    if not floor_plan_vft:
        print("# Aborting: Could not find a suitable Floor Plan View Family Type.")
    else:
        floor_plan_vft_id = floor_plan_vft.Id

        # 3. Create the Floor Plan view
        new_view_plan = None
        try:
            # Check if a view with the target name already exists for this level
            existing_view = None
            all_views = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()
            for view in all_views:
                if view.Name == new_view_name and view.GenLevel and view.GenLevel.Id == target_level_id:
                    existing_view = view
                    print("# Warning: A view named '{}' for level '{}' already exists. Using existing view.".format(new_view_name, target_level_name))
                    break

            if existing_view:
                 new_view_plan = existing_view
            else:
                 new_view_plan = ViewPlan.Create(doc, floor_plan_vft_id, target_level_id)
                 # Rename the view immediately after creation
                 try:
                     new_view_plan.Name = new_view_name
                     # print("# Created and renamed new floor plan view: '{}' (ID: {})".format(new_view_name, new_view_plan.Id)) # Optional Debug
                 except Exception as name_ex:
                     # Attempt a default name if the desired name fails
                     try:
                         default_name = target_level_name + " Plan"
                         new_view_plan.Name = default_name
                         print("# Warning: Could not rename view to '{}'. Renamed to default '{}'. Error: {}".format(new_view_name, default_name, name_ex))
                     except Exception as default_name_ex:
                          print("# Error: Could not create or rename the new floor plan view. Error: {}".format(default_name_ex))
                          new_view_plan = None # Ensure it's None if renaming failed critically


        except Exception as create_ex:
            print("# Error creating floor plan view: {}".format(create_ex))
            new_view_plan = None # Ensure it's None if creation failed

        if new_view_plan:
            # 4. Find a Title Block Type (can be None)
            title_block_type = find_first_title_block_type(doc)
            title_block_type_id = title_block_type.Id if title_block_type else ElementId.InvalidElementId

            # 5. Create a new Sheet
            new_sheet = None
            try:
                new_sheet = ViewSheet.Create(doc, title_block_type_id)
                if new_sheet:
                    # Try to set a unique sheet number and name
                    sheet_num = new_sheet_number_base
                    sheet_name = new_sheet_name_base
                    counter = 0
                    max_attempts = 100 # Prevent infinite loop
                    existing_sheet_numbers = [s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()]

                    # Ensure base number doesn't exist
                    base_num_int = int(new_sheet_number_base[1:]) # Assuming format like A###
                    prefix = new_sheet_number_base[0]

                    while sheet_num in existing_sheet_numbers and counter < max_attempts:
                         counter += 1
                         sheet_num = prefix + str(base_num_int + counter)

                    if counter < max_attempts:
                         try:
                             new_sheet.SheetNumber = sheet_num
                             new_sheet.Name = sheet_name
                             # print("# Created new sheet: {} - {} (ID: {})".format(sheet_num, sheet_name, new_sheet.Id)) # Optional Debug
                         except Exception as set_name_num_ex:
                             print("# Warning: Could not set sheet number/name for the new sheet. Error: {}".format(set_name_num_ex))
                    else:
                         print("# Warning: Could not find an unused sheet number starting from {} after {} attempts. Sheet created with default number.".format(new_sheet_number_base, max_attempts))
                else:
                    print("# Error: ViewSheet.Create returned None.")

            except Exception as sheet_ex:
                print("# Error creating sheet: {}".format(sheet_ex))

            if new_sheet and new_view_plan:
                # 6. Place the View on the Sheet
                try:
                    # Check if the view can be added (e.g., not already on max sheets)
                    if Viewport.CanAddViewToSheet(doc, new_sheet.Id, new_view_plan.Id):
                         # Calculate center point for placement (approximate)
                         sheet_bb = new_sheet.get_BoundingBox(None) # Pass None for view to get sheet bounds
                         center_point = XYZ(0, 0, 0) # Default if BB fails
                         if sheet_bb and sheet_bb.Min and sheet_bb.Max:
                              center_point = (sheet_bb.Min + sheet_bb.Max) / 2.0
                         else:
                              # Fallback placement if bounding box fails - use a reasonable default
                              # Attempt to get title block location if available
                              tb_instances = FilteredElementCollector(doc, new_sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType().ToElements()
                              if tb_instances:
                                  tb_bb = tb_instances[0].get_BoundingBox(new_sheet)
                                  if tb_bb and tb_bb.Min and tb_bb.Max:
                                       center_point = (tb_bb.Min + tb_bb.Max) / 2.0
                                       # print("# Info: Using title block center for placement.") # Optional Debug
                                  else:
                                       center_point = XYZ(1.0, 1.0, 0) # Arbitrary point if TB BB fails
                                       print("# Warning: Could not get sheet or title block bounding box. Placing viewport near (1,1).")
                              else:
                                   center_point = XYZ(1.0, 1.0, 0) # Arbitrary point if no TB and sheet BB fails
                                   print("# Warning: Could not get sheet bounding box and no title block found. Placing viewport near (1,1).")


                         # Create the viewport
                         viewport = Viewport.Create(doc, new_sheet.Id, new_view_plan.Id, center_point)
                         if viewport:
                             print("# Successfully placed view '{}' on sheet '{}'.".format(new_view_plan.Name, new_sheet.SheetNumber))
                         else:
                             print("# Error: Viewport.Create returned None.")
                    else:
                        # Check why it cannot be added
                        status = new_view_plan.GetPlacementOnSheetStatus()
                        print("# Error: View '{}' cannot be added to sheet '{}'. View Placement Status: {}".format(new_view_plan.Name, new_sheet.SheetNumber, status))

                except Exception as vp_ex:
                    print("# Error placing view on sheet: {}".format(vp_ex))
            elif not new_sheet:
                 print("# Aborting placement: Sheet creation failed.")
            elif not new_view_plan:
                 print("# Aborting placement: View creation/renaming failed.")
        # else: view creation already printed error
    # else: VFT finding already printed error
# else: Level finding already printed error