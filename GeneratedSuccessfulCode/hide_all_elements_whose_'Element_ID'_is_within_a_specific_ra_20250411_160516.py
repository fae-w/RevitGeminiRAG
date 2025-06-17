# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    View,
    Element,
    ElementIsElementTypeFilter # Import ElementIsElementTypeFilter
)
# Using System for Int64 comparison if needed, though direct comparison works
import System

# --- Configuration ---
# Define the range for Element IDs (Integer values)
# IMPORTANT: Replace these values with the desired range
min_element_id_value = 500000  # Example minimum ID (inclusive)
max_element_id_value = 600000  # Example maximum ID (inclusive)

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View):
    print("# Error: No active view found or the active view is not suitable.")
elif active_view.IsTemplate:
     print("# Error: Active view is a view template and cannot have elements hidden individually.")
else:
    # --- Find Elements to Hide ---
    elements_to_hide_ids = List[ElementId]()
    count = 0

    try:
        # Collect all elements visible in the active view, excluding element types
        collector = FilteredElementCollector(doc, active_view.Id).WhereElementIsNotElementType()
        # Note: Using WhereElementIsNotElementType() might be slower than filtering later,
        # but it ensures we only consider instances that can typically be hidden.
        # Alternatively, collect all elements and check type inside the loop.

        for element in collector:
            try:
                element_id = element.Id
                # ElementId.IntegerValue is the property holding the integer value
                element_id_int_value = element_id.IntegerValue

                # Check if the Element ID's integer value is within the specified range
                if min_element_id_value <= element_id_int_value <= max_element_id_value:
                    # Check if the element can be hidden in this specific view
                    if element.CanBeHidden(active_view):
                        elements_to_hide_ids.Add(element_id)
                        count += 1
                    # else: # Optional: report elements that cannot be hidden
                    #    print("# Info: Element ID {} (Integer: {}) cannot be hidden in this view.".format(element_id, element_id_int_value))
            except Exception as element_ex:
                # Silently ignore elements that cause errors during ID check or CanBeHidden check
                # print("# Warning: Could not process element ID {}. Error: {}".format(element.Id if element else 'N/A', element_ex)) # Optional debug
                pass # Continue to the next element

        # print("# Found {} elements within the ID range [{}, {}] to hide.".format(count, min_element_id_value, max_element_id_value)) # Optional debug message

    except Exception as col_ex:
        print("# Error during element collection: {}".format(col_ex))
        elements_to_hide_ids = List[ElementId]() # Ensure list is empty if collection failed

    # --- Hide Elements ---
    # Check if there are any elements identified to be hidden
    if elements_to_hide_ids.Count > 0:
        try:
            # Hide the collected elements using the View.HideElements method
            # IMPORTANT: Assumes an external Transaction is already started by the C# wrapper.
            active_view.HideElements(elements_to_hide_ids)
            # print("# Successfully hid {} elements in view '{}'.".format(elements_to_hide_ids.Count, active_view.Name)) # Optional confirmation message
        except Exception as hide_ex:
            # Report errors during the hiding process
            print("# Error hiding elements in the view: {}".format(hide_ex))
    # elif count == 0: # Check original count in case collection succeeded but found none
        # print("# No elements found within the specified Element ID range [{}, {}] or none could be hidden.".format(min_element_id_value, max_element_id_value)) # Optional info message