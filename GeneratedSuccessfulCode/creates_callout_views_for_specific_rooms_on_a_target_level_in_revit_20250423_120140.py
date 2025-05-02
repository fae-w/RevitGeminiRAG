# Purpose: This script creates callout views for specific rooms on a target level in Revit.

﻿# Import necessary classes
import clr
clr.AddReference('System') # For System.String comparisons if needed
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
# Note: Removed clr.AddReference('RevitAPI.Architecture') as it's part of RevitAPI.dll

from System import StringComparison, Guid
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    SpatialElement,
    View,
    ViewPlan,
    ViewFamilyType,
    ViewFamily, # Required for checking VFT family
    ViewType,
    ElementId,
    XYZ,
    BoundingBoxXYZ,
    ElementLevelFilter,
    BuiltInCategory,
    BuiltInParameter
)
from Autodesk.Revit.DB.Architecture import Room # Import Room from correct namespace

# --- Configuration ---
target_level_name = "L3"
room_name_substring = "Suite"
target_vft_name = "Enlarged Suite Plan"
callout_name_prefix = "Callout of "
# Tolerance for checking if bounding box points are distinct enough
bbox_tolerance = 0.01 # feet (approx 1/8 inch)

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name (case-insensitive)."""
    levels = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    for level in levels:
        try:
            # Use parameter first for reliability, fallback to Name
            name_param = level.get_Parameter(BuiltInParameter.LEVEL_NAME)
            level_actual_name = name_param.AsString() if name_param else level.Name

            if level_actual_name and level_actual_name.Equals(level_name, StringComparison.InvariantCultureIgnoreCase):
                 return level.Id
        except Exception:
             # Handles potential errors accessing Name property or parameter
             continue
    print("# Error: Level named '{}' not found.".format(level_name))
    return ElementId.InvalidElementId

def find_view_family_type(doc_param, vft_name):
    """Finds a Floor Plan ViewFamilyType by name (case-insensitive) and returns its ID."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        try:
            # Case-insensitive comparison using Name property
            if vft.Name.Equals(vft_name, StringComparison.InvariantCultureIgnoreCase):
                 # Check if it's a Floor Plan type as required by ViewPlan.CreateCallout
                 if vft.ViewFamily == ViewFamily.FloorPlan:
                      return vft.Id
                 else:
                      print("# Info: Found ViewFamilyType '{}' but it is not a FloorPlan type (Family: {}). Skipping this type.".format(vft_name, vft.ViewFamily.ToString()))
        except Exception as e:
             # Handles potential errors accessing Name or ViewFamily property
             print("# Warning: Error checking ViewFamilyType ID {}. Error: {}".format(vft.Id.ToString(), str(e)))
             continue
    print("# Error: Floor Plan ViewFamilyType named '{}' not found.".format(vft_name))
    return ElementId.InvalidElementId

# --- Main Script ---

# Get current document - assumes 'doc' is predefined

# Find the target level ID
target_level_id = find_level_by_name(doc, target_level_name)
if target_level_id == ElementId.InvalidElementId:
    print("# Script stopped: Target level '{}' could not be found.".format(target_level_name))
