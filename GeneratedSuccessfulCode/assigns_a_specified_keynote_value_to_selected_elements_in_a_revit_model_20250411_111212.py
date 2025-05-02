# Purpose: This script assigns a specified keynote value to selected elements in a Revit model.

# Purpose: This script assigns a specific keynote value to selected Revit elements.

﻿# Import necessary Revit API classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ElementId, Element, BuiltInParameter, Parameter

# --- Parameters ---
target_keynote_key = "A.10.20" # The specific keynote key string to assign

# --- Process Selected Elements ---
selection = uidoc.Selection
selected_ids = selection.GetElementIds()

if not selected_ids or selected_ids.Count == 0:
    print("# No elements selected.")
else:
    assigned_count = 0
    skipped_count = 0
    error_count = 0
    print("Attempting to assign keynote key '{{}}' to {{}} selected elements...".format(target_keynote_key, selected_ids.Count))

    # Transaction needs to be handled outside this script by the caller
    # t = Transaction(doc, 'Assign Keynote')
    # t.Start()

    for element_id in selected_ids:
        try:
            element = doc.GetElement(element_id)
            if element is None:
                # print("# Skipping ID {}: Element not found.".format(element_id)) # Debug
                skipped_count += 1
                continue

            # Get the Keynote parameter
            keynote_param = element.get_Parameter(BuiltInParameter.KEYNOTE_PARAM)

            if keynote_param is not None and not keynote_param.IsReadOnly:
                # Set the parameter value to the Keynote Key string
                # Revit will handle the lookup/display based on the loaded keynote table
                keynote_param.Set(target_keynote_key)
                assigned_count += 1
            elif keynote_param is None:
                # print("# Skipping Element ID {} (Category: {}): Does not have a Keynote parameter.".format(element_id, element.Category.Name if element.Category else "N/A")) # Debug
                skipped_count += 1
            else: # Parameter exists but is read-only
                # print("# Skipping Element ID {} (Category: {}): Keynote parameter is read-only.".format(element_id, element.Category.Name if element.Category else "N/A")) # Debug
                skipped_count += 1

        except Exception as e:
            # print("# Error processing Element ID {}: {}".format(element_id, e)) # Debug
            error_count += 1

    # t.Commit()

    print("Successfully assigned keynote key to {} elements.".format(assigned_count))
    if skipped_count > 0:
        print("Skipped {} elements (parameter missing or read-only).".format(skipped_count))
    if error_count > 0:
        print("Encountered errors processing {} elements.".format(error_count))