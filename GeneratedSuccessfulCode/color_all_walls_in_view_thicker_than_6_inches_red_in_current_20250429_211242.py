import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Wall,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    ElementId, View, ViewType, UnitUtils
)
# Note: Specific unit classes (UnitTypeId, DisplayUnitType) are imported conditionally below

# --- Configuration ---
# Target thickness in inches
min_thickness_inches = 6.0
# Override color (Red)
override_color = Color(255, 0, 0)

# --- Unit Conversion Handling (Robust for different Revit versions) ---
min_thickness_feet = 0.0 # Initialize
conversion_successful = False
try:
    # Try Revit 2021+ Unit API first
    from Autodesk.Revit.DB import UnitTypeId # Import only if attempting new API
    min_thickness_feet = UnitUtils.ConvertToInternalUnits(min_thickness_inches, UnitTypeId.Inches)
    conversion_successful = True
    # print("DEBUG: Used new Unit API (UnitTypeId)") # Optional debug
except (NameError, AttributeError, ImportError):
    # Fallback to older Revit API Unit Handling
    try:
        from Autodesk.Revit.DB import DisplayUnitType # Import only if attempting old API
        # Ensure DUT_DECIMAL_INCHES exists, common but check specific Revit version docs if issues arise
        min_thickness_feet = UnitUtils.ConvertToInternalUnits(min_thickness_inches, DisplayUnitType.DUT_DECIMAL_INCHES)
        conversion_successful = True
        # print("DEBUG: Used old Unit API (DisplayUnitType)") # Optional debug
    except (NameError, AttributeError, ImportError):
        # Further fallback: Manual conversion (assuming internal units are feet)
        try:
            min_thickness_feet = min_thickness_inches / 12.0
            conversion_successful = True
            # print("Warning: Unit API conversion failed. Used fallback inches/12.0.") # Optional warning
        except Exception as e_fallback:
            # print("FATAL: All unit conversion methods failed: {}".format(e_fallback)) # Optional error logging
            conversion_successful = False # Mark as failed

# Define acceptable plan view types
plan_view_types = [
    ViewType.FloorPlan,
    ViewType.CeilingPlan,
    ViewType.AreaPlan,
    ViewType.EngineeringPlan
]
# Try adding StructuralPlan if available (might not exist in older versions)
try:
    plan_view_types.append(ViewType.StructuralPlan)
except AttributeError:
    pass

# --- Get Active View ---
# Assumes 'doc' and 'uidoc' are pre-defined
active_view = doc.ActiveView

# --- Validate Active View and Unit Conversion ---
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    pass # Silently exit if not a valid view or is a template
elif active_view.ViewType not in plan_view_types:
    pass # Silently exit if not an accepted plan view type
elif not conversion_successful:
    # print("Error: Could not determine wall thickness units. Script aborted.") # Optional feedback
    pass # Silently exit if unit conversion failed
else:
    # --- Find Solid Fill Pattern Element Id ---
    solid_pattern_id = ElementId.InvalidElementId
    try:
        fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
        solid_fill_elements = []
        for pattern in fill_pattern_collector:
            try:
                fill_pattern = pattern.GetFillPattern()
                # Check if the pattern is solid
                if fill_pattern.IsSolidFill:
                     solid_fill_elements.append(pattern)
            except Exception:
                pass # Ignore patterns that error on GetFillPattern

        if solid_fill_elements:
             # Prefer Drafting patterns if available
             drafting_solid = [p for p in solid_fill_elements if p.GetFillPattern().Target == FillPatternTarget.Drafting]
             if drafting_solid:
                 solid_pattern_id = drafting_solid[0].Id
             else:
                 # Fallback to the first solid fill pattern found, regardless of target
                 model_solid = [p for p in solid_fill_elements if p.GetFillPattern().Target == FillPatternTarget.Model]
                 if model_solid:
                     solid_pattern_id = model_solid[0].Id
                 elif solid_fill_elements: # Take any solid if no drafting/model preferred found
                     solid_pattern_id = solid_fill_elements[0].Id

        # Fallback: Find by name if ID search failed (less reliable due to localization)
        if solid_pattern_id == ElementId.InvalidElementId:
            # Common names, adjust if necessary for specific Revit language versions
            solid_fill_names = ["Solid fill", "<Solid fill>"] # Add other common localized names if needed
            fp_collector_by_name = FilteredElementCollector(doc).OfClass(FillPatternElement)
            solid_pattern_by_name = None
            for fp in fp_collector_by_name:
                try:
                    if fp.Name in solid_fill_names:
                         # Check if it's actually solid fill if found by name
                         fp_pattern = fp.GetFillPattern()
                         if fp_pattern and fp_pattern.IsSolidFill:
                            solid_pattern_by_name = fp
                            break # Found one
                except Exception:
                    pass # Ignore elements that error on Name property or GetFillPattern
            if solid_pattern_by_name:
                solid_pattern_id = solid_pattern_by_name.Id

    except Exception as e_pattern:
        # print("Error finding solid fill pattern: {}".format(e_pattern)) # Optional debug
        pass # Continue without a pattern ID if search fails

    # --- Create Override Settings ---
    override_settings = OverrideGraphicSettings()

    # Set Cut Fill Pattern Colors to Red
    override_settings.SetCutForegroundPatternColor(override_color)
    override_settings.SetCutBackgroundPatternColor(override_color) # Set background to red too for solid appearance

    # Set Cut Fill Pattern Visibility to True
    override_settings.SetCutBackgroundPatternVisible(True)
    override_settings.SetCutForegroundPatternVisible(True)

    # Set Cut Fill Pattern to Solid Fill if found
    if solid_pattern_id != ElementId.InvalidElementId:
        override_settings.SetCutForegroundPatternId(solid_pattern_id)
        override_settings.SetCutBackgroundPatternId(solid_pattern_id) # Use solid for background too
    else:
        # If no solid pattern ID found, the color settings alone should make it appear solid red.
        # print("Warning: Could not find 'Solid fill' pattern ID. Applying color override only.") # Optional feedback
        pass

    # --- Collect and Filter Walls in the Active View ---
    wall_collector = FilteredElementCollector(doc, active_view.Id)\
                     .OfCategory(BuiltInCategory.OST_Walls)\
                     .WhereElementIsNotElementType()

    # --- Apply Overrides ---
    # Note: Transaction is handled externally by the calling code (e.g., C# wrapper)
    walls_overridden_count = 0
    walls_processed_count = 0
    tolerance = 1e-9 # Tolerance for floating point comparison

    for wall in wall_collector:
        if isinstance(wall, Wall):
            walls_processed_count += 1
            try:
                # Use the Wall.Width property (already in internal units - feet)
                wall_width = wall.Width
                # Check if wall thickness is greater than the minimum required (with tolerance)
                if wall_width > (min_thickness_feet - tolerance):
                    # Apply the override to this specific wall element in the active view
                    active_view.SetElementOverrides(wall.Id, override_settings)
                    walls_overridden_count += 1
            except Exception as e_wall:
                # Silently ignore walls that cause errors (e.g., cannot get Width, specific wall types)
                # print("DEBUG: Error processing wall {}: {}".format(wall.Id, e_wall)) # Optional debug
                pass

    # Final status message (optional, printed to the console where Revit runs Python)
    # print("Script finished. Processed {} walls, overridden {} walls.".format(walls_processed_count, walls_overridden_count))