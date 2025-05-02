# Purpose: This script sets transparency overrides in Revit, making all categories in linked files transparent except walls and floors.

﻿# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB
from System import Exception # To catch general exceptions

# --- Main Script ---

# Get the active view
active_view = doc.ActiveView

# Proceed only if there is an active graphical view
if active_view and isinstance(active_view, DB.View):

    # Get Category IDs for Walls and Floors
    wall_cat_id = DB.ElementId(DB.BuiltInCategory.OST_Walls)
    floor_cat_id = DB.ElementId(DB.BuiltInCategory.OST_Floors)

    # Define the opaque override settings (resetting transparency)
    opaque_settings = DB.OverrideGraphicSettings()
    opaque_settings.SetSurfaceTransparency(0) # 0 = fully opaque

    # Collect all Revit Link Instances in the document
    link_instances_collector = DB.FilteredElementCollector(doc).OfClass(DB.RevitLinkInstance)
    link_instances = link_instances_collector.ToElements()

    if not link_instances:
        # print("# No Revit link instances found in the project.") # Optional message
        pass # No links to process
    else:
        processed_links_count = 0
        error_links = []

        # Iterate through each link instance found in the document
        for link_instance in link_instances:
            if not link_instance or not link_instance.IsValidObject:
                continue

            link_instance_id = link_instance.Id

            try:
                # Get the current graphic override settings for this link instance in the active view.
                # This returns null if no instance-specific overrides are set (might be By Host, By Linked View, or Type settings).
                current_settings = active_view.GetLinkOverrides(link_instance_id)

                # Create a new settings object if none exist for the instance,
                # otherwise, we will modify the existing ones.
                if current_settings is None:
                    settings_to_modify = DB.RevitLinkGraphicsSettings()
                    # Ensure the link type isn't set to "By Linked View" or "By Host View" initially
                    # if you create new settings, although setting Custom below handles this.
                else:
                    # If settings exist, modify them directly.
                    settings_to_modify = current_settings

                # Set the display mode to Custom. This is required to apply category-specific overrides.
                settings_to_modify.LinkVisibilityType = DB.RevitLinkGraphicsType.Custom

                # Set the entire link instance to be transparent by default within the custom settings.
                # This acts as the base override for all categories unless explicitly overridden.
                settings_to_modify.SetTransparent(True)
                # Optional: Ensure Halftone is off if it was on previously or by default
                # settings_to_modify.SetHalftone(False)

                # Apply the specific opaque override settings ONLY to the Walls category
                settings_to_modify.SetCategoryOverrides(wall_cat_id, opaque_settings)

                # Apply the specific opaque override settings ONLY to the Floors category
                settings_to_modify.SetCategoryOverrides(floor_cat_id, opaque_settings)

                # Apply the modified graphics settings back to the link instance for the active view.
                active_view.SetLinkOverrides(link_instance_id, settings_to_modify)

                processed_links_count += 1
                # print(f"# Applied custom overrides to link instance ID: {{{{link_instance_id}}}}") # Escaped debug message

            except Exception as e:
                # Store information about links that failed
                link_name = "Unknown"
                try:
                    # Attempt to get the name of the link type for better error reporting
                    link_type = doc.GetElement(link_instance.GetTypeId())
                    if link_type and hasattr(link_type, 'Name'):
                        link_name = link_type.Name
                except:
                    pass # Ignore errors getting the name
                error_links.append("'{{0}}' (ID: {{1}}): {{2}}".format(link_name, link_instance_id.IntegerValue, e))


        # Final status reporting (optional, commented out for clean output as requested)
        # if processed_links_count > 0:
        #     print(f"# Successfully applied transparency overrides to {{{{processed_links_count}}}} link instance(s) in view '{{active_view.Name}}'. Walls and Floors remain opaque.") # Escaped success message
        # elif not link_instances:
        #     # Message handled earlier or no links found
        #     pass
        # else:
        #     # This case means links were found, but none were processed successfully
        #     print("# No link instances were successfully processed.") # Optional message if all failed

        # Report errors if any occurred
        if error_links:
            print("# Errors occurred while processing some links:")
            for error_msg in error_links:
                 print("# - {{}}".format(error_msg)) # Escaped format

else:
    print("# Error: No active graphical view found. Cannot apply link overrides.")