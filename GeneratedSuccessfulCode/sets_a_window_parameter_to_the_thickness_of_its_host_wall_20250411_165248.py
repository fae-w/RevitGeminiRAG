# Purpose: This script sets a window parameter to the thickness of its host wall.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilyInstance,
    Wall,
    Parameter,
    Element,
    ElementId,
    BuiltInCategory
)

# --- Configuration ---
# The exact, case-sensitive name of the custom shared parameter on the windows
# IMPORTANT: This parameter must exist on the window instances and be of type Number or Length.
TARGET_PARAMETER_NAME = "Host Wall Thickness"

# --- Main Script ---
# 'doc' is assumed to be pre-defined

# Collector for all Window family instances in the document
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType()

updated_count = 0
skipped_no_host = 0
skipped_host_not_wall = 0
skipped_no_param = 0
skipped_param_readonly = 0
skipped_error = 0

# Iterate through all window instances
for instance in collector:
    if not isinstance(instance, FamilyInstance):
        continue # Should not happen with OfClass filter, but safe check

    try:
        # Get the host element of the window
        host_element = instance.Host

        if host_element is not None:
            # Check if the host is a Wall
            if isinstance(host_element, Wall):
                host_wall = host_element
                try:
                    # Get the wall's thickness (in Revit internal units - decimal feet)
                    wall_thickness = host_wall.Width

                    # Find the target parameter on the window instance
                    # LookupParameter is case-sensitive
                    param = instance.LookupParameter(TARGET_PARAMETER_NAME)

                    if param is not None:
                        if not param.IsReadOnly:
                            # Set the parameter value
                            # Assumes the parameter type is Number or Length, accepting a double
                            param.Set(wall_thickness)
                            updated_count += 1
                        else:
                            # print("# Skipping window {{}}: Parameter '{{}}' is read-only.".format(instance.Id, TARGET_PARAMETER_NAME)) # Optional logging
                            skipped_param_readonly += 1
                    else:
                        # print("# Skipping window {{}}: Parameter '{{}}' not found.".format(instance.Id, TARGET_PARAMETER_NAME)) # Optional logging
                        skipped_no_param += 1

                except Exception as wall_err:
                    # print("# Error processing wall thickness or parameter for window {{}}: {{}}".format(instance.Id, wall_err)) # Optional logging
                    skipped_error += 1
            else:
                # Host element is not a wall
                # print("# Skipping window {{}}: Host element (ID: {{}}) is not a Wall.".format(instance.Id, host_element.Id)) # Optional logging
                skipped_host_not_wall += 1
        else:
            # Instance has no host (this shouldn't typically happen for windows, but check anyway)
            # print("# Skipping window {{}}: No host element found.".format(instance.Id)) # Optional logging
            skipped_no_host += 1

    except Exception as inst_err:
        # print("# Error processing window instance {{}}: {{}}".format(instance.Id, inst_err)) # Optional logging
        skipped_error += 1

# Optional: Print summary (commented out as per guidelines)
# print("# --- Script Summary ---")
# print("# Successfully updated '{{}}' parameter for {{}} windows.".format(TARGET_PARAMETER_NAME, updated_count))
# if skipped_no_host > 0:
#    print("# Skipped {{}} windows: No host element found.".format(skipped_no_host))
# if skipped_host_not_wall > 0:
#    print("# Skipped {{}} windows: Host element was not a Wall.".format(skipped_host_not_wall))
# if skipped_no_param > 0:
#    print("# Skipped {{}} windows: Parameter '{{}}' not found.".format(skipped_no_param, TARGET_PARAMETER_NAME))
# if skipped_param_readonly > 0:
#    print("# Skipped {{}} windows: Parameter '{{}}' is read-only.".format(skipped_param_readonly, TARGET_PARAMETER_NAME))
# if skipped_error > 0:
#    print("# Skipped {{}} windows due to errors during processing.".format(skipped_error))
# print("# Script finished.")