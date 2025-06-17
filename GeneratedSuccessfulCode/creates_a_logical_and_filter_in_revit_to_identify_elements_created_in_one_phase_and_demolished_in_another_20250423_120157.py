# Purpose: This script creates a logical AND filter in Revit to identify elements created in one phase and demolished in another.

﻿# Imports
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Phase,
    ElementId,
    ParameterFilterRuleFactory,
    FilterElementIdRule,
    ElementParameterFilter,
    LogicalAndFilter,
    BuiltInParameter
)

# --- Configuration ---
phase1_name = "Phase 1"  # Phase where elements are created
phase2_name = "Phase 2"  # Phase where elements are demolished
# --- End Configuration ---

# Function to find Phase ElementId by name
def find_phase_id(doc, phase_name):
    collector = FilteredElementCollector(doc).OfClass(Phase)
    found_phase = None
    for phase in collector:
        try:
            if phase.Name == phase_name:
                found_phase = phase
                break
        except:
            pass # Handle potential issues accessing Name property
    if found_phase:
        return found_phase.Id
    return ElementId.InvalidElementId

# Find Phase ElementIds
phase1_id = find_phase_id(doc, phase1_name)
phase2_id = find_phase_id(doc, phase2_name)

combined_filter = None # Initialize filter variable
error_messages = []
phases_ok = True

# Validate Phases
if phase1_id == ElementId.InvalidElementId:
    error_messages.append("# Error: Phase named '{}' not found.".format(phase1_name))
    phases_ok = False
if phase2_id == ElementId.InvalidElementId:
    error_messages.append("# Error: Phase named '{}' not found.".format(phase2_name))
    phases_ok = False

if not phases_ok:
    for msg in error_messages:
        print(msg)
else:
    try:
        # 1. Create filter rule for 'Phase Created' = Phase 1
        created_rule = ParameterFilterRuleFactory.CreateEqualsRule(BuiltInParameter.PHASE_CREATED, phase1_id)
        created_filter = ElementParameterFilter(created_rule)

        # 2. Create filter rule for 'Phase Demolished' = Phase 2
        # Ensure the phase ID is valid before creating the rule
        # Note: PHASE_DEMOLISHED might be invalidElementId for elements not demolished
        # We specifically want elements where it IS phase2_id
        demolished_rule = ParameterFilterRuleFactory.CreateEqualsRule(BuiltInParameter.PHASE_DEMOLISHED, phase2_id)
        demolished_filter = ElementParameterFilter(demolished_rule)

        # 3. Combine the filters with a Logical AND
        filter_list = List[ElementFilter]()
        filter_list.Add(created_filter)
        filter_list.Add(demolished_filter)
        combined_filter = LogicalAndFilter(filter_list)

        print("# Successfully generated LogicalAndFilter.")
        print("# This filter identifies elements with:")
        print("# - PHASE_CREATED = '{}' (ID: {})".format(phase1_name, phase1_id))
        print("# - PHASE_DEMOLISHED = '{}' (ID: {})".format(phase2_name, phase2_id))
        print("# To use this filter to hide elements:")
        print("# 1. Create a ParameterFilterElement using this filter logic.")
        print("# 2. Add the ParameterFilterElement to a view's Visibility/Graphics Overrides.")
        print("# 3. Set the visibility for that filter to 'Off' in the view.")

        # Optional: Example of using the filter (uncomment to test)
        # collector = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(combined_filter)
        # elements_found = collector.ToElements()
        # print("# Found {} elements matching the criteria.".format(len(elements_found)))

    except Exception as e:
        print("# Error creating the combined filter: {}".format(e))

# The variable 'combined_filter' holds the created LogicalAndFilter object if successful, otherwise it is None.
# This filter can be used with FilteredElementCollector or to create a ParameterFilterElement.