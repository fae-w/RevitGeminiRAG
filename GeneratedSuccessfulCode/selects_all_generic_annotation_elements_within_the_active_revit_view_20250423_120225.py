# Purpose: This script selects all generic annotation elements within the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections') # Required for List<T>
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, View

# Assume 'doc' and 'uidoc' are pre-defined

# Get the active view ID
try:
    active_view = doc.ActiveView
    if active_view is None:
        print("# Error: No active view found.")
        # Set active_view_id to InvalidElementId to prevent further processing
        active_view_id = ElementId.InvalidElementId
    else:
        active_view_id = active_view.Id
except Exception as e:
    print("# Error accessing ActiveView: {}".format(e)) # Escaped format string
    active_view_id = ElementId.InvalidElementId

# List to store the ElementIds of the generic annotations
generic_annotation_ids = []

# Proceed only if we have a valid active view ID
if active_view_id != ElementId.InvalidElementId:
    try:
        # Create a collector filtered for the active view
        collector = FilteredElementCollector(doc, active_view_id)

        # Filter for Generic Annotations (instances only)
        generic_annotation_collector = collector.OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType()

        # Collect the ElementIds
        for anno in generic_annotation_collector:
             # Double check element is valid before adding
             if anno and anno.IsValidObject:
                 generic_annotation_ids.append(anno.Id)

    except Exception as ex:
        print("# Error during element collection: {}".format(ex)) # Escaped format string

# Check if any generic annotations were found
if generic_annotation_ids:
    # Convert the Python list to a .NET List<ElementId>
    selection_list = List[ElementId](generic_annotation_ids)
    try:
        # Set the selection in the UI
        uidoc.Selection.SetElementIds(selection_list)
        # print("# Selected {} generic annotation elements in the current view.".format(len(generic_annotation_ids))) # Escaped format string - Optional Output
    except Exception as sel_ex:
        print("# Error setting selection: {}".format(sel_ex)) # Escaped format string
#else:
    # print("# No generic annotation elements found in the current view.") # Optional Output
    # pass # No elements to select