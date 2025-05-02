# Purpose: This script lists the names of all Wall Types found in the Revit project.

# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, WallType

# Get all WallType elements in the document
collector = FilteredElementCollector(doc).OfClass(WallType)
wall_types = list(collector) # Convert iterator to list to easily check count and iterate

# Check if any wall types were found
if wall_types:
    print("Wall Types found in project:")
    # Iterate through the collected wall types and print their names
    for wall_type in wall_types:
        if isinstance(wall_type, WallType):
            try:
                # Print the name of the wall type
                print("- {}".format(wall_type.Name))
            except Exception as e:
                # Optional: Log error for specific wall type if needed
                # print("# Error accessing name for WallType ID {}: {}".format(wall_type.Id, e))
                pass # Silently ignore types that might cause issues
else:
    print("# No Wall Types found in the project.")