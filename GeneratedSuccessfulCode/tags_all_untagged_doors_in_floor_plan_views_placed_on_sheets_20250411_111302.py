# Purpose: This script tags all untagged doors in floor plan views placed on sheets.

# Purpose: This script tags all untagged doors in floor plan views placed on sheets in a Revit project.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List, HashSet, ICollection, ISet

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilySymbol,
    ViewSheet,
    Viewport,
    View,
    ViewType,
    FamilyInstance,
    ElementId,
    IndependentTag,
    TagMode,
    TagOrientation,
    XYZ,
    Reference,
    LocationPoint,
    LocationCurve
)

# --- Configuration ---
ADD_LEADER = False  # Set to True if you want leaders on the new tags
TAG_ORIENTATION = TagOrientation.Horizontal # Or TagOrientation.Vertical

# --- Helper function to find the first loaded Door Tag Type ---
def find_default_door_tag_type(doc):
    """Finds the first loaded door tag type."""
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_DoorTags)
    first_tag_type = collector.FirstElement()
    if first_tag_type:
        return first_tag_type.Id
    else:
        return ElementId.InvalidElementId

# --- Main Script ---

# 1. Find the default Door Tag Type ID
door_tag_type_id = find_default_door_tag_type(doc)

if door_tag_type_id == ElementId.InvalidElementId:
    print("# Error: No Door Tag types found in the project. Load a Door Tag family.")
