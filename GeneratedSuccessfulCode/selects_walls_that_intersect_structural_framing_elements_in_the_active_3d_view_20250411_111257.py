# Purpose: This script selects walls that intersect structural framing elements in the active 3D view.

# Purpose: This script selects walls that intersect structural framing elements in the active 3D view of a Revit model.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections') # Required for List<T>

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Wall,
    ElementId,
    ElementIntersectsElementFilter,
    LogicalOrFilter,
    ElementFilter, # Required for List<ElementFilter>
    View3D,
    Element # For type checking/verification if needed
)

# Get the active view
active_view = uidoc.ActiveView

# Check if the active view is a 3D view
if not active_view or not isinstance(active_view, View3D):
    print("# Error: The active view is not a 3D view. Script terminated.")
else:
    active_view_id = active_view.Id

    # Collect Structural Framing elements visible in the active 3D view
    # Assumption: User wants elements whose geometry is visible/relevant in this view
    framing_collector = FilteredElementCollector(doc, active_view_id)\
                        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
                        .WhereElementIsNotElementType()
    framing_elements = list(framing_collector) # Convert to list for iteration

    intersecting_wall_ids = List[ElementId]() # Initialize as empty .NET List

    if not framing_elements:
        print("# No Structural Framing elements found in the active 3D view.")
    else:
        intersection_filters = List[ElementFilter]()
        skipped_framing_count = 0

        # Create intersection filters for each valid framing element
        for framing_element in framing_elements:
            try:
                # Basic validity check - ensures element exists and has a category.
                # More complex checks (e.g., has solid geometry) could be added but might slow down significantly.
                if framing_element and framing_element.IsValidObject and framing_element.Category:
                     # Attempt to create the filter. This might fail for elements without suitable geometry.
                     intersect_filter = ElementIntersectsElementFilter(framing_element)
                     intersection_filters.Add(intersect_filter)
                else:
                    skipped_framing_count += 1
            except Exception as e:
                # Catch exceptions during filter creation (e.g., element not supported)
                # print("# Warning: Could not create intersection filter for element {}. Skipping. Error: {}".format(framing_element.Id, e)) # Optional debug msg
                skipped_framing_count += 1
                continue

        # Report if any framing elements were skipped
        # if skipped_framing_count > 0:
        #      print("# Info: Skipped {} Structural Framing elements unsuitable for intersection checks.".format(skipped_framing_count))

        if intersection_filters.Count > 0:
            # Combine all individual intersection filters with OR logic.
            # This means a wall will be selected if it intersects *any* of the valid framing elements.
            # Using LogicalOrFilter is generally more efficient than multiple separate queries or Python-side loops.
            combined_filter = LogicalOrFilter(intersection_filters)

            # Collect Walls visible in the active 3D view that pass the combined intersection filter
            wall_collector = FilteredElementCollector(doc, active_view_id)\
                            .OfCategory(BuiltInCategory.OST_Walls)\
                            .WhereElementIsNotElementType()\
                            .WherePasses(combined_filter)

            # Get the IDs of the intersecting walls directly from the collector
            intersecting_wall_ids_collection = wall_collector.ToElementIds() # Returns ICollection<ElementId>

            # Ensure it's a List<ElementId> for SetElementIds
            final_selection_ids = List[ElementId](intersecting_wall_ids_collection)

            if final_selection_ids.Count > 0:
                try:
                    # Set the selection in the UI
                    uidoc.Selection.SetElementIds(final_selection_ids)
                    # print("# Selected {} walls intersecting Structural Framing in the active 3D view.".format(final_selection_ids.Count)) # Optional confirmation
                except Exception as sel_ex:
                    print("# Error setting selection: {}".format(sel_ex))
            else:
                print("# No walls found intersecting the specified Structural Framing elements in the active 3D view.")
        else:
            # This case occurs if framing elements were found, but none were suitable for creating filters.
            print("# No valid Structural Framing elements found to create intersection filters.")