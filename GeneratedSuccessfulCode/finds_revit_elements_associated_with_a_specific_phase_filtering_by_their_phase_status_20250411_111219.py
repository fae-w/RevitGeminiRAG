# Purpose: This script finds Revit elements associated with a specific phase, filtering by their phase status.

# Purpose: This script collects all Revit elements associated with a specific phase, filtering by their phase status (New or Existing).

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
target_phase_name = "Phase 2"
# --- End Configuration ---

# Find the target Phase ElementId
target_phase_id = ElementId.InvalidElementId
phase_collector = FilteredElementCollector(doc).OfClass(Phase)
for phase in phase_collector:
    # Phase names are stored in the element's Name property
    if phase.Name == target_phase_name:
        target_phase_id = phase.Id
        break

found_element_ids = []

if target_phase_id != ElementId.InvalidElementId:
    # Define the statuses that represent elements "existing" or "new" in the target phase
    # This typically covers elements relevant to that phase in standard views.
    statuses_to_find = List[ElementOnPhaseStatus]()
    statuses_to_find.Add(ElementOnPhaseStatus.New)        # Created in this phase
    statuses_to_find.Add(ElementOnPhaseStatus.Existing)   # Created in a previous phase, not demolished yet

    # Create the phase status filter
    # False for inverted means we *want* elements matching the specified statuses
    phase_status_filter = ElementPhaseStatusFilter(target_phase_id, statuses_to_find, False)

    # Collect all elements (excluding element types and view-specific elements potentially)
    # Passing ElementId.InvalidElementId gets all model elements
    collector = FilteredElementCollector(doc)
    elements_in_phase = collector.WhereElementIsNotElementType().WherePasses(phase_status_filter).ToElements()

    # Store the IDs of the found elements
    found_element_ids = [el.Id for el in elements_in_phase]

    # Optional: Print the count of elements found
    print("# Found {0} elements assigned to phase '{1}' (Status: New or Existing)".format(len(found_element_ids), target_phase_name))

    # Optional: Select the found elements in the UI (uncomment if needed)
    # if found_element_ids:
    #    selection_list = List[ElementId](found_element_ids)
    #    try:
    #        uidoc.Selection.SetElementIds(selection_list)
    #    except Exception as sel_ex:
    #        print("# Error setting selection: {}".format(sel_ex))

else:
    print("# Error: Phase named '{0}' not found in the document.".format(target_phase_name))

# If you wanted ONLY elements CREATED in Phase 2, you would change statuses_to_find:
# statuses_to_find = List[ElementOnPhaseStatus]()
# statuses_to_find.Add(ElementOnPhaseStatus.New)
# phase_status_filter = ElementPhaseStatusFilter(target_phase_id, statuses_to_find, False)
# ... rest of collector ...