else:
    # Find the target ViewFamilyType ID (must be a FloorPlan type)
    target_vft_id = find_view_family_type(doc, target_vft_name)
    if target_vft_id == ElementId.InvalidElementId:
        print("# Script stopped: Target Floor Plan ViewFamilyType '{}' could not be found.".format(target_vft_name))
    else:
        # Filter for Rooms on the target level
        level_filter = ElementLevelFilter(target_level_id)
        rooms_on_level = FilteredElementCollector(doc)\
                          .OfCategory(BuiltInCategory.OST_Rooms)\
                          .WherePasses(level_filter)\
                          .WhereElementIsNotElementType()\
                          .ToElements()

        rooms_processed_count = 0
        callouts_created_count = 0

        # Iterate through rooms and create callouts
        for room in rooms_on_level:
            # Ensure it's actually placed (has Location and Area) and get name
            room_name = ""
            try:
                if room.Location is not None and room.Area > 0: # Check if room is placed and has area
                    room_name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)
                    if room_name_param:
                        room_name = room_name_param.AsString()
                else:
                    # Skip unplaced or zero-area rooms silently
                    continue
            except Exception as e:
                print("# Warning: Could not get name or location for Room ID {}. Skipping. Error: {}".format(room.Id.ToString(), str(e)))
                continue

            # Check if room name contains the substring (case-insensitive)
            if room_name and room_name_substring.lower() in room_name.lower():
                rooms_processed_count += 1
                # Get room bounding box
                try:
                    bbox = room.get_BoundingBox(None) # Pass None to get model coordinates BBox
                    if bbox is None or not bbox.Enabled:
                        print("# Warning: Room ID {} '{}' has no valid bounding box. Skipping.".format(room.Id.ToString(), room_name))
                        continue

                    # Extract corner points for the callout region
                    p1 = bbox.Min
                    p3 = bbox.Max # Use Min and Max for ViewPlan.CreateCallout

                    # Ensure points are not too close to avoid errors
                    if p1.DistanceTo(p3) < bbox_tolerance:
                         print("# Warning: Room ID {} '{}' has a degenerate bounding box (Min/Max too close). Skipping.".format(room.Id.ToString(), room_name))
                         continue

                    # Find a suitable parent view (an existing *Floor Plan* View showing the room's level)
                    parent_view = None
                    views = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements()
                    for v in views:
                        # Check if view is a FloorPlan, not a template, and matches the room's level
                        if not v.IsTemplate and v.ViewType == ViewType.FloorPlan:
                             # Check level using the dedicated parameter for plan views
                             view_level_id = ElementId.InvalidElementId
                             try:
                                 # Primarily use GenLevel property
                                 if v.GenLevel:
                                     view_level_id = v.GenLevel.Id
                             except Exception:
                                 # GenLevel might throw if not applicable, though unlikely for FloorPlan
                                 pass

                             # Fallback or secondary check using parameter (might be less reliable or differ across view types)
                             # if view_level_id == ElementId.InvalidElementId:
                             #     view_level_param = v.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL) # More specific to plan views
                             #     if view_level_param and view_level_param.HasValue:
                             #         view_level_id = view_level_param.AsElementId()


                             if view_level_id == target_level_id:
                                 parent_view = v
                                 break # Found a suitable parent view

                    if parent_view is None:
                         print("# Warning: Could not find a suitable parent Floor Plan View on Level '{}' for Room ID {}. Skipping.".format(target_level_name, room.Id.ToString()))
                         continue

                    # Create the callout using ViewPlan.CreateCallout
                    try:
                        # CreateCallout requires parent view ID, target ViewFamilyType ID (FloorPlan type), and corner points
                        new_callout_view_id = ViewPlan.CreateCallout(doc,
                                                                     parent_view.Id,
                                                                     target_vft_id,
                                                                     p1,
                                                                     p3)

                        if new_callout_view_id != ElementId.InvalidElementId:
                            # Get the newly created view element using its ID
                            new_view = doc.GetElement(new_callout_view_id)
                            if new_view:
                                # Rename the new callout view
                                try:
                                    view_name_param = new_view.get_Parameter(BuiltInParameter.VIEW_NAME)
                                    if view_name_param:
                                        view_name_param.Set("{}{}".format(callout_name_prefix, room_name))
                                        callouts_created_count += 1
                                        # print("# Info: Created callout '{}' for Room ID {}.".format(new_view.Name, room.Id.ToString())) # Optional verbose output
                                    else:
                                        print("# Warning: Could not get VIEW_NAME parameter for new callout view ID: {}. Cannot rename.".format(new_callout_view_id.ToString()))

                                except Exception as rename_e:
                                    print("# Error: Failed to rename callout view ID: {}. Error: {}".format(new_callout_view_id.ToString(), str(rename_e)))
                            else:
                                print("# Warning: Failed to retrieve the newly created callout view (ID: {}) for Room ID {} '{}' after creation.".format(new_callout_view_id.ToString(), room.Id.ToString(), room_name))
                        else:
                             print("# Warning: Failed to create callout for Room ID {} '{}'. ViewPlan.CreateCallout returned InvalidElementId.".format(room.Id.ToString(), room_name))

                    except Exception as e:
                         # Catch potential exceptions during callout creation or renaming
                         print("# Error: Failed to create or rename callout for Room ID {} '{}'. Parent View ID: {}, VFT ID: {}. Error: {}".format(
                             room.Id.ToString(),
                             room_name,
                             parent_view.Id.ToString(),
                             target_vft_id.ToString(),
                             str(e)))

                except Exception as e:
                     # Catch potential exceptions during bounding box retrieval or processing
                     print("# Error: Failed processing Room ID {} '{}'. Error: {}".format(room.Id.ToString(), room_name, str(e)))


        print("# --- Script Summary ---")
        print("# Target Level: {}".format(target_level_name))
        print("# Room Name Substring: '{}'".format(room_name_substring))
        print("# Target ViewFamilyType: '{}'".format(target_vft_name))
        print("# Rooms matching criteria found: {}".format(rooms_processed_count))
        print("# Callout views created: {}".format(callouts_created_count))

# --- End Script ---