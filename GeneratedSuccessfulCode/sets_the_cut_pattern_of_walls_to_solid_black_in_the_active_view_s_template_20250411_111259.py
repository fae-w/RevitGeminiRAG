# Purpose: This script sets the cut pattern of walls to solid black in the active view's template.

# Purpose: This script sets the cut pattern of walls to solid black in the active view's template.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List # Although not directly used, good practice if dealing with collections
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
    if template_id == ElementId.InvalidElementId:
        print("# Error: The active view does not have a View Template applied.")
    else:
        # Get the View Template element (which is also a View)
        template_view = doc.GetElement(template_id)
        if not template_view or not isinstance(template_view, View):
            print("# Error: Could not retrieve the View Template element.")
        else:
            # Find the "Solid fill" pattern ElementId
            solid_fill_pattern_id = ElementId.InvalidElementId
            fill_pattern_collector = FilteredElementCollector(doc).OfClass(FillPatternElement)
            for pattern_elem in fill_pattern_collector:
                fill_pattern = pattern_elem.GetFillPattern()
                if fill_pattern.IsSolidFill and fill_pattern.Target == FillPatternTarget.Drafting:
                    solid_fill_pattern_id = pattern_elem.Id
                    break # Found it

            if solid_fill_pattern_id == ElementId.InvalidElementId:
                print("# Error: Could not find a 'Solid fill' drafting pattern in the project.")
            else:
                # Define the color black
                black_color = Color(0, 0, 0)

                # Get the category ID for Walls
                walls_category_id = ElementId(BuiltInCategory.OST_Walls)

                # Get the current override settings for the Walls category from the template
                # If no specific overrides exist, this creates/returns default settings
                override_settings = template_view.GetCategoryOverrides(walls_category_id)
                if override_settings is None: # Should not happen based on API docs, but check just in case
                    override_settings = OverrideGraphicSettings() # Create new if somehow null

                # Modify the Cut Pattern settings
                override_settings.SetCutForegroundPatternVisible(True)
                override_settings.SetCutForegroundPatternId(solid_fill_pattern_id)
                override_settings.SetCutForegroundPatternColor(black_color)

                # Optional: Ensure cut background pattern is not interfering (usually default is not visible)
                override_settings.SetCutBackgroundPatternVisible(False)

                # Apply the modified overrides back to the Walls category in the View Template
                try:
                    template_view.SetCategoryOverrides(walls_category_id, override_settings)
                    # print(f"# Successfully updated Wall cut pattern overrides in View Template: {template_view.Name}") # Optional output
                except Exception as e:
                    print(f"# Error applying category overrides to the view template: {e}") # Escaped f-string