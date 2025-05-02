# Purpose: This script applies a halftone graphic override to tags associated with elements on a specified workset in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List, HashSet

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    WorksetTable,
    WorksetKind,
    FilteredWorksetCollector,
    Workset,
    WorksetId,
    ElementId,
    IndependentTag,
    OverrideGraphicSettings,
    View,
    ElementWorksetFilter,
    RevitLinkInstance # To potentially check linked elements if needed, though GetTaggedLocalElementId usually handles this
)

# --- Configuration ---
target_workset_name = "Linked Models"

# --- Get Active View ---
active_view = doc.ActiveView
if active_view is None or not active_view.IsValidObject:
    print("# Error: No active view found or the active view is invalid.")
    # Stop processing if no valid active view
    active_view = None
elif not active_view.AreGraphicsOverridesAllowed():
     print("# Error: View '{}' (Type: {}) does not support element overrides.".format(active_view.Name, active_view.ViewType))
     # Stop processing if view doesn't support overrides
     active_view = None

# Proceed only if the view is valid and supports overrides
target_workset_id = None
if active_view:
    # --- Check if Worksharing is Enabled ---
    if not doc.IsWorkshared:
        print("# Error: Worksharing is not enabled in this project.")
        active_view = None # Stop processing
    else:
        # --- Find the Target Workset ---
        workset_table = doc.GetWorksetTable()
        workset_collector = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset)
        found_workset = None
        for ws in workset_collector:
            if ws.Name == target_workset_name:
                found_workset = ws
                break

        if found_workset is None:
            print("# Error: Workset named '{}' not found.".format(target_workset_name))
            active_view = None # Stop processing
        else:
            target_workset_id = found_workset.Id
            # print("# Debug: Found workset '{}' with ID: {}".format(target_workset_name, target_workset_id))

# Proceed only if view is valid and workset was found
if active_view and target_workset_id:

    # --- Collect Element IDs on the Target Workset ---
    # Note: ElementWorksetFilter might not find elements *within* links directly.
    # We rely on the Tag's TaggedElementId pointing to the correct element representation in the host.
    workset_filter = ElementWorksetFilter(target_workset_id, False) # False = only elements directly in this workset
    elements_on_workset_collector = FilteredElementCollector(doc).WherePasses(workset_filter).WhereElementIsNotElementType()
    elements_on_workset_ids = HashSet[ElementId](elements_on_workset_collector.ToElementIds())

    # Also consider elements within Revit Links that are placed on this workset
    link_instances_on_workset = FilteredElementCollector(doc).OfClass(RevitLinkInstance).WherePasses(workset_filter).ToElements()
    for link_instance in link_instances_on_workset:
         # Add the link instance ID itself, as tags might sometimes target the instance? (Less common)
         # elements_on_workset_ids.Add(link_instance.Id) # Usually tags point *through* the link
         pass # Primarily relying on GetTaggedLocalElementId resolving correctly

    if elements_on_workset_ids.Count == 0 and len(link_instances_on_workset) == 0:
         print("# Warning: No elements (excluding types and potentially elements inside links) found directly on workset '{}'. Tags might not be found.".format(target_workset_name))

    # --- Collect Tags in the Active View ---
    tag_collector = FilteredElementCollector(doc, active_view.Id).OfClass(IndependentTag).WhereElementIsNotElementType()
    tags_in_view = list(tag_collector)

    if not tags_in_view:
        print("# No tags found in the active view '{}'.".format(active_view.Name))
    else:
        # --- Define Halftone Override ---
        override_settings = OverrideGraphicSettings()
        override_settings.SetHalftone(True)

        # --- Iterate Through Tags and Apply Overrides ---
        count_halftoned = 0
        skipped_unlinked = 0
        error_count = 0

        for tag in tags_in_view:
            try:
                # Get the element the tag is attached to.
                # GetTaggedLocalElementId() attempts to resolve the ID in the context of the current document,
                # even if the tagged element is in a link.
                tagged_element_id = tag.GetTaggedLocalElementId()

                # Check if the tagged element ID is valid and exists in our set of workset elements
                if tagged_element_id is not None and tagged_element_id != ElementId.InvalidElementId:
                    if tagged_element_id in elements_on_workset_ids:
                        # Apply the override to the tag itself
                        active_view.SetElementOverrides(tag.Id, override_settings)
                        count_halftoned += 1
                    # else: # Debugging if needed
                    #     # tagged_elem = doc.GetElement(tagged_element_id)
                    #     # if tagged_elem:
                    #     #     elem_workset_id = tagged_elem.WorksetId
                    #     #     print("# Debug: Tag {} targets Elem {} on Workset {}".format(tag.Id, tagged_element_id, elem_workset_id))
                    #     # else:
                    #     #     print("# Debug: Tag {} targets Elem {} which was not found in doc".format(tag.Id, tagged_element_id))
                    pass

                # Handle cases where the tag might be associated with multiple elements (less common for IndependentTag)
                # or uses GetTaggedElementIds() which returns LinkElementIds for linked elements.
                # This example focuses on GetTaggedLocalElementId for simplicity.

                elif hasattr(tag, 'GetTaggedElementIds'): # Check if method exists
                     link_elem_ids = tag.GetTaggedElementIds()
                     found_match_in_link = False
                     if link_elem_ids and link_elem_ids.Count > 0:
                          for link_elem_id in link_elem_ids:
                                linked_instance = doc.GetElement(link_elem_id.LinkInstanceId)
                                if linked_instance and linked_instance.Id in elements_on_workset_ids:
                                     # If the *link instance itself* is on the target workset
                                     active_view.SetElementOverrides(tag.Id, override_settings)
                                     count_halftoned += 1
                                     found_match_in_link = True
                                     break # Applied override, move to next tag
                                elif linked_instance:
                                     # Check if the specific element *inside* the link is on the target workset
                                     # This requires getting the element from the linked document, which is complex
                                     # and usually GetTaggedLocalElementId handles the resolution.
                                     # For this script, we primarily rely on GetTaggedLocalElementId or the link instance check.
                                     pass

                     if not found_match_in_link:
                          # If GetTaggedLocalElementId failed and GetTaggedElementIds didn't match the link instance workset
                          skipped_unlinked += 1
                else:
                    skipped_unlinked += 1

            except Exception as e:
                # print("# Error processing Tag ID {}: {}".format(tag.Id, e)) # Debug
                error_count += 1

        print("# Applied halftone override to {} tags associated with elements on workset '{}' in view '{}'.".format(count_halftoned, target_workset_name, active_view.Name))
        if skipped_unlinked > 0:
            print("# Skipped {} tags that were not linked to a valid local element or whose linked element/instance check didn't match.".format(skipped_unlinked))
        if error_count > 0:
            print("# Encountered errors processing {} tags.".format(error_count))

# Else (view invalid, worksharing off, or workset not found) handled by previous prints.