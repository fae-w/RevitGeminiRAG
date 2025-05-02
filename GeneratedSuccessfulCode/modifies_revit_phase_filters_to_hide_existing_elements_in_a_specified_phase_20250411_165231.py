# Purpose: This script modifies Revit phase filters to hide existing elements in a specified phase.

﻿# Imports
import clr
clr.AddReference('System.Collections') # Required for List and HashSet
from System.Collections.Generic import List, HashSet

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Phase,
    ElementId,
    View,
    PhaseFilter,
    BuiltInParameter,
    ElementOnPhaseStatus,
    PhaseStatusPresentation,
    Element # Required for GetElement
)

# --- Configuration ---
# !! IMPORTANT ASSUMPTION !!
# This script assumes the following order of phases: Phase 1 -> Phase 2 -> Phase Demolished
# Based on this assumption, elements Created in 'Phase 1' and Demolished in 'Phase Demolished'
# are considered 'Existing' when viewed in 'Phase 2'.
# Therefore, the script modifies the 'Existing' category in the relevant Phase Filters.
# If the actual phase order is different (e.g., Phase 1 -> Phase Demolished -> Phase 2),
# this script might not produce the desired result, and the 'Demolished' category might need adjustment instead.
phase1_name = "Phase 1"
phase2_name = "Phase 2"
phase_demolished_name = "Phase Demolished" # The phase where demolition occurs
# --- End Configuration ---

# Function to find Phase ElementId by name
def find_phase_id(doc, phase_name):
    collector = FilteredElementCollector(doc).OfClass(Phase)
    # Use a more robust check for name comparison
    found_phase = None
    for phase in collector:
        try:
            if phase.Name == phase_name:
                found_phase = phase
                break
        except:
            # Handle potential issues accessing Name property, though unlikely for Phase elements
            pass
    if found_phase:
        return found_phase.Id
    return ElementId.InvalidElementId

# Find Phase ElementIds
phase1_id = find_phase_id(doc, phase1_name)
phase2_id = find_phase_id(doc, phase2_name)
phase_demolished_id = find_phase_id(doc, phase_demolished_name) # Primarily needed to confirm existence

# Validate Phases
error_messages = []
phases_ok = True
if phase1_id == ElementId.InvalidElementId:
    error_messages.append("# Error: Phase named '{}' not found.".format(phase1_name))
    phases_ok = False
if phase2_id == ElementId.InvalidElementId:
    error_messages.append("# Error: Phase named '{}' not found.".format(phase2_name))
    phases_ok = False
if phase_demolished_id == ElementId.InvalidElementId:
    # This phase isn't strictly needed for the filter logic if the assumption holds, but the user mentioned it.
    error_messages.append("# Warning: Phase named '{}' (demolition phase) not found. Proceeding based on assumption.".format(phase_demolished_name))
    # phases_ok = False # Allow script to continue if only the demolition phase is missing, based on assumption

if not phases_ok:
    for msg in error_messages:
        print(msg)
else:
    # Find views set to 'Phase 2'
    view_collector = FilteredElementCollector(doc).OfClass(View)
    target_views = []
    for view in view_collector:
        # Skip view templates and non-graphical views if necessary
        if view.IsTemplate or not view.ViewType: # Basic check for valid graphical views
             continue
        try:
            # Check the VIEW_PHASE parameter
            phase_param = view.get_Parameter(BuiltInParameter.VIEW_PHASE)
            if phase_param and phase_param.HasValue and phase_param.AsElementId() == phase2_id:
                target_views.append(view)
        except Exception as e:
            # print("# Debug: Error checking view {} - {}".format(view.Id, e)) # Optional Debug
            pass # Skip views that cause errors

    if not target_views:
        print("# Info: No views found with Phase set to '{}'.".format(phase2_name))
    else:
        # Collect unique Phase Filter Ids used by these views
        target_filter_ids = HashSet[ElementId]()
        for view in target_views:
            try:
                filter_param = view.get_Parameter(BuiltInParameter.VIEW_PHASE_FILTER)
                # Check if parameter exists, has a value, and is not read-only (basic check, might still be template controlled)
                if filter_param and filter_param.HasValue and not filter_param.IsReadOnly:
                    filter_id = filter_param.AsElementId()
                    if filter_id != ElementId.InvalidElementId:
                        target_filter_ids.Add(filter_id)
                # else: View might use template, have no filter, or filter param is read-only
            except Exception as e:
                # print("# Debug: Error getting filter from view {} - {}".format(view.Id, e)) # Optional Debug
                pass

        if target_filter_ids.Count == 0:
            print("# Info: No modifiable Phase Filters found assigned to views set to '{}'.".format(phase2_name))
            print("# Check if views use View Templates or if Phase Filters are assigned.")
        else:
            # Modify the collected Phase Filters
            modified_filters_count = 0
            skipped_filters_errors = []
            already_set_filters_count = 0

            for filter_id in target_filter_ids:
                phase_filter_element = doc.GetElement(filter_id)
                if not isinstance(phase_filter_element, PhaseFilter):
                    # print("# Warning: Element ID {} is not a PhaseFilter.".format(filter_id)) # Optional debug
                    continue

                try:
                    # Get the presentation for 'Existing' elements
                    # Based on assumption: Created(P1) + Demolished(PDemo) => Existing in P2 (if P1 < P2 < PDemo)
                    current_presentation = phase_filter_element.GetPhaseStatusPresentation(ElementOnPhaseStatus.Existing)

                    target_presentation = PhaseStatusPresentation.DoNotDisplay

                    # If it's not already set to 'Not Displayed', change it
                    if current_presentation != target_presentation:
                        phase_filter_element.SetPhaseStatusPresentation(ElementOnPhaseStatus.Existing, target_presentation)
                        modified_filters_count += 1
                        # print("# Modified Phase Filter '{}' (ID: {}): Set 'Existing' to Not Displayed.".format(phase_filter_element.Name, filter_id)) # Optional Debug
                    else:
                        already_set_filters_count += 1
                        # print("# Phase Filter '{}' (ID: {}) already has 'Existing' set to Not Displayed.".format(phase_filter_element.Name, filter_id)) # Optional Debug


                except Exception as e:
                    filter_name = "Unknown"
                    try:
                        filter_name = phase_filter_element.Name
                    except: pass
                    skipped_filters_errors.append("'{}' (ID: {}) - Error: {}".format(filter_name, filter_id, e))

            # Report outcome
            # if modified_filters_count > 0:
            #      print("# Successfully modified {} Phase Filters.".format(modified_filters_count)) # Optional summary
            # if already_set_filters_count > 0:
            #      print("# {} Phase Filters already had the desired setting.".format(already_set_filters_count)) # Optional summary
            # if modified_filters_count == 0 and already_set_filters_count == 0 and not skipped_filters_errors:
                 # print("# No Phase Filters required modification or none were found applicable.") # Optional summary

            if skipped_filters_errors:
                print("# Errors occurred while processing some Phase Filters:")
                for skip_msg in skipped_filters_errors:
                    print("# - {}".format(skip_msg))