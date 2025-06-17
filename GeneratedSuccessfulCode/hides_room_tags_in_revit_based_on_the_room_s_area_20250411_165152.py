# Purpose: This script hides room tags in Revit based on the room's area.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often needed, good practice
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    UnitUtils,
    View,
    Architecture, # Required for RoomTag, Room
    ElementCategoryFilter,
    BuiltInCategory
)

# Attempt to import newer unit classes, handle fallback
try:
    from Autodesk.Revit.DB import ForgeTypeId
    from Autodesk.Revit.DB import UnitTypeId
    use_forge_type_id = True
except ImportError:
    from Autodesk.Revit.DB import DisplayUnitType
    use_forge_type_id = False

# --- Configuration ---
threshold_sqm = 2.0

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active valid view found.")
else:
    # --- Convert Threshold to Internal Units (Square Feet) ---
    threshold_internal = None
    conversion_success = False

    # Try Revit 2021+ ForgeTypeId/UnitTypeId method first
    if use_forge_type_id:
        try:
            # Use UnitTypeId.SquareMeters if available
            if hasattr(UnitTypeId, 'SquareMeters'):
                 square_meters_type_id = UnitTypeId.SquareMeters
                 if UnitUtils.IsValidUnit(square_meters_type_id):
                     threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_sqm, square_meters_type_id)
                     conversion_success = True
                     # print("# Info: Used UnitTypeId.SquareMeters for unit conversion.") # Optional Debug
                 else:
                     # Fallback to ForgeTypeId string lookup if UnitTypeId property didn't work
                     try:
                         # Example ForgeTypeId string (check specific Revit version docs if needed)
                         forge_type_id_str = "autodesk.unit.unit:squareMeters-1.0.0"
                         square_meters_forge_type = ForgeTypeId(forge_type_id_str)
                         if UnitUtils.IsValidUnit(square_meters_forge_type):
                             threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_sqm, square_meters_forge_type)
                             conversion_success = True
                             # print("# Info: Used ForgeTypeId string lookup for unit conversion.") # Optional Debug
                     except Exception as ft_str_e:
                         # print("# Info: Failed ForgeTypeId string lookup: {}".format(ft_str_e)) # Optional Debug
                         pass # Continue to next fallback
            else: # If UnitTypeId.SquareMeters doesn't exist, try ForgeTypeId string lookup directly
                 try:
                     forge_type_id_str = "autodesk.unit.unit:squareMeters-1.0.0"
                     square_meters_forge_type = ForgeTypeId(forge_type_id_str)
                     if UnitUtils.IsValidUnit(square_meters_forge_type):
                         threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_sqm, square_meters_forge_type)
                         conversion_success = True
                         # print("# Info: Used ForgeTypeId string lookup (direct) for unit conversion.") # Optional Debug
                 except Exception as ft_str_e:
                     # print("# Info: Failed ForgeTypeId string lookup (direct): {}".format(ft_str_e)) # Optional Debug
                     pass # Continue to next fallback

        except Exception as ft_e:
             # print("# Info: Failed using ForgeTypeId/UnitTypeId method: {}".format(ft_e)) # Optional Debug
             pass # Continue to next fallback

    # Fallback for older API versions (pre-2021) using DisplayUnitType
    if not conversion_success and not use_forge_type_id and DisplayUnitType:
        try:
            threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_sqm, DisplayUnitType.DUT_SQUARE_METERS)
            conversion_success = True
            # print("# Info: Used DisplayUnitType (legacy) for unit conversion.") # Optional Debug
        except Exception as dut_e:
            print("# Error: Failed converting threshold units using DisplayUnitType: {}".format(dut_e))
            # Keep conversion_success as False

    if not conversion_success or threshold_internal is None:
        print("# Error: Could not determine internal units for threshold area. Cannot proceed.")
    else:
        # --- Collect Room Tags in Active View ---
        # Using BuiltInCategory.OST_RoomTags is more direct than OfClass(Architecture.RoomTag) sometimes
        collector = FilteredElementCollector(doc, active_view.Id).OfCategory(BuiltInCategory.OST_RoomTags).WhereElementIsNotElementType()

        room_tags_to_hide = List[ElementId]()
        processed_count = 0
        hidden_count = 0
        orphaned_tags = 0

        for tag in collector:
            # Double check it's a RoomTag (though collector should handle this)
            if isinstance(tag, Architecture.RoomTag):
                processed_count += 1
                try:
                    # Get the ID of the room being tagged
                    tagged_room_id = tag.TaggedLocalRoomId

                    if tagged_room_id != ElementId.InvalidElementId:
                        # Get the Room element
                        room = doc.GetElement(tagged_room_id)
                        if room and isinstance(room, Architecture.Room):
                            # Get the room area (already in internal units - sq feet)
                            room_area = room.Area
                            if room_area < threshold_internal:
                                # Check if already hidden (optional, good practice)
                                try:
                                    if not tag.IsHidden(active_view):
                                        room_tags_to_hide.Add(tag.Id)
                                        hidden_count += 1
                                except Exception as is_hidden_e:
                                     # print("# Warning: Could not check if tag ID {} is hidden: {}. Adding to hide list anyway.".format(tag.Id, is_hidden_e)) # Optional Debug
                                     room_tags_to_hide.Add(tag.Id) # Add anyway if check fails
                                     hidden_count += 1 # Assume it wasn't hidden
                        else:
                             # print("# Warning: Tag ID {} refers to Element ID {} which is not a valid Room.".format(tag.Id, tagged_room_id)) # Optional Debug
                             pass
                    else:
                        # Tag is orphaned (not tagging any room)
                        orphaned_tags += 1
                        # Decide whether to hide orphaned tags or not - typically they are not hidden by area filters
                        # print("# Info: Tag ID {} is orphaned.".format(tag.Id)) # Optional Debug
                        pass

                except Exception as e:
                    print("# Error processing RoomTag ID {}: {}".format(tag.Id, e))

        # --- Hide Collected Room Tags ---
        if room_tags_to_hide.Count > 0:
            try:
                # Hide the elements (Transaction managed externally)
                active_view.HideElements(room_tags_to_hide)
                print("# Attempted to hide {} Room Tags for rooms smaller than {} sq meters in view '{}'.".format(hidden_count, threshold_sqm, active_view.Name))
            except Exception as hide_e:
                print("# Error occurred while hiding Room Tags: {}".format(hide_e))
        else:
            print("# No Room Tags found for rooms smaller than {} sq meters to hide in view '{}'.".format(threshold_sqm, active_view.Name))

        print("# Processed {} Room Tags. Found {} orphaned tags.".format(processed_count, orphaned_tags))