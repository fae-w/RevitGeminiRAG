# Purpose: This script sets the angle of selected corner mullions to a specified value.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for System.Math and System.Double

from Autodesk.Revit.DB import Mullion, ElementId, BuiltInParameter
import System # Required for Math.PI and System.Double

# --- Configuration ---
target_angle_degrees = 45.0
# Convert degrees to radians for Revit's internal use
target_angle_radians = System.Math.PI * target_angle_degrees / 180.0

# --- Get Selected Elements ---
selected_ids = uidoc.Selection.GetElementIds()

# --- Process Selection ---
if selected_ids:
    for element_id in selected_ids:
        element = doc.GetElement(element_id)

        # Check if the element is a Mullion
        if not isinstance(element, Mullion):
            continue

        mullion = element

        # Check if it's a corner mullion using the IsCornerMullion property
        if not mullion.IsCornerMullion:
            continue

        try:
            # Get the 'Angle' parameter using BuiltInParameter
            angle_param = mullion.get_Parameter(BuiltInParameter.MULLION_ANGLE)

            if angle_param is None or not angle_param.HasValue:
                continue

            # Check if the parameter is read-only
            if angle_param.IsReadOnly:
                continue

            # Check if the parameter storage type is Double (expected for angle)
            # Although MULLION_ANGLE is expected to be Double, this check prevents potential errors.
            if angle_param.StorageType != System.Double:
                 print("# Warning: Mullion ID: {0} - 'Angle' parameter is not a Double type (found {1}). Skipping update.".format(mullion.Id, angle_param.StorageType))
                 continue

            # Set the parameter value (in radians)
            angle_param.Set(target_angle_radians)

        except Exception as e:
            print("# Error processing Mullion ID {0}: {1}".format(mullion.Id, str(e)))
# else:
    # Optional: Add a message if nothing is selected, but the request asks for ONLY the code.
    # print("# No elements selected.")