# Purpose: This script changes the graphic overrides of doors on a specific level in the active Revit view.

# Purpose: This script changes the graphic overrides of doors on a specific level in the active Revit view.

﻿# Import necessary Revit API classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Often needed, though maybe not strictly for this task

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Level,
    ElementId, View, OverrideGraphicSettings, Color, FillPatternElement,
    FillPatternTarget, ViewType
)
# Note: Removed 'Door' from import as it caused the original error.
# Filtering by category OST_Doors is sufficient.

# Define the target level name and color
target_level_name = "Level 1"
target_color = Color(255, 0, 0) # Red color

# --- Find the target Level ElementId ---
level_id = ElementId.InvalidElementId
level_collector = FilteredElementCollector(doc).OfClass(Level)
target_level = None
for level in level_collector:
    if level.Name == target_level_name:
        target_level = level
        break

if not target_level:
    print("# Error: Level named '{}' not found.".format(target_level_name))
else:
    level_id = target_level.Id

    # --- Get the active view ---
    active_view = doc.ActiveView
    if not active_view:
        print("# Error: No active view found. Cannot apply overrides.")
    # Check if the view type supports element overrides
    elif not active_view.CanApplyOverrides():
         print("# Error: Cannot apply element overrides in the current active view '{}' (View Type: {}).".format(active_view.Name, active_view.ViewType))
         active_view = None # Prevent further processing

    # --- Find the Solid Fill pattern ---
    solid_fill_pattern_id = ElementId.InvalidElementId
    fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
    # Find the first solid fill pattern available
    for fp_elem in fill_pattern_collector:
        fill_pattern = fp_elem.GetFillPattern()
        if fill_pattern.IsSolidFill:
            solid_fill_pattern_id = fp_elem.Id
            break # Found one, stop searching

    if solid_fill_pattern_id == ElementId.InvalidElementId:
         print("# Warning: Solid fill pattern not found. Color will be applied without solid pattern.")

    # --- Proceed only if level and view are valid ---
    if level_id != ElementId.InvalidElementId and active_view:

        # --- Create override graphic settings ---
        override_settings = OverrideGraphicSettings()
        override_settings.SetSurfaceForegroundPatternColor(target_color)

        # Apply solid fill pattern if found
        if solid_fill_pattern_id != ElementId.InvalidElementId:
            override_settings.SetSurfaceForegroundPatternId(solid_fill_pattern_id)
            override_settings.SetSurfaceForegroundPatternVisible(True)
        else:
            # Color is set, but pattern isn't. Visibility depends on view settings.
            # We won't force visibility without a pattern ID.
            pass

        # --- Collect Door instances on the target level in the active view ---
        # Filter by view to ensure elements are visible/relevant in the context
        door_collector = FilteredElementCollector(doc, active_view.Id)\
                         .OfCategory(BuiltInCategory.OST_Doors)\
                         .WhereElementIsNotElementType()

        doors_on_level_ids = []
        for door_element in door_collector:
            try:
                # Check if the door's LevelId matches the target level
                # Use get_Parameter for potentially more robust level checking if LevelId fails
                if hasattr(door_element, "LevelId") and door_element.LevelId == level_id:
                     doors_on_level_ids.append(door_element.Id)
            except Exception as e:
                # print("# Debug: Could not check level for door {}: {}".format(door_element.Id, e))
                pass # Ignore doors where level cannot be reliably checked

        # --- Apply overrides in the active view ---
        if doors_on_level_ids:
            print("# Applying overrides to {} doors on '{}' in view '{}'".format(len(doors_on_level_ids), target_level_name, active_view.Name))
            for door_id in doors_on_level_ids:
                try:
                    active_view.SetElementOverrides(door_id, override_settings)
                except Exception as e:
                    print("# Error applying override to element {}: {}".format(door_id, e))
        else:
            # This message is printed only if the level and view were valid, but no doors were found matching the criteria
            print("# No doors found on level '{}' in the active view '{}'.".format(target_level_name, active_view.Name))

# End of script