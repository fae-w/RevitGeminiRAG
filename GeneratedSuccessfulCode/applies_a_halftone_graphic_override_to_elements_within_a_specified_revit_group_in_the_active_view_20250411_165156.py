# Purpose: This script applies a halftone graphic override to elements within a specified Revit group in the active view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Group,
    ElementId,
    OverrideGraphicSettings,
    View
)

# --- Configuration ---
target_group_name = "Core Toilet Layout"

# --- Find the specific group by name ---
group_collector = FilteredElementCollector(doc).OfClass(Group).WhereElementIsNotElementType()
target_group = None
for group in group_collector:
    # Group name can be accessed via its type or directly if instance name matches type name implicitly
    group_type = doc.GetElement(group.GetTypeId())
    group_instance_name = group.Name # Instance name (might be empty or number)
    group_type_name = ""
    if group_type:
        group_type_name = group_type.Name

    # Check both instance name and type name, preferring type name as it's more stable
    if group_type_name == target_group_name or group_instance_name == target_group_name:
        target_group = group
        # print("# Found group '{{}}' with ID: {{}}".format(target_group_name, group.Id)) # Debug
        break # Stop after finding the first match

# --- Apply overrides if group found ---
if target_group is None:
    print("# Error: Group named '{{}}' not found in the document.".format(target_group_name))
else:
    member_ids = target_group.GetMemberIds()

    if not member_ids or member_ids.Count == 0:
        print("# Warning: Group '{{}}' found but contains no members.".format(target_group_name))
    else:
        active_view = doc.ActiveView
        if active_view is None or not active_view.IsValidObject:
            print("# Error: No active view found or the active view is invalid.")
        elif not active_view.AreGraphicsOverridesAllowed():
            print("# Error: Active view '{{}}' (Type: {{}}) does not support element overrides.".format(active_view.Name, active_view.ViewType))
        else:
            # Define the graphic overrides (set halftone to True)
            override_settings = OverrideGraphicSettings()
            override_settings.SetHalftone(True)

            # Apply overrides to each member of the group in the active view
            elements_overridden_count = 0
            elements_failed_count = 0
            member_ids_list = List[ElementId](member_ids) # Convert ICollection to List for easier handling if needed

            for member_id in member_ids_list:
                try:
                    # Check if element is visible in the view before applying override (optional but good practice)
                    # Getting element might fail if purged or corrupted
                    element = doc.GetElement(member_id)
                    if element is None:
                         # print("# Skipping ElementId {{}} - Element not found.".format(member_id)) # Debug
                         elements_failed_count += 1
                         continue

                    # Check if element is hidden in the view (applying override might not be useful visually)
                    # if active_view.IsElementHidden(member_id):
                    #     # print("# Skipping ElementId {{}} - Element is hidden in the active view.".format(member_id)) # Debug
                    #     continue # Skip hidden elements

                    active_view.SetElementOverrides(member_id, override_settings)
                    elements_overridden_count += 1
                except Exception as ex:
                    # print("# Error applying override to element ID {{}}: {{}}".format(member_id, ex)) # Debug
                    elements_failed_count += 1

            print("# Applied halftone override to {{}} elements in group '{{}}' in view '{{}}'.".format(elements_overridden_count, target_group_name, active_view.Name))
            if elements_failed_count > 0:
                 print("# Failed to apply overrides to {{}} elements (might be hidden, deleted, or unsupported).".format(elements_failed_count))

# Note: This script applies overrides directly to elements, not via a persistent ParameterFilterElement,
# as filtering elements based purely on group membership is not directly supported by standard filter rules.