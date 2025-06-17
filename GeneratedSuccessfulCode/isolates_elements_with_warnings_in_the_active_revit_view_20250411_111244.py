# Purpose: This script isolates elements with warnings in the active Revit view.

# Purpose: This script isolates elements in the active Revit view that have warnings associated with them.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import View, ElementId, FilteredElementCollector, FailureMessage

# Get the active view
active_view = doc.ActiveView

if active_view is None:
    print("# Error: No active view found. Cannot perform isolation.")
else:
    # Get all warnings in the document
    warnings = doc.GetWarnings()
    
    element_ids_with_warnings = set() # Use a set to store unique ElementIds
    
    if warnings:
        for warning in warnings:
            failing_ids = warning.GetFailingElements()
            if failing_ids:
                for element_id in failing_ids:
                    # We collect all elements with warnings first.
                    # The isolation will apply in the context of the active view.
                    # Elements not visible in the view won't suddenly appear,
                    # but if an element with a warning IS potentially visible, it will be isolated.
                    element_ids_with_warnings.add(element_id)

    if element_ids_with_warnings:
        # Convert the Python set of ElementIds to a .NET List<ElementId>
        ids_to_isolate_net = List[ElementId](element_ids_with_warnings)
        
        try:
            # Check if temporary hide/isolate is already active - inform the user if so.
            if active_view.IsTemporaryHideIsolateActive():
                 # print("# Info: Temporary Hide/Isolate is already active. Applying new isolation.") # Optional info
                 pass
            
            # Apply Temporary Isolation (Transaction is managed externally)
            active_view.IsolateElementsTemporary(ids_to_isolate_net)
            # print(f"# Successfully initiated temporary isolation for {len(element_ids_with_warnings)} elements with warnings in the active view.") # Optional confirmation
        except Exception as e:
            print(f"# Error applying temporary isolation: {e}") # Escaped f-string for error reporting
    else:
        # print("# No elements with warnings found in the document to isolate.") # Optional info
        pass # No elements with warnings were found