# Purpose: This script changes the color of structural columns to red in the active 3D view.

# Purpose: This script changes the color of structural columns to red in the active 3D view of a Revit model.

﻿import clr
# Add references to Revit API assemblies
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Generally useful, though not strictly required for this specific task
clr.AddReference('System')
from System import Byte

# Import necessary Revit DB classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    View,
    ViewType,
    OverrideGraphicSettings,
    Color,
    ElementId
)
# Import Structure namespace for StructuralColumn
clr.AddReference("RevitAPI") # Ensure loaded
clr.AddReference("RevitAPIUI") # Ensure loaded
from Autodesk.Revit.DB.Structure import StructuralType # Needed for filtering if using OfClass

# doc and uidoc are assumed available from the execution context

# Get the active view
active_view = doc.ActiveView

# Define the target color (Red)
# Using System.Byte for components, though integers often work in IronPython
red_color = Color(Byte(255), Byte(0), Byte(0))

# Proceed only if there is an active view and it's a 3D view
if active_view and active_view.ViewType == ViewType.ThreeD:

    # Create OverrideGraphicSettings object
    override_settings = OverrideGraphicSettings()

    # Set the projection line color
    override_settings.SetProjectionLineColor(red_color)

    # Collect all Structural Column element instances visible in the active 3D view
    collector = FilteredElementCollector(doc, active_view.Id)
    # Using OfCategory is generally safer and often sufficient
    column_collector = collector.OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType()

    # Apply the overrides to each structural column instance
    # Transaction management is handled by the calling environment (e.g., C# wrapper)
    elements_to_override = list(column_collector) # Convert to list to avoid potential modification issues during iteration

    for column in elements_to_override:
        try:
            # Check if element is valid before overriding
            if column and column.IsValidObject:
                 active_view.SetElementOverrides(column.Id, override_settings)
        except Exception as e:
            # Silently ignore failures for individual elements, or log if necessary
            # print("Error overriding element {{}}: {{}}".format(column.Id, e))
            pass

# No output messages required by the prompt
# Script completes silently if not a 3D view or no active view