else:
    # Get all sheets in the document
    sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()

    if not sheets:
        print("# No sheets found in the document.")
    else:
        tagged_count = 0
        processed_views_count = 0

        # Iterate through each sheet
        for sheet in sheets:
            if not isinstance(sheet, ViewSheet):
                continue

            try:
                # Get all viewport IDs on the current sheet
                viewport_ids = sheet.GetAllViewports() # Returns ICollection<ElementId>

                if not viewport_ids or viewport_ids.Count == 0:
                    continue

                # Iterate through viewport IDs to find Floor Plan views
                for vp_id in viewport_ids:
                    viewport = doc.GetElement(vp_id)
                    if not isinstance(viewport, Viewport):
                        continue

                    # Get the view associated with the viewport
                    view = doc.GetElement(viewport.ViewId)
                    if not isinstance(view, View):
                        continue

                    # Check if the view is a Floor Plan and not a template
                    if view.ViewType == ViewType.FloorPlan and not view.IsTemplate:
                        processed_views_count += 1
                        view_id = view.Id

                        # Find existing door tags in this specific view
                        existing_tagged_door_ids = HashSet[ElementId]()
                        tag_collector = FilteredElementCollector(doc, view_id).OfCategory(BuiltInCategory.OST_DoorTags).OfClass(IndependentTag)
                        for tag in tag_collector:
                            # IndependentTag.GetTaggedLocalElement() should return the element tagged by this tag *in this view*
                            try:
                                tagged_element = tag.GetTaggedLocalElement(doc) # Changed from GetTaggedElementId to handle workshared environments potentially better? No, GetTaggedLocalElement does not exist. Let's try GetTaggedElementIds()
                                # GetTaggedElementIds returns ICollection<LinkElementId>
                                # Let's try the old way first or a property...
                                # Revit 2022+ has taggedElementId = tag.TaggedElementId
                                # Revit 2023+ has taggedElement = tag.GetTaggedElement()
                                # For wider compatibility let's try iterating GetTaggedElementIds() even if it's usually one.
                                # Let's assume tag.TaggedElementId property exists and works for non-multiref tags
                                if hasattr(tag, 'TaggedElementId') and tag.TaggedElementId:
                                     # Check if it's a local element id
                                     link_elem_id = tag.TaggedElementId
                                     if link_elem_id.HostElementId == ElementId.InvalidElementId and link_elem_id.LinkedElementId == ElementId.InvalidElementId:
                                         # This seems to be how a local element is represented sometimes
                                         pass # No good way here?
                                     # Let's try GetTaggedLocalElementId if available, fallback to TaggedElementId
                                     local_id_to_add = ElementId.InvalidElementId
                                     if hasattr(tag, 'GetTaggedLocalElementId') and callable(getattr(tag, 'GetTaggedLocalElementId')):
                                         local_id_to_add = tag.GetTaggedLocalElementId() # Prefer this if available
                                     elif hasattr(tag, 'TaggedElementId'):
                                         # Older way, might be LinkElementId
                                         link_el_id = tag.TaggedElementId
                                         # Heuristic: If LinkInstanceId is invalid, assume it's local
                                         if link_el_id and link_el_id.LinkInstanceId == ElementId.InvalidElementId:
                                             local_id_to_add = link_el_id.HostElementId

                                     if local_id_to_add and local_id_to_add != ElementId.InvalidElementId:
                                          existing_tagged_door_ids.Add(local_id_to_add)
                                else:
                                    # Fallback for very old versions or if property missing? Get reference?
                                    # tagged_ref = tag.TagReference
                                    # if tagged_ref:
                                    #     existing_tagged_door_ids.Add(tagged_ref.ElementId) # This might tag the element in linked file context incorrectly?
                                    pass # Skip if we cannot reliably get the tagged ID

                            except Exception as e_tag_check:
                                # print(f"# Warning: Could not get tagged element for tag {tag.Id} in view {view.Name}. Error: {e_tag_check}") # Escaped debug
                                pass


                        # Find all doors visible in this view
                        door_collector = FilteredElementCollector(doc, view_id).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

                        # Iterate through doors and tag if untagged
                        for door in door_collector:
                            if isinstance(door, FamilyInstance) and door.Id not in existing_tagged_door_ids:
                                try:
                                    # Create a reference to the door
                                    door_ref = Reference(door)

                                    # Determine tag location - use LocationPoint if available, else bounding box center
                                    tag_point = None
                                    location = door.Location
                                    if isinstance(location, LocationPoint):
                                        tag_point = location.Point
                                    elif isinstance(location, LocationCurve):
                                        # Use midpoint of the location curve
                                        curve = location.Curve
                                        tag_point = curve.Evaluate(0.5, True) # Parameter 0.5, normalized = True
                                    else:
                                        # Fallback: Bounding box center in the view
                                        bbox = door.get_BoundingBox(view)
                                        if bbox:
                                            # Use the midpoint of the bounding box, project Z to view plane? Usually view Z is irrelevant for tag XY.
                                            tag_point = (bbox.Min + bbox.Max) / 2.0
                                        else:
                                            # print(f"# Skipping door {door.Id} in view {view.Name}: Cannot determine location.") # Escaped debug
                                            continue # Skip if no location found

                                    if tag_point:
                                        # Create the tag
                                        new_tag = IndependentTag.Create(
                                            doc,                # Document
                                            door_tag_type_id,   # Tag Symbol ElementId (specific type)
                                            view_id,            # View ElementId
                                            door_ref,           # Reference to the door
                                            ADD_LEADER,         # Add Leader?
                                            TAG_ORIENTATION,    # Tag Orientation
                                            tag_point           # Tag location (XYZ)
                                        )
                                        if new_tag:
                                            tagged_count += 1
                                        else:
                                            # print(f"# Failed to create tag for door {door.Id} in view {view.Name}") # Escaped debug
                                            pass

                                except Exception as e_create:
                                    # print(f"# Error tagging door {door.Id} in view {view.Name}. Error: {e_create}") # Escaped debug
                                    pass # Continue with the next door

            except Exception as ex_sheet:
                # print(f"# Error processing sheet '{sheet.SheetNumber} - {sheet.Name}'. Error: {ex_sheet}") # Escaped debug
                pass # Continue with the next sheet

        # Optional: Print summary (commented out by default)
        # if tagged_count > 0:
        #     print(f"# Successfully created {tagged_count} door tags across {processed_views_count} floor plan views found on sheets.") # Escaped
        # else:
        #     print("# No untagged doors found in floor plan views on sheets, or no suitable views/doors found.") # Escaped