# Purpose: This script transfers the volume of selected floor elements to their comment parameter.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    Parameter,
    StorageType,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Element,
    Floor # Added for type checking
)
# System.Collections is not strictly needed here as we iterate selected IDs directly
# from System.Collections.Generic import List

# Get the current selection
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids:
    print("# No elements selected.")
else:
    processed_count = 0
    error_count = 0
    skipped_count = 0

    for element_id in selected_ids:
        element = doc.GetElement(element_id)

        # Check if the element exists and is a Floor element
        if element and isinstance(element, Floor):
            try:
                # Get the Volume parameter
                # HOST_VOLUME_COMPUTED is the typical parameter for Floor volume
                volume_param = element.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED)

                # Fallback: Try looking up by name "Volume" if the BuiltInParameter fails
                if not volume_param or not volume_param.HasValue:
                    volume_param = element.LookupParameter("Volume")

                # Get the Comments parameter
                comments_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

                # Proceed only if both parameters are found and valid
                if volume_param and volume_param.HasValue and volume_param.StorageType == StorageType.Double and \
                   comments_param and not comments_param.IsReadOnly and comments_param.StorageType == StorageType.String:

                    volume_value_internal = volume_param.AsDouble() # Value is in internal units (cubic feet)

                    # Convert volume value to string - keep it simple as internal value string
                    volume_str = str(volume_value_internal)
                    # Alternative formatting (e.g., 2 decimal places):
                    # volume_str = "{:.2f}".format(volume_value_internal)

                    # Set the Comments parameter
                    comments_param.Set(volume_str)
                    processed_count += 1
                else:
                    # print(f"# Skipping element ID {element.Id}: Could not find valid/writable Volume or Comments parameter.")
                    skipped_count += 1

            except Exception as e:
                # print(f"# Error processing element ID {element.Id}: {e}")
                error_count += 1
        else:
            # Element is not a Floor
             skipped_count += 1
             # print(f"# Skipping element ID {element_id}: Not a Floor element.")

    # Optional: Print summary (useful for debugging in RPS/pyRevit)
    # print(f"# Process finished. Updated: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")

# No EXPORT required, modifications are done in the model.