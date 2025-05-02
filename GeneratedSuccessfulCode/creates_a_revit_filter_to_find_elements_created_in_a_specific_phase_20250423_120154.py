# Purpose: This script creates a Revit filter to find elements created in a specific phase.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Phase,
    ElementId,
    ElementPhaseStatusFilter,
    ElementOnPhaseStatus
)

# --- Configuration ---
target_phase_name = "Phase 1"
# --- End Configuration ---

# Find the target Phase ElementId
target_phase_id = ElementId.InvalidElementId
phase_collector = FilteredElementCollector(doc).OfClass(Phase)
for phase in phase_collector:
    # Phase names are stored in the element's Name property
    if phase.Name == target_phase_name:
        target_phase_id = phase.Id
        break

phase_filter = None # Initialize filter variable

if target_phase_id != ElementId.InvalidElementId:
    # Define the status for elements CREATED in the target phase
    # This is the 'New' status relative to the specified phase.
    statuses_to_find = List[ElementOnPhaseStatus]()
    statuses_to_find.Add(ElementOnPhaseStatus.New)

    # Create the phase status filter
    # The 'inverted' parameter is False because we want elements matching the specified status (New)
    try:
        phase_filter = ElementPhaseStatusFilter(target_phase_id, statuses_to_find, False)
        print("# Successfully created ElementPhaseStatusFilter for elements created in phase '{{0}}' (ID: {{1}})".format(target_phase_name, target_phase_id))
        # Example of using the filter (optional):
        # collector = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(phase_filter)
        # elements_created_in_phase = collector.ToElements()
        # print("# Found {{0}} elements created in '{{1}}'.".format(len(elements_created_in_phase), target_phase_name))

    except Exception as e:
        print("# Error creating ElementPhaseStatusFilter: {{0}}".format(e))

else:
    print("# Error: Phase named '{{0}}' not found in the document. Cannot create filter.".format(target_phase_name))

# The variable 'phase_filter' now holds the created filter object if successful, otherwise it is None.
# This filter can be used with FilteredElementCollector like:
# if phase_filter:
#     collector = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(phase_filter)
#     # ... process collected elements ...