# Purpose: This script applies a halftone graphic override to elements from specific Revit links within the active view.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkInstance,
    RevitLinkType,
    ElementId,
    OverrideGraphicSettings,
    View,
    BuiltInParameter # Although likely using Type Name, keeping for potential future parameter use
)
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List # Though not strictly needed for this approach, good practice

# --- Configuration ---
substring_to_find = "_ARCH" # Case-insensitive search for this string in the Link Type name

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not active_view.IsValidObject:
    print("# Error: No active view found or active view is invalid.")
else:
    if not active_view.AreGraphicsOverridesAllowed():
        print("# Error: The active view '{}' (Type: {}) does not support graphic overrides.".format(active_view.Name, active_view.ViewType))
    else:
        # --- Prepare Override Settings ---
        override_settings = OverrideGraphicSettings()
        override_settings.SetHalftone(True)

        # --- Find Relevant Link Instances ---
        link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()

        found_matching_links = False
        total_elements_overridden = 0

        for link_instance in link_instances:
            if not link_instance.IsValidObject:
                continue

            try:
                # Get the RevitLinkType associated with this instance
                link_type_id = link_instance.GetTypeId()
                if link_type_id != ElementId.InvalidElementId:
                    link_type = doc.GetElement(link_type_id)
                    if isinstance(link_type, RevitLinkType):
                        # Check if the Link Type name contains the target substring (case-insensitive)
                        if substring_to_find.lower() in link_type.Name.lower():
                            found_matching_links = True
                            link_instance_id = link_instance.Id
                            link_type_name = link_type.Name
                            # print("# Found matching link instance: {} (Type: {})".format(link_instance_id, link_type_name)) # Debug

                            # --- Collect and Override Elements from this Link in the Active View ---
                            try:
                                # Collector for elements defined IN the link document, visible IN the active view through this specific instance
                                collector = FilteredElementCollector(doc, active_view.Id, link_instance_id)
                                # Exclude element types to avoid potential issues/warnings when applying overrides
                                elements_in_link_in_view = collector.WhereElementIsNotElementType().ToElementIds()

                                applied_count_for_link = 0
                                if elements_in_link_in_view and elements_in_link_in_view.Count > 0:
                                    for element_id in elements_in_link_in_view:
                                        try:
                                            active_view.SetElementOverrides(element_id, override_settings)
                                            applied_count_for_link += 1
                                        except Exception as override_ex:
                                            # Silently ignore elements that cannot be overridden (e.g., some non-graphical elements)
                                            # print("# Warning: Could not apply halftone to element {} from link '{}'. Error: {}".format(element_id, link_type_name, override_ex)) # Debug
                                            pass
                                    total_elements_overridden += applied_count_for_link
                                    # print("# Applied halftone override to {} elements from link '{}' in view '{}'.".format(applied_count_for_link, link_type_name, active_view.Name)) # Debug
                                else:
                                     pass # print("# No elements from link '{}' found or visible in the active view '{}'.".format(link_type_name, active_view.Name)) # Debug

                            except Exception as collect_ex:
                                print("# Error collecting or applying overrides for elements in link '{}': {}".format(link_type_name, collect_ex))

            except Exception as instance_ex:
                print("# Error processing link instance {}: {}".format(link_instance.Id, instance_ex))

        if not found_matching_links:
            print("# No Revit link instances found whose type name contains '{}'.".format(substring_to_find))
        # elif total_elements_overridden > 0: # Optional summary print
            # print("# Successfully applied halftone overrides to a total of {} elements from matching links in view '{}'.".format(total_elements_overridden, active_view.Name))