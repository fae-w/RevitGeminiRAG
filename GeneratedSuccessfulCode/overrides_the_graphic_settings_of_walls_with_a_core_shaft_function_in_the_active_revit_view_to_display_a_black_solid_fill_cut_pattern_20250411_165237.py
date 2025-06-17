# Purpose: This script overrides the graphic settings of walls with a 'Core Shaft' function in the active Revit view to display a black solid fill cut pattern.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Ensure System is referenced for Enum.Parse

# Import Revit API namespaces
import Autodesk.Revit.DB as DB
import Autodesk.Revit.UI as UI
import System # Import System namespace for Enum.Parse

# --- Configuration ---
# Target Wall Function (CoreShaft corresponds to integer 5)
target_wall_function_value = 5
# Override color (Black)
override_color = DB.Color(0, 0, 0)

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined
if uidoc is None:
    print("# Error: UIDocument is not available.")
    # Consider raising an exception or exiting if appropriate
else:
    active_view = uidoc.ActiveView
    if not active_view or not isinstance(active_view, DB.View) or active_view.IsTemplate:
        print("# Error: No active graphical view found or the active view is a template.")
        # Consider raising an exception or exiting
    else:
        # --- Find Solid Fill Pattern Element Id ---
        solid_fill_pattern_id = DB.ElementId.InvalidElementId
        fill_pattern_collector = DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement).WhereElementIsNotElementType()
        # Common name, adjust if different in your Revit language/template
        solid_fill_pattern_name = "Solid fill"

        # First pass: Find by name, prioritizing Drafting type
        temp_solid_fill_id = DB.ElementId.InvalidElementId
        for pattern in fill_pattern_collector:
             # Use pattern name directly if available
            pattern_name = ""
            try:
                pattern_name = pattern.Name
            except Exception: # Some elements might not have a Name property easily accessible
                pass # Ignore patterns without a name or where accessing it fails

            if pattern_name == solid_fill_pattern_name:
                try:
                    fill_patt = pattern.GetFillPattern()
                    if fill_patt: # Check if GetFillPattern returned a valid pattern
                        if fill_patt.Target == DB.FillPatternTarget.Drafting:
                            solid_fill_pattern_id = pattern.Id
                            # print("# Debug: Found preferred drafting solid fill by name: {}".format(pattern.Id))
                            break # Found the preferred drafting solid fill
                        elif temp_solid_fill_id == DB.ElementId.InvalidElementId:
                            # Store the first non-drafting solid fill found by name as a fallback
                            temp_solid_fill_id = pattern.Id
                            # print("# Debug: Storing non-drafting solid fill fallback by name: {}".format(pattern.Id))
                except Exception as e:
                    # Some patterns might throw errors, ignore them
                    # print("# Debug: Error getting fill pattern for {}: {}".format(pattern.Id, e))
                    pass # Continue searching

        # If drafting solid fill wasn't found by name, use the stored fallback if available
        if solid_fill_pattern_id == DB.ElementId.InvalidElementId and temp_solid_fill_id != DB.ElementId.InvalidElementId:
            solid_fill_pattern_id = temp_solid_fill_id
            # print("# Debug: Using non-Drafting solid fill pattern found by name.")

        # Second pass: If still not found, check IsSolidFill
        if solid_fill_pattern_id == DB.ElementId.InvalidElementId:
            print("# Warning: Could not find a '{}' pattern by name. Falling back to IsSolidFill check.".format(solid_fill_pattern_name))
            drafting_solid_fallback_id = DB.ElementId.InvalidElementId
            model_solid_fallback_id = DB.ElementId.InvalidElementId
            # Re-iterate or use the existing collector if performance is critical
            fill_pattern_collector_pass2 = DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement).WhereElementIsNotElementType()
            for pattern in fill_pattern_collector_pass2:
                try:
                    fill_patt = pattern.GetFillPattern()
                    # Check if the pattern object is valid and if it's a solid fill
                    if fill_patt and fill_patt.IsSolidFill:
                        if fill_patt.Target == DB.FillPatternTarget.Drafting:
                             if drafting_solid_fallback_id == DB.ElementId.InvalidElementId: # Store the first one found
                                 drafting_solid_fallback_id = pattern.Id
                                 # print("# Debug: Storing Drafting solid fill fallback via IsSolidFill: {}".format(pattern.Id))
                        elif fill_patt.Target == DB.FillPatternTarget.Model:
                             if model_solid_fallback_id == DB.ElementId.InvalidElementId: # Store the first one found
                                 model_solid_fallback_id = pattern.Id
                                 # print("# Debug: Storing Model solid fill fallback via IsSolidFill: {}".format(pattern.Id))

                        # If we found both, we can stop early if desired, but iterating through all is safer
                        # if drafting_solid_fallback_id != DB.ElementId.InvalidElementId and model_solid_fallback_id != DB.ElementId.InvalidElementId:
                        #    break

                except Exception as e:
                    # Some patterns might throw errors on GetFillPattern(), ignore them
                    # print("# Debug: Error getting fill pattern for {}: {}".format(pattern.Id, e))
                    pass

            # Prioritize Drafting, then Model
            if drafting_solid_fallback_id != DB.ElementId.InvalidElementId:
                solid_fill_pattern_id = drafting_solid_fallback_id
                # print("# Debug: Using Drafting solid fill found via IsSolidFill.")
            elif model_solid_fallback_id != DB.ElementId.InvalidElementId:
                solid_fill_pattern_id = model_solid_fallback_id
                # print("# Debug: Using Model solid fill found via IsSolidFill.")
            else:
                print("# Warning: Could not find ANY 'Solid fill' pattern element using Name or IsSolidFill. Color override will be applied without explicit pattern ID.")

        # --- Create Override Settings ---
        override_settings = DB.OverrideGraphicSettings()

        # Set Cut Fill Pattern Colors to Black
        override_settings.SetCutForegroundPatternColor(override_color)
        # override_settings.SetCutBackgroundPatternColor(override_color) # Optional: Set background too

        # Set Cut Fill Pattern Visibility to True
        override_settings.SetCutForegroundPatternVisible(True)
        # override_settings.SetCutBackgroundPatternVisible(False) # Typically background is hidden for solid fill override

        # Set Cut Fill Pattern to Solid Fill if found
        if solid_fill_pattern_id != DB.ElementId.InvalidElementId:
            override_settings.SetCutForegroundPatternId(solid_fill_pattern_id)
            # override_settings.SetCutBackgroundPatternId(DB.ElementId.InvalidElementId) # Ensure background pattern is cleared
            # print("# Debug: Using solid fill pattern ID: {}".format(solid_fill_pattern_id))
        # else: # If no solid pattern ID found, the color settings alone will often make it appear solid.
            # pass # No action needed if pattern ID not found

        # --- Create Filter for Wall Function ---
        # The 'Function' parameter (WALL_FUNCTION_PARAM) stores an integer.
        # WallFunction enum: Exterior(0), Interior(1), Retaining(2), Soffit(3), Foundation(4), CoreShaft(5)

        function_param_id = DB.ElementId.InvalidElementId
        try:
            # Standard way to get BuiltInParameter enum value
            wall_function_bip_value = DB.BuiltInParameter.WALL_FUNCTION_PARAM
            function_param_id = DB.ElementId(wall_function_bip_value)
        except AttributeError:
            print("# Warning: Direct access to BuiltInParameter 'WALL_FUNCTION_PARAM' failed. Trying System.Enum.Parse...")
            try:
                # Alternative way using System.Enum.Parse - requires clr.AddReference('System') and import System
                bip_enum_type = clr.GetClrType(DB.BuiltInParameter)
                wall_function_bip_value = System.Enum.Parse(bip_enum_type, "WALL_FUNCTION_PARAM")
                # Ensure the parsed value is converted to the correct integer type if needed,
                # but ElementId constructor should handle the enum value directly.
                function_param_id = DB.ElementId(wall_function_bip_value)
                print("# Info: Successfully obtained WALL_FUNCTION_PARAM using System.Enum.Parse.")
            except Exception as e:
                print("# Error: Failed to get ElementId for WALL_FUNCTION_PARAM using System.Enum.Parse. Cannot create filter. Error: {}".format(e))
                # function_param_id remains InvalidElementId

        # --- Collect and Filter Walls only if parameter ID was found ---
        walls_overridden_count = 0
        if function_param_id != DB.ElementId.InvalidElementId:
            pvp = DB.ParameterValueProvider(function_param_id)
            # Using FilterIntegerRule which is specifically designed for integer comparisons
            # Using DB.FilterNumericEquals() ensures clarity
            filter_rule = DB.FilterIntegerRule(pvp, DB.FilterNumericEquals(), target_wall_function_value)
            param_filter = DB.ElementParameterFilter(filter_rule)

            # --- Collect and Filter Walls in the Active View ---
            wall_collector = DB.FilteredElementCollector(doc, active_view.Id)\
                             .OfCategory(DB.BuiltInCategory.OST_Walls)\
                             .WhereElementIsNotElementType()\
                             .WherePasses(param_filter) # Apply the parameter filter

            walls_to_override = list(wall_collector)

            # --- Apply Overrides ---
            # Note: Assumes transaction is handled externally.
            for wall in walls_to_override:
                # It's good practice to double-check the type, though the collector should handle this
                if isinstance(wall, DB.Wall):
                    try:
                        # Apply the override to this specific wall element in the active view
                        active_view.SetElementOverrides(wall.Id, override_settings)
                        walls_overridden_count += 1
                    except Exception as e:
                        # Log errors for individual elements but continue processing others
                        print("# Error applying override to Wall {}: {}".format(wall.Id, e))

            # Provide feedback to the user
            if walls_overridden_count > 0:
                print("# Applied black solid fill cut pattern override to {} Wall(s) with Function='Core Shaft' in the active view '{}'.".format(walls_overridden_count, active_view.Name))
            else:
                print("# No Wall elements found with Function='Core Shaft' in the active view '{}' to apply overrides.".format(active_view.Name))
        else:
            print("# Error: Could not determine ElementId for WALL_FUNCTION_PARAM. Aborting override process.")