# Purpose: This script sets the Phase and Phase Filter of the active Revit view.

﻿# Imports
import clr
clr.AddReference('System.Collections') # Required for List
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Phase,
    ElementId,
    View,
    PhaseFilter, # Class representing Phase Filter elements
    BuiltInParameter
)

# --- Configuration ---
target_phase_name = "Phase 1"
# Assumption: A Phase Filter element exists with this name, configured to show ONLY 'New' elements.
# Common default names might include "Show New" or similar. Adjust if needed.
target_phase_filter_name = "Show New"
# --- End Configuration ---

# Find the target Phase ElementId
target_phase_id = ElementId.InvalidElementId
phase_collector = FilteredElementCollector(doc).OfClass(Phase)
for phase in phase_collector:
    # Phase names are stored in the element's Name property
    if phase.Name == target_phase_name:
        target_phase_id = phase.Id
        break

if target_phase_id == ElementId.InvalidElementId:
    print("# Error: Phase named '{0}' not found.".format(target_phase_name))
else:
    # Find the target PhaseFilter ElementId
    target_phase_filter_id = ElementId.InvalidElementId
    phase_filter_collector = FilteredElementCollector(doc).OfClass(PhaseFilter)
    for pf in phase_filter_collector:
        # PhaseFilter names are stored in the element's Name property
        # Accessing Name property of the element 'pf'
        try:
            pf_name = pf.Name
            if pf_name == target_phase_filter_name:
                target_phase_filter_id = pf.Id
                break
        except Exception as name_ex:
            # print("# Debug: Could not get name for PhaseFilter ID {0}: {1}".format(pf.Id, name_ex)) # Optional Debug
            pass # Skip elements where Name cannot be accessed

    if target_phase_filter_id == ElementId.InvalidElementId:
        print("# Error: Phase Filter element named '{0}' not found.".format(target_phase_filter_name))
        print("# Ensure a Phase Filter exists with settings: New=By Category/Overridden, Existing/Demo/Temp=Not Displayed.")
    else:
        # Get the active view
        active_view = uidoc.ActiveView
        if not active_view:
            print("# Error: No active view.")
        elif not isinstance(active_view, View):
             print("# Error: Active document is not a view.")
        else:
            view_updated = False
            error_messages = []

            # 1. Set the View's Phase parameter to the target phase
            phase_param = active_view.get_Parameter(BuiltInParameter.VIEW_PHASE)
            if phase_param:
                if phase_param.IsReadOnly:
                    error_messages.append("# View Phase parameter is read-only (check View Template?).")
                elif phase_param.AsElementId() != target_phase_id:
                     try:
                         phase_param.Set(target_phase_id)
                         view_updated = True
                         # print("# View phase set to '{0}'".format(target_phase_name)) # Optional Debug
                     except Exception as e:
                         error_messages.append("# Failed to set View Phase: {0}".format(e))
                # else: Parameter already set correctly
            else:
                 error_messages.append("# Could not find View Phase parameter (VIEW_PHASE).")


            # 2. Set the View's Phase Filter parameter to the target filter
            phase_filter_param = active_view.get_Parameter(BuiltInParameter.VIEW_PHASE_FILTER)
            if phase_filter_param:
                if phase_filter_param.IsReadOnly:
                    error_messages.append("# View Phase Filter parameter is read-only (check View Template?).")
                elif phase_filter_param.AsElementId() != target_phase_filter_id:
                     try:
                         phase_filter_param.Set(target_phase_filter_id)
                         view_updated = True
                         # print("# View Phase Filter set to '{0}'".format(target_phase_filter_name)) # Optional Debug
                     except Exception as e:
                         error_messages.append("# Failed to set View Phase Filter: {0}".format(e))
                # else: Parameter already set correctly
            else:
                 error_messages.append("# Could not find View Phase Filter parameter (VIEW_PHASE_FILTER).")


            # Report outcome
            if error_messages:
                for msg in error_messages:
                    print(msg)
            elif not view_updated:
                # print("# No changes needed or possible for view parameters.") # Optional Info
                pass
            # else: Successful update occurred, no message needed unless debugging