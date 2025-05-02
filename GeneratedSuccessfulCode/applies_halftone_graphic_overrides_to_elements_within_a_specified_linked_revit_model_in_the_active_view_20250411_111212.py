# Purpose: This script applies halftone graphic overrides to elements within a specified linked Revit model in the active view.

# Purpose: This script applies halftone overrides to elements from a specific linked Revit model in the active view.

﻿# Import necessary classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkInstance,
    ElementId,
    OverrideGraphicSettings,
    View,
    RevitLinkType
)

# Target linked model filename (case-insensitive comparison might be safer)
target_link_filename = "ARCH_LINK.rvt"

# Get the active view
active_view = doc.ActiveView
if not active_view:
    print("# Error: No active view found.")
else:
    # Find the RevitLinkInstance corresponding to the target filename
    target_link_instance_id = ElementId.InvalidElementId
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()

    found_link = False
    for link_instance in link_instances:
        if not link_instance.IsValidObject:
            continue
        try:
            # Get the RevitLinkType associated with this instance
            link_type_id = link_instance.GetTypeId()
            if link_type_id != ElementId.InvalidElementId:
                link_type = doc.GetElement(link_type_id)
                if isinstance(link_type, RevitLinkType):
                    # Check if the link type name matches the target filename (often includes it)
                    # Using case-insensitive comparison for robustness
                    if target_link_filename.lower() in link_type.Name.lower():
                        # Found the link instance
                        target_link_instance_id = link_instance.Id
                        found_link = True
                        # print(f"# Found link instance: {link_instance.Id} for type: {link_type.Name}") # Escaped debug
                        break # Stop searching once found
        except Exception as e:
            # print(f"# Error checking link instance {link_instance.Id}: {e}") # Escaped debug
            pass # Continue searching other links

    if not found_link:
        print("# Error: Revit link instance for '{}' not found in the document.".format(target_link_filename))
    else:
        # Create halftone override settings
        override_settings = OverrideGraphicSettings()
        override_settings.SetHalftone(True)

        # Collect elements from the specified link instance that are visible in the active view
        # Note: This collects elements DEFINED in the link, not just the instance itself.
        try:
            collector = FilteredElementCollector(doc, active_view.Id, target_link_instance_id)
            # Exclude element types just in case, usually not strictly necessary for overrides
            elements_in_link_in_view = collector.WhereElementIsNotElementType().ToElementIds()

            applied_count = 0
            if elements_in_link_in_view and elements_in_link_in_view.Count > 0:
                # Apply overrides to each element from the link visible in the view
                for element_id in elements_in_link_in_view:
                    try:
                        active_view.SetElementOverrides(element_id, override_settings)
                        applied_count += 1
                    except Exception as e:
                        # Might fail for certain element types or if the element is not overridable
                        # print(f"# Warning: Could not apply halftone override to element {element_id} from link. Error: {e}") # Escaped debug
                        pass
                # print("# Applied halftone override to {} elements from link '{}' in view '{}'.".format(applied_count, target_link_filename, active_view.Name))
            else:
                print("# No elements from link '{}' found or visible in the active view '{}'.".format(target_link_filename, active_view.Name))

        except Exception as ex:
             print("# Error collecting or applying overrides for link elements: {}".format(ex))