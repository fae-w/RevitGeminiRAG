# Purpose: This script updates the 'Fire Rating' parameter of a Revit door based on its 'Mark' value.

﻿# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    BuiltInParameter,
    Parameter,
    StorageType,
    ParameterValueProvider,
    FilterStringRule,
    FilterStringEquals,
    ElementParameterFilter
)
import System # For exception handling

# --- Configuration ---
target_mark_value = "D-101"
fire_rating_value_to_set = "60 min"

# Parameter identifiers
mark_param_bip = BuiltInParameter.ALL_MODEL_MARK # Common parameter for 'Mark'
fire_rating_param_bip = BuiltInParameter.FIRE_RATING

# --- Status Flags/Counters ---
door_found = False
update_successful = False
error_message = None

# --- Main Logic ---
try:
    # Build filter for the 'Mark' parameter
    # 1. Parameter Value Provider for Mark
    mark_pvp = ParameterValueProvider(mark_param_bip)
    # 2. String comparison rule (case-sensitive, use FilterStringEquals() for case-insensitive if needed)
    mark_evaluator = FilterStringEquals() # Case-sensitive comparison
    # 3. Filter rule comparing the parameter value with the target mark
    mark_rule = FilterStringRule(mark_pvp, mark_evaluator, target_mark_value)
    # 4. Element Parameter Filter based on the rule
    mark_filter = ElementParameterFilter(mark_rule)

    # Create a collector for door instances matching the Mark value
    collector = FilteredElementCollector(doc)\
                .OfCategory(BuiltInCategory.OST_Doors)\
                .WhereElementIsNotElementType()\
                .WherePasses(mark_filter)

    # Get the first matching door (assuming Mark is unique)
    door_element = collector.FirstOrDefault()

    if door_element:
        door_found = True
        # Ensure it's a FamilyInstance, though the category filter should handle this
        if isinstance(door_element, FamilyInstance):
            # Get the 'Fire Rating' parameter
            fire_rating_param = door_element.get_Parameter(fire_rating_param_bip)

            if fire_rating_param:
                if fire_rating_param.IsReadOnly:
                    error_message = "Error: 'Fire Rating' parameter is read-only."
                elif fire_rating_param.StorageType != StorageType.String:
                    error_message = "Error: 'Fire Rating' parameter is not a Text type (expected String)."
                else:
                    try:
                        set_result = fire_rating_param.Set(fire_rating_value_to_set)
                        if set_result:
                            update_successful = True
                        else:
                            # Parameter.Set returns false if the value is invalid for the parameter type
                            error_message = "Error: Failed to set 'Fire Rating' parameter (possibly invalid value or internal constraint)."
                    except Exception as set_ex:
                        error_message = "Error setting 'Fire Rating' parameter: {}".format(str(set_ex))
            else:
                error_message = "Error: Door instance found, but 'Fire Rating' parameter does not exist on it."
        else:
             error_message = "Error: Found element with Mark '{}' but it is not a FamilyInstance.".format(target_mark_value) # Should not happen with OST_Doors filter
    else:
        error_message = "Error: Door with Mark '{}' not found in the document.".format(target_mark_value)

except System.Exception as ex:
    error_message = "An unexpected error occurred: {}".format(str(ex))

# --- Final Output ---
if update_successful:
    print("Successfully set 'Fire Rating' to '{}' for door with Mark '{}'.".format(fire_rating_value_to_set, target_mark_value))
elif door_found:
    print("Found door with Mark '{}', but could not update 'Fire Rating'.".format(target_mark_value))
    if error_message:
        print(error_message)
else:
    # Door not found message is already in error_message if that was the case
    if error_message:
        print(error_message)
    else:
        print("Door with Mark '{}' not found.".format(target_mark_value)) # Fallback message