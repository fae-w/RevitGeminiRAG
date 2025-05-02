# Purpose: This script sets the underlay base level and orientation for a specified Revit view.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewPlan,
    ElementId,
    UnderlayOrientation,
    View,
    BuiltInParameter
)

# --- Configuration ---
target_view_name = "L3 Floor Plan"
underlay_base_level_name = "L2" # Interpret 'L2 Reflected Ceiling Plan' as referring to the 'L2' level
target_orientation = UnderlayOrientation.LookingDown # 'Look Down' corresponds to LookingDown enum

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels = FilteredElementCollector(doc_param).OfClass(Level).WhereElementIsNotElementType().ToElements()
    for level in levels:
        try:
            # Using Name property is generally reliable
            if level.Name == level_name:
                return level
        except Exception as e:
            print("# Warning: Error accessing level name for ID {{}}: {{}}".format(level.Id, e))
            continue
    print("# Error: Level named '{{}}' not found.".format(level_name))
    return None

def find_view_plan_by_name(doc_param, view_name):
    """Finds a ViewPlan element by its exact name."""
    views = FilteredElementCollector(doc_param).OfClass(ViewPlan).WhereElementIsNotElementType().ToElements()
    for v in views:
        try:
            # Using Name property
            if v.Name == view_name:
                # Ensure it's specifically a ViewPlan (redundant due to collector filter but safe)
                if isinstance(v, ViewPlan):
                    return v
                else:
                    print("# Info: View '{{}}' found but it is not a ViewPlan (Type: {{}}).".format(view_name, v.GetType().Name))
                    return None
        except Exception as e:
            print("# Warning: Error accessing view name for ID {{}}: {{}}".format(v.Id, e))
            continue
    print("# Error: ViewPlan named '{{}}' not found.".format(view_name))
    return None

# --- Main Logic ---

# 1. Find the target ViewPlan
target_view_plan = find_view_plan_by_name(doc, target_view_name)

# 2. Find the target underlay base Level
underlay_level = find_level_by_name(doc, underlay_base_level_name)

# 3. Proceed only if both view and level are found
if target_view_plan and underlay_level:
    underlay_level_id = underlay_level.Id

    # Check if the view supports underlay settings (most ViewPlans should)
    # You could check if GetUnderlayBaseLevel method exists, but try/except is often easier in Python
    try:
        # Get current settings for comparison/logging if needed (optional)
        # current_base_id = target_view_plan.GetUnderlayBaseLevel()
        # current_orientation = target_view_plan.GetUnderlayOrientation()
        # print(f"# Current Underlay: Base={current_base_id}, Orientation={current_orientation}")

        # Set the Underlay Base Level
        # Using SetUnderlayBaseLevel sets the base and implies the top is the next level up.
        # Use SetUnderlayRange(baseId, topId) if explicit top control is needed.
        target_view_plan.SetUnderlayBaseLevel(underlay_level_id)
        print("# Successfully set Underlay Base Level for view '{{}}' to Level '{{}}' (ID: {{}}).".format(target_view_name, underlay_base_level_name, underlay_level_id))

        # Set the Underlay Orientation
        target_view_plan.SetUnderlayOrientation(target_orientation)
        print("# Successfully set Underlay Orientation for view '{{}}' to '{{}}'.".format(target_view_name, target_orientation.ToString()))

        print("# Underlay settings updated for view '{}'.".format(target_view_name))

    except AttributeError as ae:
         print("# Error: The view '{{}}' (Type: {{}}) might not support underlay settings directly via these methods. Error: {{}}".format(target_view_name, target_view_plan.GetType().Name, ae))
    except Exception as ex:
        print("# Error applying underlay settings to view '{{}}'. Exception: {{}}".format(target_view_name, ex))

else:
    # Print messages about which prerequisite failed
    if not target_view_plan:
        # Error message already printed by find_view_plan_by_name
        pass
    if not underlay_level:
        # Error message already printed by find_level_by_name
        pass
    print("# Failed to update underlay settings due to missing view or level.")

# Optional: Check active view matches target view - informational only
active_view = uidoc.ActiveView
if active_view and active_view.Name != target_view_name:
    print("# Info: The active view ('{}') is different from the target view ('{}'). Changes were applied to the target view.".format(active_view.Name, target_view_name))
elif not active_view:
    print("# Info: Could not determine the active view.")