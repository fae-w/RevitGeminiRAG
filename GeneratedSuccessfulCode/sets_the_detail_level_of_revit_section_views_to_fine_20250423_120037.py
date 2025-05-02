# Purpose: This script sets the detail level of Revit section views to 'Fine'.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, View, ViewType, ViewDetailLevel, BuiltInCategory
import System

# Define the target detail level
target_detail_level = ViewDetailLevel.Fine

# Collect all View elements in the document
view_collector = FilteredElementCollector(doc).OfClass(View)

# Counter for modified views and skipped views
modified_count = 0
skipped_count = 0
error_count = 0

# Iterate through the views
for view in view_collector:
    # Check if it's a Section view
    if view.ViewType == ViewType.Section:
        try:
            # Check if the view supports setting Detail Level and it can be modified
            # Note: View Templates often restrict modification.
            if view.CanModifyDetailLevel():
                # Check if the current detail level is already the target level
                if view.DetailLevel != target_detail_level:
                    # Set the detail level
                    view.DetailLevel = target_detail_level
                    modified_count += 1
                # else:
                    # Optional: Note if already set
                    # print(f"# View '{view.Name}' (ID: {view.Id}) is already set to Fine.")
            else:
                # Optional: Note if view cannot be modified (e.g., locked by template)
                # print(f"# Skipping view '{view.Name}' (ID: {view.Id}) - Detail Level cannot be modified (likely due to a View Template).")
                skipped_count += 1
        except System.Exception as e:
            # Log errors for specific views if needed
            # print(f"# Error processing view '{view.Name}' (ID: {view.Id}): {e}")
            error_count += 1
            pass # Continue with the next view

# Optional: Print summary (commented out by default to meet output constraints)
# print("# Processing complete.")
# print("# Successfully modified {0} Section views to Fine detail level.".format(modified_count))
# print("# Skipped {0} Section views (Detail Level likely controlled by View Template).".format(skipped_count))
# if error_count > 0:
#    print("# Encountered errors while processing {0} views.".format(error_count))

# If no views were modified or skipped (e.g., no section views in project)
# if modified_count == 0 and skipped_count == 0 and error_count == 0:
#    print("# No Section views found in the project.")