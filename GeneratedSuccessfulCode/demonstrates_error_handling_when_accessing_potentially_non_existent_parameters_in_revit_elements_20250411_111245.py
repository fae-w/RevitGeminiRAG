# Purpose: This script demonstrates error handling when accessing potentially non-existent parameters in Revit elements.

# Purpose: This script iterates through all Revit elements, attempts to access a specific parameter (likely to be missing on many elements), and demonstrates error handling for the AttributeError that occurs when accessing properties of a non-existent parameter.

﻿# Import necessary classes
from Autodesk.Revit.DB import FilteredElementCollector, Element, BuiltInParameter, Parameter

# Collect *all* elements in the model (can be very large)
# This broad collection increases the chance of encountering an element
# that does not have the specific parameter we will query.
collector = FilteredElementCollector(doc).WhereElementIsNotElementType()

processed_count = 0
error_triggered = False

# Iterate through elements and attempt an operation likely to fail on some element types
for elem in collector:
    processed_count += 1
    try:
        # Attempt to get a parameter that is often specific to certain categories
        # like Rooms or Areas (BuiltInParameter.ROOM_AREA used here as an example).
        # Many other element types will not have this parameter.
        area_param = elem.get_Parameter(BuiltInParameter.ROOM_AREA)

        # THE INTENDED POINT OF FAILURE:
        # If 'area_param' is None (because the element doesn't have it),
        # attempting to access '.AsDouble()' will raise an AttributeError.
        # This is a common type of error in Revit API scripting when
        # assumptions about element parameters are incorrect.
        area_value = area_param.AsDouble()

        # This line will likely only be reached for elements that *do* have the parameter
        # print("# Element {} has area: {}".format(elem.Id, area_value)) # Optional debug output

    except AttributeError:
        # This is the expected error when area_param is None
        print("# Error: Encountered AttributeError, likely accessing a property on a None object (parameter not found) for element ID: {}".format(elem.Id)) # Escaped
        error_triggered = True
        # Stop the script after the first expected error is encountered
        break
    except Exception as e:
        # Catch any other potential errors during processing
        print("# An unexpected error occurred processing element ID {}: {}".format(elem.Id, e)) # Escaped
        error_triggered = True
        # Stop the script after any error
        break

# Final status message
if not error_triggered:
    print("# Script completed processing {} elements without triggering the intended error.".format(processed_count)) # Escaped
else:
    print("# Script stopped due to an error after processing {} elements.".format(processed_count)) # Escaped