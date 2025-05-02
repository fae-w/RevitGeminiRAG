# Purpose: This script sets up element collectors and helper functions for Revit automation.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ParameterFilterElement, ElementId,
    ElementWorksetFilter, WorksetTable, WorksetKind, FilteredWorksetCollector,
    Workset, WorksetId, OverrideGraphicSettings, Color, LinePatternElement, View,
    Element # Base class for collector
)

# Helper function to get LinePatternElementId by name
def get_line_pattern_id_by_name(doc_param, name):
    """Finds the ElementId of a LinePatternElement by its name."""
    # Return InvalidElementId if name is empty or null
    if not name:
        return ElementId.InvalidElementId
    # Create collector for LinePatternElement
    collector = FilteredElementCollector(doc_param).OfClass(LinePatternElement)
    # Iterate through elements