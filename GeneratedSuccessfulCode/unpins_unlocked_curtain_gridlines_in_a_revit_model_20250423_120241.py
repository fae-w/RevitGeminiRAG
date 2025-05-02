# Purpose: This script unpins unlocked Curtain Gridlines in a Revit model.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
import System # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    CurtainGridLine,
    Element,
    ElementId # Though not strictly needed for this logic, good practice
)

# --- Script Core Logic ---

unpinned_count = 0
processed_count = 0
error_count = 0

# Collect all CurtainGridLine elements in the document
collector = FilteredElementCollector(doc).OfClass(CurtainGridLine)

# Iterate through each CurtainGridLine
for cgl in collector:
    processed_count += 1
    try:
        # Check if the grid line is currently pinned
        is_pinned = cgl.Pinned

        # Check if the grid line is currently locked
        # Assumption: Locked grid lines are considered "perimeter" or otherwise protected
        # and should not be unpinned according to the request.
        is_locked = cgl.Lock

        # If the grid line is pinned AND it is NOT locked, unpin it
        if is_pinned and not is_locked:
            cgl.Pinned = False
            unpinned_count += 1

    except System.Exception as e:
        # Log errors for specific elements if needed (optional)
        # print("# Error processing CurtainGridLine ID {}: {}".format(cgl.Id, e))
        error_count += 1
        pass # Continue with the next element even if one fails

# Optional: Print a summary message
# print("# Processed {} Curtain Grid Lines.".format(processed_count))
# print("# Unpinned {} interior (non-locked) Curtain Grid Lines.".format(unpinned_count))
# if error_count > 0:
#    print("# Encountered errors processing {} grid lines.".format(error_count))

# Final check print statement (optional but can be helpful for confirmation)
# if unpinned_count > 0:
#     print("# Successfully unpinned {} interior/unlocked curtain grid lines.".format(unpinned_count))
# elif processed_count > 0:
#     print("# No pinned interior/unlocked curtain grid lines found to unpin.")
# else:
#     print("# No curtain grid lines found in the document.")