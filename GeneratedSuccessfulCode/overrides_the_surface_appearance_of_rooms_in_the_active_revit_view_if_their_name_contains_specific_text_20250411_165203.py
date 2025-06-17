# Purpose: This script overrides the surface appearance of rooms in the active Revit view if their name contains specific text.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Color and Exceptions
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Architecture, # Import the Architecture namespace
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    FillPattern,      # Needed for IsSolidFill check
    FillPatternTarget,
    ElementId,
    View,
    BuiltInParameter
)
import System # For exception handling

# --- Configuration ---
search_text = "Office" # Text to search for in the room name (case-insensitive)
override_color = Color(0, 0, 255) # Blue color

# --- Get Active View ---
# Assume 'doc' is pre-defined
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
    # Exit script cleanly if no suitable view - let wrapper handle exit
    # import sys
    # sys.exit()
else:
    # --- Find a Solid Fill Pattern ---
    solid_fill_pattern_id = ElementId.InvalidElementId
    solid_fill_pattern_element = None

    try:
        # Iterate and check IsSolidFill (more robust than by name)
        fill_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
        for fp_elem in fill_patterns:
            if fp_elem is not None:
                pattern = fp_elem.GetFillPattern()
                if pattern is not None and pattern.IsSolidFill:
                    # Check if it's a Drafting pattern, as required for surface overrides
                    if pattern.Target == FillPatternTarget.Drafting:
                        solid_fill_pattern_element = fp_elem
                        break # Found one, stop searching

        if solid_fill_pattern_element:
            solid_fill_pattern_id = solid_fill_pattern_element.Id
            # print("# Debug: Found solid fill pattern: ID {{{{}}}}, Name '{{{{}}}}'".format(solid_fill_pattern_id, solid_fill_pattern_element.Name)) # Escaped format
        else:
            print("# Warning: No solid fill drafting pattern found in the document. Surface override may not appear solid.")
            # Script will proceed without setting a pattern ID, relying only on color.

    except System.Exception as e:
        print("# Warning: Error occurred while searching for solid fill pattern: {{}}. Proceeding without pattern.".format(e))
        solid_fill_pattern_id = ElementId.InvalidElementId # Ensure it's invalid if error occurs

    # --- Define Override Graphic Settings ---
    override_settings = OverrideGraphicSettings()

    # Set surface foreground pattern settings
    override_settings.SetSurfaceForegroundPatternColor(override_color)
    override_settings.SetSurfaceForegroundPatternVisible(True)
    if solid_fill_pattern_id != ElementId.InvalidElementId:
        override_settings.SetSurfaceForegroundPatternId(solid_fill_pattern_id)

    # Set surface background pattern settings for solid appearance
    override_settings.SetSurfaceBackgroundPatternColor(override_color)
    override_settings.SetSurfaceBackgroundPatternVisible(True)
    if solid_fill_pattern_id != ElementId.InvalidElementId:
        override_settings.SetSurfaceBackgroundPatternId(solid_fill_pattern_id)

    # --- Collect and Override Rooms ---
    applied_count = 0
    error_count = 0
    processed_count = 0

    try:
        # Collect Room elements visible in the active view
        # Note: Rooms might exist in the model but not be placed/visible in certain views.
        # Filtering by active_view.Id ensures we only try to override visible ones.
        room_collector = FilteredElementCollector(doc, active_view.Id)\
                            .OfCategory(BuiltInCategory.OST_Rooms)\
                            .WhereElementIsNotElementType()

        for room in room_collector:
            processed_count += 1
            # Use Architecture.Room for type checking
            if isinstance(room, Architecture.Room):
                try:
                    # Get the 'Name' parameter using BuiltInParameter for reliability
                    name_param = room.get_Parameter(BuiltInParameter.ROOM_NAME)

                    # Check if the parameter exists, has a value, and contains the search text (case-insensitive)
                    if name_param and name_param.HasValue:
                        room_name = name_param.AsString()
                        if room_name and search_text.lower() in room_name.lower():
                            try:
                                # Apply override within the active view
                                active_view.SetElementOverrides(room.Id, override_settings)
                                applied_count += 1
                            except System.Exception as apply_ex:
                                print("# Error applying override to Room ID {{}}: {{}}".format(room.Id, apply_ex.Message)) # Escaped format
                                error_count += 1
                except System.Exception as param_ex:
                    # Catch errors getting the parameter (less likely with BuiltInParameter but possible)
                    # print("# Info: Could not check parameter for Room ID {{{{}}}}: {{{{}}}}".format(room.Id, param_ex.Message)) # Optional debug info
                    error_count += 1

    except System.Exception as general_ex:
        print("# Error during room collection or processing: {{}}".format(general_ex)) # Escaped format
        error_count += 1

    # --- Final Summary ---
    if applied_count > 0:
        print("# Successfully applied solid blue surface override to {{}} Room(s) containing '{{}}' in their name in the active view '{{}}'.".format(applied_count, search_text, active_view.Name)) # Escaped format
    elif processed_count > 0 and error_count == 0:
         print("# No Rooms found containing '{{}}' in their name among the {{}} rooms processed in the active view.".format(search_text, processed_count)) # Escaped format
    elif processed_count == 0 and error_count == 0:
         print("# No Room elements found in the active view.")

    if error_count > 0:
        print("# Encountered {{}} errors during processing.".format(error_count)) # Escaped format