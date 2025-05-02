# Purpose: This script selects duplicate Revit elements identified by Revit's warnings.

# Purpose: This script selects elements in Revit identified as duplicates based on Revit's built-in duplicate instances warning.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List, HashSet # Using HashSet for efficient unique collection
from Autodesk.Revit.DB import ElementId, BuiltInFailures, FailureMessage, FailureDefinitionId

# Define the specific FailureDefinitionId for duplicate instances warnings
# This targets elements Revit has identified as being in the same place.
duplicate_instances_failure_id = BuiltInFailures.OverlapFailures.DuplicateInstances

# Use a HashSet to store unique ElementIds of duplicate elements
duplicate_element_ids = HashSet[ElementId]()

# Retrieve all warnings currently present in the document
try:
    warnings = doc.GetWarnings()
except Exception as e:
    print("# Error retrieving document warnings: {}".format(e)) # Escaped
    warnings = [] # Ensure warnings is iterable even if retrieval fails

# Iterate through each warning message
for warning in warnings:
    try:
        failure_id = warning.GetFailureDefinitionId()
        # Check if the warning's ID matches the one for duplicate instances
        if failure_id == duplicate_instances_failure_id:
            # Get the ElementIds of the elements causing this specific warning
            failing_ids = warning.GetFailingElements()
            # Add each failing element ID to the HashSet (duplicates are automatically handled)
            for element_id in failing_ids:
                # Ensure the element ID is valid before adding
                if element_id is not None and element_id != ElementId.InvalidElementId:
                    duplicate_element_ids.Add(element_id)
    except Exception as ex:
        # Log error processing a specific warning, but continue processing others
        print("# Error processing warning: {}".format(ex)) # Escaped
        pass

# Convert the HashSet of unique ElementIds to a List suitable for selection
selection_list = List[ElementId](duplicate_element_ids)

# Check if any elements identified as duplicates were found
if selection_list.Count > 0:
    try:
        # Set the current selection in the UI to the list of duplicate element IDs
        uidoc.Selection.SetElementIds(selection_list)
        # print("# Selected {} elements identified as duplicates by Revit warnings.".format(selection_list.Count)) # Escaped Optional output
    except Exception as sel_ex:
        # Handle potential errors during the selection process
        print("# Error setting selection: {}".format(sel_ex)) # Escaped
else:
    # Inform the user if no duplicate instance warnings were found
    print("# No elements found triggering the 'Duplicate Instances' warning.")