# Purpose: This script applies transparency overrides to specific Revit link instances within the active view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for List and Exceptions
from System import Exception as SysException
from System.Collections.Generic import List # Might be needed if handling multiple IDs

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkInstance,
    RevitLinkType,
    OverrideGraphicSettings,
    View,
    ElementId
)

# --- Configuration ---
# IMPORTANT: RevitLinkType.Name usually doesn't include the '.rvt' extension.
# Adjust this name to match the Link Type name shown in Revit's Manage Links dialog.
target_link_type_name = "STRUCT_Main" # Example: Assuming the TYPE name is this. Adjust if needed.
# Original request used "STRUCT_Main.rvt", which is usually the file name, not the Type name.
# Check Manage Links -> Revit tab -> 'Name' column for the correct Type Name.

transparency_value = 75 # Percentage (0-100)

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found, or the active view is a template.")
    # Cannot proceed without a valid view
    active_view = None

# Proceed only if view is valid
if active_view:
    # --- Find the Link Instances by Type Name ---
    link_instance_ids_to_override = []
    link_instances_collector = FilteredElementCollector(doc).OfClass(RevitLinkInstance)
    found_link_type = False

    for link_instance in link_instances_collector:
        if link_instance and link_instance.IsValidObject:
            try:
                # Get the ElementId of the RevitLinkType associated with this instance
                link_type_id = link_instance.GetTypeId()
                if link_type_id != ElementId.InvalidElementId:
                    link_type = doc.GetElement(link_type_id)
                    if isinstance(link_type, RevitLinkType):
                        # Compare the name of the link type
                        # Using OrdinalIgnoreCase for robustness against case variations
                        if link_type.Name.Equals(target_link_type_name, System.StringComparison.OrdinalIgnoreCase):
                            link_instance_ids_to_override.append(link_instance.Id)
                            found_link_type = True
                            # print(f"# Found matching link instance: ID {{{{{{{{link_instance.Id}}}}}}}}") # Escaped debug message
            except SysException as find_err:
                print("# Error processing a link instance (ID: {{}}): {{}}".format(link_instance.Id, find_err))

    if not found_link_type:
        print("# Warning: No Revit link instances found with the Type Name '{}'. Check the name in Manage Links.".format(target_link_type_name))
    elif not link_instance_ids_to_override:
         print("# Found link type '{}', but no valid instances to override.".format(target_link_type_name))


    # --- Apply Overrides to Found Link Instances ---
    if link_instance_ids_to_override:
        # --- Define Override Settings ---
        override_settings = OverrideGraphicSettings()
        apply_overrides = True
        try:
            # Set the surface transparency for the link instance element itself
            override_settings.SetSurfaceTransparency(transparency_value)
            # You could add other overrides here if needed (e.g., Halftone, Color, etc.)
            # override_settings.SetHalftone(True)
        except SysException as override_def_err:
            print("# Error defining override graphic settings: {{}}".format(override_def_err))
            apply_overrides = False # Don't try to apply invalid overrides


        if apply_overrides:
            applied_count = 0
            error_count = 0
            # Apply the overrides to each found link instance in the active view
            for link_instance_id in link_instance_ids_to_override:
                try:
                    # Use SetElementOverrides to apply overrides directly to the link instance element
                    active_view.SetElementOverrides(link_instance_id, override_settings)
                    applied_count += 1
                except SysException as apply_err:
                    print("# Error applying overrides to link instance ID {{}} in view '{{}}': {{}}".format(link_instance_id, active_view.Name, apply_err))
                    error_count += 1

            if applied_count > 0:
                 print("# Applied transparency override ({{}}%) to {{}} instance(s) of link type '{{}}' in view '{{}}'.".format(transparency_value, applied_count, target_link_type_name, active_view.Name))
            if error_count > 0:
                 print("# Failed to apply overrides to {{}} instance(s).".format(error_count))

# Note: This script applies overrides directly to the link *instances* in the *active view*.
# It does not create a named 'Filter' element in the Revit Filters dialog.
# Creating a standard ParameterFilterElement to target elements *only* from a specific link is generally not possible
# without relying on other parameters (like Workset or Shared Parameters) set within the linked model elements.