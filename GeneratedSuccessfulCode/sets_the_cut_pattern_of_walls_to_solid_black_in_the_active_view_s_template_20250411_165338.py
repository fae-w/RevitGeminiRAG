# Purpose: This script sets the cut pattern of walls to solid black in the active view's template.

﻿# Purpose: This script sets the cut pattern of walls to solid black in the active view's template.

# Import necessary classes
import clr
# No explicit need for List here, but keeping clr import is safe practice
# clr.AddReference('System.Collections')
# from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ElementId,
    OverrideGraphicSettings, Color, FillPatternElement, FillPatternTarget,
    View
)

# Get the active view
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active graphical view found.")
else:
    # Check if the active view has a View Template applied
    template_id = active_view.ViewTemplateId
    if template_id is None or template_id == ElementId.InvalidElementId:
        print("# Error: The active view does not have a View Template applied.")
    else:
        # Get the View Template element (which is also a View)
        template_view = doc.GetElement(template_id)
        if not template_view or not isinstance(template_view, View):
            print("# Error: Could not retrieve the View Template element.")
        else:
            # Find the "Solid fill" pattern ElementId (Drafting target preferred)
            solid_fill_pattern_id = ElementId.InvalidElementId
            fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
            for pattern_elem in fill_pattern_collector:
                try:
                    fill_pattern = pattern_elem.GetFillPattern()
                    # Ensure it's a Drafting pattern and solid fill
                    if fill_pattern.IsSolidFill and fill_pattern.Target == FillPatternTarget.Drafting:
                        solid_fill_pattern_id = pattern_elem.Id
                        break # Found the preferred pattern
                except Exception:
                    # Some patterns might cause issues, skip them
                    pass

            # Fallback: if no Drafting solid fill found, try any solid fill
            if solid_fill_pattern_id == ElementId.InvalidElementId:
                for pattern_elem in fill_pattern_collector:
                     try:
                         fill_pattern = pattern_elem.GetFillPattern()
                         if fill_pattern.IsSolidFill:
                             solid_fill_pattern_id = pattern_elem.Id
                             # print("# Warning: Using a non-Drafting solid fill pattern as fallback.") # Optional warning
                             break # Found any solid fill
                     except Exception:
                         pass

            if solid_fill_pattern_id == ElementId.InvalidElementId:
                print("# Error: Could not find any 'Solid fill' pattern in the project.")
            else:
                # Define the color black
                black_color = Color(0, 0, 0)

                # Get the category ID for Walls
                walls_category_id = ElementId(BuiltInCategory.OST_Walls)

                # Get the current override settings for the Walls category from the template
                # This method returns default settings if no specific overrides exist yet.
                override_settings = template_view.GetCategoryOverrides(walls_category_id)
                if override_settings is None:
                     # This case is unlikely based on API docs, but included for safety
                     override_settings = OverrideGraphicSettings()
                     # print("# Warning: GetCategoryOverrides returned None unexpectedly. Creating new settings.")

                # Modify the Cut Pattern settings
                override_settings.SetCutForegroundPatternVisible(True)
                override_settings.SetCutForegroundPatternId(solid_fill_pattern_id)
                override_settings.SetCutForegroundPatternColor(black_color)

                # Ensure cut background pattern is not interfering (set invisible)
                override_settings.SetCutBackgroundPatternVisible(False)
                # Optionally reset background pattern ID and color if needed
                # override_settings.SetCutBackgroundPatternId(ElementId.InvalidElementId)
                # override_settings.SetCutBackgroundPatternColor(Color.InvalidColorValue)

                # Apply the modified overrides back to the Walls category in the View Template
                # The script runs within an external transaction (C# wrapper), so no transaction management here.
                try:
                    template_view.SetCategoryOverrides(walls_category_id, override_settings)
                    # print(f"# Successfully updated Wall cut pattern overrides in View Template: {{template_view.Name}}") # Optional success message
                except Exception as e:
                    print(f"# Error applying category overrides to the view template: {{e}}") # Escaped f-string