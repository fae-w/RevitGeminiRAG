# Purpose: This script creates a wall sweep on a selected wall using a specified type and offset.

# Purpose: This script creates a wall sweep on a selected wall in Revit, using a specified type and offset from the top.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Wall,
    WallSweep,
    WallSweepInfo,
    WallSweepType, # Import specific type
    ElementId,
    UnitUtils,
    ForgeTypeId # Import ForgeTypeId for units
)
# Note: WallSweepLocation is an enum within WallSweepInfo class

# --- Parameters ---
target_sweep_type_name = "Default Cornice" # The name of the Wall Sweep Type in Revit
distance_from_top_mm = 150.0

# --- Convert units ---
# Revit internal units are feet. Convert mm to feet using ForgeTypeId.
distance_from_top_feet = UnitUtils.ConvertToInternalUnits(distance_from_top_mm, ForgeTypeId("autodesk.unit.unit:millimeters-1.0.1")) # Use ForgeTypeId for mm

# --- Get Selection ---
# Assume uidoc and doc are available in the execution context
selected_ids = uidoc.Selection.GetElementIds()
selected_wall = None

# --- Validate Selection ---
# Use Count property for ICollection in IronPython
if selected_ids.Count == 1:
    # Get the first ElementId from the selection
    element_id = list(selected_ids)[0] # Need to convert ICollection to list/iterable to index
    element = doc.GetElement(element_id)
    if isinstance(element, Wall):
        selected_wall = element
    else:
        print("# Error: Selected element is not a Wall.")
elif selected_ids.Count == 0:
    print("# Error: No element selected. Please select one Wall.")
else:
    print("# Error: More than one element selected. Please select only one Wall.")

# --- Find Wall Sweep Type ---
sweep_type = None # Store the found type object
if selected_wall: # Proceed only if a valid wall was selected
    # Filter specifically for WallSweepType elements
    collector = FilteredElementCollector(doc).OfClass(WallSweepType)
    # Iterate to find the type by name
    for el_type in collector:
        if el_type.Name == target_sweep_type_name:
             sweep_type = el_type # Store the found type
             break # Found it, stop searching

    if sweep_type is None:
        print("# Error: Wall Sweep Type '{}' not found in the project.".format(target_sweep_type_name))

# --- Create Wall Sweep ---
if selected_wall and sweep_type:
    # Check if the wall can host a sweep (e.g., basic walls can, curtain walls cannot)
    # The API doesn't have a direct 'WallAllowsWallSweep' method. Rely on Create to throw.
    try:
        # Configure WallSweepInfo for placement
        # WallSweepLocation is an enum inside WallSweepInfo class
        # Constructor: (Autodesk.Revit.DB.WallSweepInfo.WallSweepType type, bool isSweep)
        sweep_info = WallSweepInfo(WallSweepInfo.WallSweepType.Sweep, True)
        # Property: DistanceMeasuredFrom (enum WallSweepLocation: Base, Top)
        sweep_info.DistanceMeasuredFrom = WallSweepInfo.WallSweepLocation.Top
        # Property: Distance (double, distance from Base or Top)
        sweep_info.Distance = distance_from_top_feet # Positive distance down from Top
        # Other properties like WallOffset, ProfileId are controlled by the type or defaults

        # Create the Wall Sweep
        # Method: WallSweep.Create(Wall hostWall, ElementId wallSweepTypeId, WallSweepInfo wallSweepInfo)
        # Pass the ID of the found WallSweepType
        new_sweep = WallSweep.Create(selected_wall, sweep_type.Id, sweep_info)

        # Optional: Print success message (kept commented out)
        # print("# Successfully created Wall Sweep ID: {} on Wall ID: {}".format(new_sweep.Id, selected_wall.Id))

    except Exception as e:
        # Provide more specific feedback if possible
        error_message = str(e)
        if "Wall does not support sweeps or reveals" in error_message or \
           "Input wall cannot accept wall sweep" in error_message or \
           "doesn't support sweeps/reveals insertions" in error_message:
             print("# Error: The selected Wall Type or specific Wall instance does not allow Wall Sweeps.")
        else:
            # Generic error for other issues
            print("# Error creating Wall Sweep: {}".format(error_message))

# Else: Errors related to selection or finding the type were already printed if they occurred