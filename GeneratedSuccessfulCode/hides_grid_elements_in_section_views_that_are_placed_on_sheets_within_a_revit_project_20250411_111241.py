# Purpose: This script hides grid elements in section views that are placed on sheets within a Revit project.

# Purpose: This script hides grid elements in section views placed on sheets within a Revit project.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    View,
    ViewType,
    BuiltInCategory,
    ElementId
)
from System.Collections.Generic import List, HashSet

# Assume 'doc' is pre-defined

# 1. Find all Grid Element IDs in the project
grid_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType()
grid_ids = List[ElementId]()
for grid in grid_collector:
    if grid and grid.IsValidObject:
        grid_ids.Add(grid.Id)

# If no grids exist, there's nothing to hide
if grid_ids.Count == 0:
    # print("# No grid elements found in the project.") # Optional info
    pass # Exit gracefully if no grids exist
else:
    # 2. Find all unique Section View IDs that are placed on sheets
    section_view_ids_on_sheets = HashSet[ElementId]()
    sheet_collector = FilteredElementCollector(doc).OfClass(ViewSheet)

    for sheet in sheet_collector:
        # Ensure sheet is valid before proceeding
        if sheet and sheet.IsValidObject:
            try:
                # GetAllPlacedViews is more direct than iterating viewports
                placed_view_ids = sheet.GetAllPlacedViews()
                for view_id in placed_view_ids:
                    # Check if view_id is valid before getting the element
                    if view_id != ElementId.InvalidElementId:
                        view = doc.GetElement(view_id)
                        # Check if view element exists, is a View, and is a Section view
                        if view and view.IsValidObject and isinstance(view, View) and view.ViewType == ViewType.Section:
                            section_view_ids_on_sheets.Add(view_id)
            except Exception as e:
                # print(f"# Warning: Could not process views for sheet {{{{sheet.Id}}}}. Error: {{{{e}}}}") # Optional debug
                pass # Continue with the next sheet

    # 3. Hide the collected Grid Lines in each identified Section View
    hidden_count = 0
    if section_view_ids_on_sheets.Count > 0:
        for view_id in section_view_ids_on_sheets:
            try:
                section_view = doc.GetElement(view_id)
                # Double-check view validity before attempting to hide
                if section_view and section_view.IsValidObject and isinstance(section_view, View):
                    # Hide the collection of grid IDs in this specific view
                    # The transaction is handled by the external C# wrapper
                    section_view.HideElements(grid_ids)
                    hidden_count += 1 # Count views processed
            except Exception as e:
                # print(f"# Warning: Could not hide grids in view {{{{view_id}}}}. Error: {{{{e}}}}") # Optional debug
                pass # Continue with the next view

        # print(f"# Attempted to hide grids in {{{{hidden_count}}}} section views placed on sheets.") # Optional summary
    # else:
    #    print("# No section views found placed on sheets.") # Optional info
    #    pass