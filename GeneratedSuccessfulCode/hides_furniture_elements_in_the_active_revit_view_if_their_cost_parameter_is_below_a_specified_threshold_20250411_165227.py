# Purpose: This script hides furniture elements in the active Revit view if their cost parameter is below a specified threshold.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    View,
    StorageType
)

# --- Configuration ---
target_category = BuiltInCategory.OST_Furniture
parameter_name = "Cost"
threshold_value = 100.0 # Assuming Cost is a numerical value (like currency)

# --- Get Active View ---
current_view = doc.ActiveView # Use a distinct name

if not current_view or not isinstance(current_view, View):
    print("# Error: No active view found or the active view is not a valid View object.")
elif current_view.IsTemplate:
     print("# Error: Active view is a view template and cannot have elements hidden individually.")
else:
    # --- Find Elements to Hide ---
    elements_to_hide_ids = List[ElementId]()
    try:
        collector = FilteredElementCollector(doc, current_view.Id)
        furniture_elements = collector.OfCategory(target_category).WhereElementIsNotElementType().ToElements()

        if not furniture_elements:
            # print("# No furniture elements found in the active view.") # Optional message
            pass
        else:
            count = 0
            for element in furniture_elements:
                try:
                    # Attempt to get the 'Cost' parameter by name
                    cost_param = element.LookupParameter(parameter_name)

                    # Check if parameter exists and has a value
                    if cost_param and cost_param.HasValue:
                        # Get parameter value - primarily expect Double for currency
                        cost_value = None
                        storage_type = cost_param.StorageType
                        if storage_type == StorageType.Double:
                           cost_value = cost_param.AsDouble()
                        elif storage_type == StorageType.Integer:
                           # Less likely for cost, but handle just in case
                           cost_value = float(cost_param.AsInteger()) # Convert int to float for consistent comparison
                        # Note: String storage type is ignored for numerical comparison

                        # Compare with threshold if a valid numerical value was obtained
                        if cost_value is not None and cost_value < threshold_value:
                            # Check if the element can be hidden in this specific view
                            if element.CanBeHidden(current_view):
                                elements_to_hide_ids.Add(element.Id)
                                count += 1
                            # else: # Optional: report elements that cannot be hidden
                            #    print(f"# Info: Element {element.Id} ({element.Name}) cannot be hidden in this view.")

                except Exception as param_ex:
                    # Silently ignore elements that cause errors during parameter lookup/check
                    # print(f"# Warning: Could not process element {element.Id}. Error accessing parameter '{parameter_name}': {param_ex}") # Optional debug
                    pass # Continue to the next element

            # print(f"# Found {count} furniture elements with '{parameter_name}' < {threshold_value} to hide.") # Optional debug message

    except Exception as col_ex:
        print("# Error during element collection: {}".format(col_ex))
        elements_to_hide_ids = List[ElementId]() # Ensure list is empty if collection failed

    # --- Hide Elements ---
    # Check if there are any elements identified to be hidden
    if elements_to_hide_ids.Count > 0:
        try:
            # Hide the collected elements using the View.HideElements method
            # IMPORTANT: Assumes an external Transaction is already started by the C# wrapper.
            current_view.HideElements(elements_to_hide_ids)
            # print(f"# Successfully hid {elements_to_hide_ids.Count} furniture elements in view '{current_view.Name}'.") # Optional confirmation message
        except Exception as hide_ex:
            # Report errors during the hiding process
            print("# Error hiding elements in the view: {}".format(hide_ex))
    # elif elements_to_hide_ids.Count == 0:
        # No elements met the criteria, no action needed, optional message below
        # print("# No elements met the criteria to be hidden or collection failed.") # Optional info message