# Purpose: This script aligns floor plan viewports on Revit sheets vertically or horizontally.

# Purpose: This script aligns floor plan viewports on sheets either vertically or horizontally.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List, ICollection

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    View,
    ViewType,
    XYZ,
    ElementId,
    BuiltInCategory
)

# --- Alignment Configuration ---
# Set to True to align centers vertically (same X coordinate)
# Set to False to align centers horizontally (same Y coordinate)
ALIGN_VERTICALLY = True
# -----------------------------

# Get all sheets in the document
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()

if not sheets:
    print("# No sheets found in the document.")
else:
    aligned_sheets_count = 0
    total_viewports_aligned = 0

    # Iterate through each sheet
    for sheet in sheets:
        if not isinstance(sheet, ViewSheet):
            continue

        try:
            # Get all viewport IDs on the current sheet
            viewport_ids = sheet.GetAllViewports() # Returns ICollection<ElementId>

            if not viewport_ids or viewport_ids.Count < 2: # Need at least two viewports to align
                # print(f"# Sheet '{sheet.SheetNumber} - {sheet.Name}' has less than two viewports. Skipping.") # Escaped
                continue

            floor_plan_viewports = []
            # Iterate through viewport IDs and get Viewport elements
            for vp_id in viewport_ids:
                viewport = doc.GetElement(vp_id)
                if not isinstance(viewport, Viewport):
                    continue

                # Get the view associated with the viewport
                view = doc.GetElement(viewport.ViewId)
                if not isinstance(view, View):
                    continue

                # Check if the view is a Floor Plan
                if view.ViewType == ViewType.FloorPlan:
                    floor_plan_viewports.append(viewport)

            # Check if there are multiple floor plan viewports to align on this sheet
            if len(floor_plan_viewports) > 1:
                aligned_on_this_sheet = False
                # print(f"# Processing Sheet '{sheet.SheetNumber} - {sheet.Name}': Found {len(floor_plan_viewports)} floor plan viewports.") # Escaped

                # Use the first floor plan viewport found as the alignment reference
                reference_viewport = floor_plan_viewports[0]
                try:
                    reference_center = reference_viewport.GetBoxCenter()
                except Exception as ex_ref_center:
                    # print(f"# Could not get center for reference viewport {reference_viewport.Id} on sheet '{sheet.SheetNumber}'. Error: {ex_ref_center}. Skipping sheet.") # Escaped
                    continue # Skip this sheet if reference center fails

                # Align other floor plan viewports to the reference viewport
                for i in range(1, len(floor_plan_viewports)):
                    vp_to_align = floor_plan_viewports[i]
                    try:
                        current_center = vp_to_align.GetBoxCenter()

                        # Calculate the new center based on the alignment strategy
                        if ALIGN_VERTICALLY:
                            # Align X coordinate to reference, keep current Y and Z
                            new_center = XYZ(reference_center.X, current_center.Y, reference_center.Z) # Keep Ref Z too, usually 0 for sheet coordinates
                        else:
                            # Align Y coordinate to reference, keep current X and Z
                            new_center = XYZ(current_center.X, reference_center.Y, reference_center.Z) # Keep Ref Z too

                        # Check if the position needs changing (avoid unnecessary modifications)
                        if not current_center.IsAlmostEqualTo(new_center, 1e-6): # Use tolerance for floating point comparison
                            vp_to_align.SetBoxCenter(new_center)
                            total_viewports_aligned += 1
                            aligned_on_this_sheet = True
                            # print(f"#   Aligned viewport {vp_to_align.Id} on sheet '{sheet.SheetNumber}'.") # Escaped

                    except Exception as ex_align:
                        # print(f"# Error aligning viewport {vp_to_align.Id} on sheet '{sheet.SheetNumber}'. Error: {ex_align}") # Escaped
                        pass # Continue with the next viewport

                if aligned_on_this_sheet:
                    aligned_sheets_count += 1

        except Exception as ex_sheet:
            # print(f"# Error processing sheet '{sheet.SheetNumber} - {sheet.Name}'. Error: {ex_sheet}") # Escaped
            pass # Continue with the next sheet

    # Optional: Print summary (commented out by default)
    # if total_viewports_aligned > 0:
    #     print(f"# Alignment complete. Aligned {total_viewports_aligned} floor plan viewports across {aligned_sheets_count} sheets.") # Escaped
    # else:
    #     print("# No floor plan viewports needed alignment or no sheets/viewports found matching criteria.") # Escaped