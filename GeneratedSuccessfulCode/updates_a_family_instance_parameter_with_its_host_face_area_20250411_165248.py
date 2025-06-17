# Purpose: This script updates a family instance parameter with its host face area.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilyInstance,
    Reference,
    GeometryObject,
    Face,
    Parameter,
    Element,
    ElementId,
    BuiltInCategory # Although not strictly needed for FamilyInstance class filter, it's good practice
)

# --- Configuration ---
# The exact, case-sensitive name of the custom shared parameter to populate
# IMPORTANT: This parameter must exist on the family instances and be of type Number or Area.
TARGET_PARAMETER_NAME = "Host Area"

# --- Main Script ---
# 'doc' is assumed to be pre-defined

# Collector for all FamilyInstance elements in the document
collector = FilteredElementCollector(doc).OfClass(FamilyInstance).WhereElementIsNotElementType()

updated_count = 0
skipped_no_host_face = 0
skipped_no_param = 0
skipped_param_readonly = 0
skipped_error = 0

# Iterate through all family instances
for instance in collector:
    if not isinstance(instance, FamilyInstance):
        continue # Should not happen with OfClass filter, but safe check

    try:
        # Get the reference to the host face
        host_face_ref = instance.HostFace

        # Check if the instance is hosted on a specific face
        if host_face_ref is not None and host_face_ref.ElementId != ElementId.InvalidElementId:
            host_element = doc.GetElement(host_face_ref.ElementId)
            if host_element is None:
                 # print("# Skipping instance {}: Host element not found.".format(instance.Id)) # Optional logging
                 skipped_error += 1
                 continue

            # Get the geometry object (the Face) from the host element using the reference
            geo_obj = host_element.GetGeometryObjectFromReference(host_face_ref)

            if isinstance(geo_obj, Face):
                host_face = geo_obj
                try:
                    # Get the area of the host face (in Revit internal units - square feet)
                    face_area = host_face.Area

                    # Find the target parameter on the family instance
                    # LookupParameter is case-sensitive
                    param = instance.LookupParameter(TARGET_PARAMETER_NAME)

                    if param is not None:
                        if not param.IsReadOnly:
                            # Set the parameter value
                            # Assumes the parameter type is Number or Area, accepting a double
                            param.Set(face_area)
                            updated_count += 1
                        else:
                            # print("# Skipping instance {}: Parameter '{}' is read-only.".format(instance.Id, TARGET_PARAMETER_NAME)) # Optional logging
                            skipped_param_readonly += 1
                    else:
                        # print("# Skipping instance {}: Parameter '{}' not found.".format(instance.Id, TARGET_PARAMETER_NAME)) # Optional logging
                        skipped_no_param += 1

                except Exception as face_err:
                    # print("# Error processing face area or parameter for instance {}: {}".format(instance.Id, face_err)) # Optional logging
                    skipped_error += 1
            # else:
                # print("# Skipping instance {}: Host reference did not resolve to a Face.".format(instance.Id)) # Optional logging
                # This might happen if the host geometry is complex or the reference is invalid
                # skipped_error += 1 # Or a different counter if needed

        else:
            # Instance is not hosted on a specific face (e.g., level-hosted, workplane-hosted not on a face, unhosted)
            skipped_no_host_face += 1

    except Exception as inst_err:
        # print("# Error processing instance {}: {}".format(instance.Id, inst_err)) # Optional logging
        skipped_error += 1

# Optional: Print summary (commented out as per guidelines)
# print("# --- Script Summary ---")
# print("# Successfully updated '{}' parameter for {} instances.".format(TARGET_PARAMETER_NAME, updated_count))
# if skipped_no_host_face > 0:
#    print("# Skipped {} instances: Not hosted on a specific face.".format(skipped_no_host_face))
# if skipped_no_param > 0:
#    print("# Skipped {} instances: Parameter '{}' not found.".format(skipped_no_param, TARGET_PARAMETER_NAME))
# if skipped_param_readonly > 0:
#    print("# Skipped {} instances: Parameter '{}' is read-only.".format(skipped_param_readonly, TARGET_PARAMETER_NAME))
# if skipped_error > 0:
#    print("# Skipped {} instances due to errors during processing.".format(skipped_error))
# print("# Script finished.")