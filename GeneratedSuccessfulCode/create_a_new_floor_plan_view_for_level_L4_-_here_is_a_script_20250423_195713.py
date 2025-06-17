# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewFamilyType,
    ViewFamily,
    ViewPlan,
    ElementId,
    View # Added for checking existing view names
)

# --- Configuration ---
target_level_name = "L4"
new_view_name_base = "Floor Plan - L4" # Desired base name for the new view

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels_collector = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    for level in levels_collector:
        try:
            if level.Name == level_name:
                return level
        except Exception as e:
            print("# Warning: Error accessing level name for ID {0}: {1}".format(level.Id, e))
            continue
    print("# Error: Level named '{0}' not found.".format(level_name))
    return None

def find_first_floor_plan_vft(doc_param):
    """Finds the first available Floor Plan ViewFamilyType."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        try:
            if vft.ViewFamily == ViewFamily.FloorPlan:
                return vft
        except Exception as e:
             print("# Warning: Error accessing ViewFamilyType ID {0}: {1}".format(vft.Id, e))
             continue
    print("# Error: No Floor Plan View Family Type found in the document.")
    return None

def get_unique_view_name(doc_param, base_name):
    """Checks if a view name exists and returns a unique version."""
    existing_view_names = [v.Name for v in FilteredElementCollector(doc_param).OfClass(View).ToElements()]
    final_view_name = base_name
    counter = 1
    while final_view_name in existing_view_names:
        final_view_name = "{0}_{1}".format(base_name, counter)
        counter += 1
    return final_view_name

# --- Main Logic ---

# 1. Find the specified Level
level_element = find_level_by_name(doc, target_level_name)

# 2. Find the first available Floor Plan ViewFamilyType
floor_plan_vft = find_first_floor_plan_vft(doc)

# 3. Proceed only if level and VFT are found
if level_element and floor_plan_vft:
    level_id = level_element.Id
    floor_plan_vft_id = floor_plan_vft.Id
    new_view_plan = None
    try:
        # Create the new floor plan view
        # The transaction is handled by the external C# code
        new_view_plan = ViewPlan.Create(doc, floor_plan_vft_id, level_id)

        # Set the name of the new view, ensuring uniqueness
        unique_name = get_unique_view_name(doc, new_view_name_base)
        if new_view_plan.Name != unique_name: # Only rename if necessary or different from default
            new_view_plan.Name = unique_name

        print("# Successfully created floor plan view '{0}' for level '{1}'.".format(new_view_plan.Name, target_level_name))

        # Note: Setting the active view (uidoc.ActiveView = new_view_plan)
        # is omitted as it's often problematic within transactions and not requested.
        # Use uidoc.RequestViewChange(new_view_plan) outside the transaction if needed.

    except Exception as create_ex:
        # Print error message instead of TaskDialog
        print("# Error creating floor plan view for level '{0}'. Error: {1}".format(target_level_name, create_ex))
        # No transaction rollback needed here, handled externally

else:
    # Print messages about which prerequisite failed
    if not level_element:
        # Message already printed by find_level_by_name
        pass
    if not floor_plan_vft:
        # Message already printed by find_first_floor_plan_vft
        pass
    print("# View creation aborted due to missing prerequisites.")
    # No transaction rollback needed here, handled externally