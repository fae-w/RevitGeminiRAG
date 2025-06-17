# Purpose: This script sets the detail level of specific Revit elevation views to 'Fine'.

# Purpose: This script sets the detail level of elevation views in Revit to 'Fine', but only for views whose names start with a specified prefix and whose detail level can be modified.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, View, ViewType, ViewDetailLevel, BuiltInCategory

# Define the target detail level
target_detail_level = ViewDetailLevel.Fine
target_prefix = "Exterior"

# Collect all View elements in the document
view_collector = FilteredElementCollector(doc).OfClass(View)

# Counter for modified views
modified_count = 0
error_count = 0

# Iterate through the views
for view in view_collector:
    # Check if it's an Elevation view and the name matches
    if view.ViewType == ViewType.Elevation and view.Name.startswith(target_prefix):
        try:
            # Check if the view supports setting Detail Level
            if view.CanModifyDetailLevel(): # More direct check than HasDetailLevel + IsModifiable
                # Check if the current detail level is already the target level
                if view.DetailLevel != target_detail_level:
                    # Set the detail level
                    view.DetailLevel = target_detail_level
                    modified_count += 1
            # else:
                # Optional: Print if view cannot be modified (e.g., locked template)
                # print(f"# Skipping view '{view.Name}' (ID: {view.Id}) - Detail Level cannot be modified.")
        except Exception as e:
            # Log errors for specific views if needed
            # print(f"# Error processing view '{view.Name}' (ID: {view.Id}): {e}")
            error_count += 1
            pass # Continue with the next view

# Optional: Print summary (commented out by default)
# print(f"# Successfully modified {modified_count} elevation views starting with '{target_prefix}' to Fine detail level.")
# if error_count > 0:
#    print(f"# Encountered errors while processing {error_count} views.")