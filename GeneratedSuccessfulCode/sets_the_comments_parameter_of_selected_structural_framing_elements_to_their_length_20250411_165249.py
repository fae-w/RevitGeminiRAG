# Purpose: This script sets the 'Comments' parameter of selected structural framing elements to their length.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    Parameter,
    StorageType,
    BuiltInCategory,
    BuiltInParameter,
    ElementId,
    Element,
    UnitUtils,
    UnitTypeId # Changed from DisplayUnitType for newer APIs if needed, assume internal units are fine
)
clr.AddReference('System.Collections')
from System.Collections.Generic import List

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

        # Check if the element exists and is a Structural Framing element (beam, brace, etc.)
        if element and element.Category and element.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFraming):
            try:
                # Get the Length parameter
                # CURVE_ELEM_LENGTH is often the most reliable for overall length
                length_param = element.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)

                # Fallback: Try STRUCTURAL_FRAME_CUT_LENGTH if the first one failed
                if not length_param or not length_param.HasValue:
                    length_param = element.get_Parameter(BuiltInParameter.STRUCTURAL_FRAME_CUT_LENGTH)

                # Fallback: Try looking up by name "Length"
                if not length_param or not length_param.HasValue:
                    length_param = element.LookupParameter("Length")

                # Get the Comments parameter
                comments_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

                # Proceed only if both parameters are found and valid
                if length_param and length_param.HasValue and length_param.StorageType == StorageType.Double and \
                   comments_param and not comments_param.IsReadOnly and comments_param.StorageType == StorageType.String:

                    length_value_internal = length_param.AsDouble() # Value is in internal units (decimal feet)

                    # Convert length value to string - keep it simple as internal value string
                    # Could format this differently if needed (e.g., with units)
                    length_str = str(length_value_internal)
                    # Alternative formatting (e.g., 4 decimal places):
                    # length_str = "{:.4f}".format(length_value_internal)

                    # Set the Comments parameter
                    comments_param.Set(length_str)
                    processed_count += 1
                else:
                    # print(f"# Skipping element ID {element.Id}: Could not find valid/writable Length or Comments parameter.")
                    skipped_count += 1

            except Exception as e:
                # print(f"# Error processing element ID {element.Id}: {e}")
                error_count += 1
        else:
            # Element is not structural framing
             skipped_count += 1
             # print(f"# Skipping element ID {element_id}: Not a Structural Framing element.")

    # Optional: Print summary
    # print(f"# Process finished. Updated: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")

# No EXPORT required, modifications are done in the model.