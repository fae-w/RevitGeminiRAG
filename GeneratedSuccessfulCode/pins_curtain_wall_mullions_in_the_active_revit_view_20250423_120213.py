# Purpose: This script pins curtain wall mullions in the active Revit view.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Mullion

# Get the active view
active_view = doc.ActiveView
pinned_count = 0
already_pinned_count = 0
error_count = 0

if active_view:
    # Create a collector for the active view
    collector = FilteredElementCollector(doc, active_view.Id)

    # Filter for mullion instances in the active view
    mullion_collector = collector.OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType()

    # Iterate through mullions and pin them
    for mullion in mullion_collector:
        # Ensure it's a Mullion instance (though the filter should handle this)
        if isinstance(mullion, Mullion):
            try:
                # Check if the mullion is already pinned
                if not mullion.Pinned:
                    # Pin the mullion
                    mullion.Pinned = True
                    pinned_count += 1
                else:
                    already_pinned_count += 1
            except Exception as e:
                # Log errors if pinning fails for any reason
                print("# Error pinning Mullion ID {}: {}".format(mullion.Id, e))
                error_count += 1
        else:
             # This case should ideally not happen due to the filter
             print("# Warning: Found non-Mullion element with ID {} in Mullion collector.".format(mullion.Id))


    # Print summary
    print("# Successfully pinned {} new mullions.".format(pinned_count))
    print("# Found {} mullions already pinned.".format(already_pinned_count))
    if error_count > 0:
        print("# Failed to pin {} mullions due to errors.".format(error_count))

else:
    # Handle case where there is no active view
    print("# Error: No active view found. Cannot pin mullions.")