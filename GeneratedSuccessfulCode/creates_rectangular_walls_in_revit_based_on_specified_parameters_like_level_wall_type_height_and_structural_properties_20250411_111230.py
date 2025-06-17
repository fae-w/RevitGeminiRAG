# Purpose: This script creates rectangular walls in Revit based on specified parameters like level, wall type, height, and structural properties.

# Purpose: This script creates a rectangular wall using lines in Revit, specifying level, type, height, and structural properties.

﻿import clr
clr.AddReference('RevitAPI')
# clr.AddReference('RevitAPIUI') # Not strictly needed for this task but often useful

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Wall, WallType, Level, XYZ, Line, ElementId, WallKind

# --- Assumptions ---
# Define corner points for the rectangle (in decimal feet)
p1 = XYZ(0, 0, 0)
p2 = XYZ(20, 0, 0)
p3 = XYZ(20, 10, 0)
p4 = XYZ(0, 10, 0)

# Define wall height (in decimal feet)
wall_height = 10.0

# Define wall offset from base level (in decimal feet)
base_offset = 0.0

# Specify if the walls should be structural
is_structural = False

# Specify if the wall orientation should be flipped
flip_wall = False
# --- End Assumptions ---

# Find the first available Level
level_collector = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()
first_level = level_collector.FirstElement()

if not first_level:
    print("# Error: No Levels found in the document. Cannot create walls.")
else:
    level_id = first_level.Id

    # Find the first available basic WallType
    wall_type_collector = FilteredElementCollector(doc).OfClass(WallType).WhereElementIsElementType()
    first_wall_type = None
    # Iterate using .ToElements() for safety or directly if collector is small/guaranteed
    for wt in wall_type_collector: # Direct iteration is usually fine for WallTypes
        if wt.Kind == WallKind.Basic: # Ensure it's a basic wall type
             first_wall_type = wt
             break

    if not first_wall_type:
        print("# Error: No suitable Basic WallTypes found in the document. Cannot create walls.")
    else:
        wall_type_id = first_wall_type.Id

        # Create the lines for the rectangle
        line1 = Line.CreateBound(p1, p2)
        line2 = Line.CreateBound(p2, p3)
        line3 = Line.CreateBound(p3, p4)
        line4 = Line.CreateBound(p4, p1)

        lines = [line1, line2, line3, line4]
        created_walls = []

        # Create the walls using the overload specifying height
        # IMPORTANT: Assumes a Transaction is already started by the calling environment
        try:
            for line in lines:
                # Use Wall.Create(Document, Curve, ElementId wallTypeId, ElementId levelId, double height, double offset, bool flip, bool structural)
                # Note: Revit API requires height in internal units (decimal feet)
                new_wall = Wall.Create(doc, line, wall_type_id, level_id, wall_height, base_offset, flip_wall, is_structural)
                if new_wall:
                    created_walls.append(new_wall.Id)
            # Optional: Print success message (uncomment if needed)
            # print("# Successfully created {} walls forming a rectangle.".format(len(created_walls)))
        except Exception as e:
            # Provide a more informative error message
            import traceback
            print("# Error creating walls: {}".format(e))
            # print(traceback.format_exc()) # Uncomment for detailed stack trace if needed