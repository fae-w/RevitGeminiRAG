# Purpose: This script exports structural column 'Mark' parameters and intersecting grid names to a CSV file.

﻿import clr
import System

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    Grid,
    ElementIntersectsElementFilter,
    BuiltInParameter,
    ElementId,
    Element
)

# List to hold CSV lines
csv_lines = []
# Add header row
csv_lines.append('"Mark","Intersecting Grids"')

# Collect all Structural Column instances
col_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType()
columns = list(col_collector) # Convert to list

# Check if any columns exist
if not columns:
    print("# No Structural Column elements found in the project.")
else:
    processed_count = 0
    # Iterate through columns
    for column in columns:
        # Ensure it's a FamilyInstance (though category filter should handle this)
        if not isinstance(column, FamilyInstance):
            continue

        try:
            # 1. Get Mark parameter
            mark_param = column.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            mark = mark_param.AsString() if mark_param and mark_param.HasValue else ""
            # Escape quotes for CSV safety
            safe_mark = '"' + mark.replace('"', '""') + '"'

            # 2. Find Intersecting Grids
            intersecting_grid_names = []
            # Create the intersection filter for this specific column
            # Note: ElementIntersectsElementFilter might be slow on large models with many grids.
            # Consider spatial filtering first if performance is an issue.
            intersect_filter = ElementIntersectsElementFilter(column)

            # Apply the filter to find intersecting grids
            # It's generally more efficient to filter grids once and then apply intersection check,
            # but for simplicity here, we run the collector per column.
            intersecting_grids_collector = FilteredElementCollector(doc)\
                                            .OfCategory(BuiltInCategory.OST_Grids)\
                                            .WhereElementIsNotElementType()\
                                            .WherePasses(intersect_filter)

            for grid in intersecting_grids_collector:
                if isinstance(grid, Grid):
                    grid_name = Element.Name.__get__(grid) # Use property getter for name
                    if grid_name: # Check if grid has a name
                        intersecting_grid_names.append(grid_name)

            # Sort names alphabetically for consistent output
            intersecting_grid_names.sort()

            # Format grid names list as a single comma-separated string
            grids_string = ",".join(intersecting_grid_names)
            # Escape quotes for CSV safety
            safe_grids_string = '"' + grids_string.replace('"', '""') + '"'

            # 3. Add data row to CSV list
            csv_lines.append(','.join([safe_mark, safe_grids_string]))
            processed_count += 1

        except System.Exception as e:
            # Optional: Log errors for debugging specific columns
            # print("# Error processing Column ID {}: {}".format(column.Id.ToString(), e))
            pass # Silently skip columns that cause errors

    # Final Output Generation
    # Check if we gathered any data beyond the header
    if len(csv_lines) > 1:
        file_content = "\n".join(csv_lines)
        print("EXPORT::CSV::structural_column_grid_intersections.csv")
        print(file_content)
    elif len(columns) > 0: # Columns found, but none processed or no intersections found
         print("# Found {} columns, but no intersecting grids identified or errors occurred during processing.".format(len(columns)))
    # If no columns were found initially, the first message handles it.