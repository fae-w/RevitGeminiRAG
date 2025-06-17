# Purpose: This script overrides the surface color of areas belonging to a specified area scheme in the active Revit view.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Color and Exceptions
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Area,               # Specific class for Areas
    AreaScheme,         # To find the correct Area Scheme
    OverrideGraphicSettings,
    Color,
    FillPatternElement,
    FillPattern,        # Needed for IsSolidFill check
    FillPatternTarget,  # To check for Drafting patterns
    ElementId,
    View,
    BuiltInParameter
)
import System # For exception handling

# --- Configuration ---
target_area_scheme_name = "Rentable"
override_color = Color(255, 255, 0) # Yellow color

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: No active graphical view found or active view is a template.")
    # Exit script cleanly if no suitable view
    import sys
    sys.exit()

# --- Find the Target Area Scheme ID ---
rentable_scheme_id = ElementId.InvalidElementId
area_schemes = FilteredElementCollector(doc).OfClass(AreaScheme).ToElements()
for scheme in area_schemes:
    if scheme.Name.lower() == target_area_scheme_name.lower():
        rentable_scheme_id = scheme.Id
        break

if rentable_scheme_id == ElementId.InvalidElementId:
    print("# Error: Area Scheme named '{}' not found in the document.".format(target_area_scheme_name))
    # Exit script cleanly if the scheme doesn't exist
    import sys
    sys.exit()
# else:
#     print("# Debug: Found Area Scheme '{{}}' with ID: {{{{{{{{}}}}}}}}".format(target_area_scheme_name, rentable_scheme_id)) # Optional Debug

# --- Find a Solid Fill Pattern ---
solid_fill_pattern_id = ElementId.InvalidElementId
solid_fill_pattern_element = None
try:
    # Iterate and check IsSolidFill and Target (more robust than by name)
    fill_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    for fp_elem in fill_patterns:
        if fp_elem is not None:
            pattern = fp_elem.GetFillPattern()
            # Ensure pattern is valid, is solid, and is a Drafting pattern (required for surface overrides)
            if pattern is not None and pattern.IsSolidFill and pattern.Target == FillPatternTarget.Drafting:
                solid_fill_pattern_element = fp_elem
                break # Found one, stop searching

    if solid_fill_pattern_element:
        solid_fill_pattern_id = solid_fill_pattern_element.Id
        # print("# Debug: Found solid fill drafting pattern: ID {{{{{{{{}}}}}}}}, Name '{{{{{{{{}}}}}}}}'".format(solid_fill_pattern_id, solid_fill_pattern_element.Name)) # Escaped format
    else:
        print("# Warning: No solid fill drafting pattern found. Surface override may not appear solid.")
        # Script will proceed without setting a pattern ID, relying only on color.

except System.Exception as e:
    print("# Warning: Error finding solid fill pattern: {{{{}}}}. Proceeding without pattern.".format(e))
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


# --- Collect and Override Areas ---
applied_count = 0
error_count = 0
processed_count = 0

try:
    # Collect Area elements visible in the active view
    area_collector = FilteredElementCollector(doc, active_view.Id)\
                        .OfCategory(BuiltInCategory.OST_Areas)\
                        .WhereElementIsNotElementType()

    for area in area_collector:
        processed_count += 1
        # Check if it's an Area element and not deleted/invalid
        if isinstance(area, Area) and area.IsValidObject:
            try:
                # Get the Area Scheme ID directly from the Area element
                area_scheme_id_param = area.get_Parameter(BuiltInParameter.AREA_SCHEME_ID)

                if area_scheme_id_param and area_scheme_id_param.HasValue:
                    current_scheme_id = area_scheme_id_param.AsElementId()
                    # Compare the Area's scheme ID with the target 'Rentable' scheme ID
                    if current_scheme_id == rentable_scheme_id:
                        try:
                            # Apply override within the active view
                            active_view.SetElementOverrides(area.Id, override_settings)
                            applied_count += 1
                        except System.Exception as apply_ex:
                            print("# Error applying override to Area ID {{{{}}}}: {{{{}}}}".format(area.Id, apply_ex.Message)) # Escaped format
                            error_count += 1
                # else: # Optional: Handle case where Area might not have the scheme ID parameter (unlikely for valid Areas)
                #    print("# Info: Area ID {{{{}}}} missing Area Scheme ID parameter.".format(area.Id))

            except System.Exception as param_ex:
                # Catch errors getting the parameter or checking the scheme
                print("# Error processing Area ID {{{{}}}}: {{{{}}}}".format(area.Id, param_ex.Message)) # Escaped format
                error_count += 1

except System.Exception as general_ex:
    print("# Error during Area collection or processing: {{{{}}}}".format(general_ex)) # Escaped format
    error_count += 1

# --- Final Summary ---
if applied_count > 0:
    print("# Successfully applied yellow surface override to {{{{}}}} Area(s) belonging to the '{{{{}}}}' scheme in view '{{{{}}}}'.".format(applied_count, target_area_scheme_name, active_view.Name)) # Escaped format
elif processed_count > 0 and error_count == 0:
     print("# No Areas found belonging to the '{{{{}}}}' scheme among the {{{{}}}} areas processed in the active view.".format(target_area_scheme_name, processed_count)) # Escaped format
elif processed_count == 0 and error_count == 0:
     print("# No Area elements found in the active view.")

if error_count > 0:
    print("# Encountered {{{{}}}} errors during processing.".format(error_count)) # Escaped format