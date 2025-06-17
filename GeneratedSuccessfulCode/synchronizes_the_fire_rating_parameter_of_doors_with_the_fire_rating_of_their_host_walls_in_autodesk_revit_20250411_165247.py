# Purpose: This script synchronizes the 'Fire Rating' parameter of doors with the 'Fire Rating' of their host walls in Autodesk Revit.

﻿# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Although not strictly needed for DB operations, good practice if uidoc might be used later
from Autodesk.Revit.DB import *
from Autodesk.Revit.Exceptions import InvalidOperationException

# --- Parameters ---
# Assumption: Wall Fire Rating is stored in the built-in 'Fire Rating' parameter.
wall_rating_bip = BuiltInParameter.FIRE_RATING
# Assumption: Door Fire Rating is also stored in the built-in 'Fire Rating' parameter.
# Note: Changed from DOOR_FIRE_RATING based on typical usage and original request wording.
door_rating_bip = BuiltInParameter.FIRE_RATING

# --- Counters ---
updated_doors_count = 0
skipped_doors_count = 0
processed_doors_count = 0

# --- Main Logic ---
# Collect all door instances in the model
# Use ElementClassFilter for potentially better performance than OfCategory with WhereElementIsNotElementType
door_collector = FilteredElementCollector(doc).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

# Ensure we are iterating over actual Element objects
for door in door_collector:
    processed_doors_count += 1
    # It's generally safer to work directly with the Element object unless specific Door properties are needed
    # The collector already filters for Doors, so the isinstance check might be redundant but harmless
    try:
        # Get the host element of the door
        host_element = doc.GetElement(door.HostElementId) # Use HostElementId for more reliability

        # Check if the host is a Wall
        if host_element and isinstance(host_element, Wall):
            wall = host_element

            # Get the wall's Fire Rating parameter
            wall_param = wall.get_Parameter(wall_rating_bip)

            # Check if the wall parameter exists, has a value, and is a string
            if wall_param and wall_param.HasValue:
                 # Check StorageType AFTER confirming HasValue
                 if wall_param.StorageType == StorageType.String:
                    wall_rating_value = wall_param.AsString()

                    # Proceed only if the wall rating is not null or empty
                    if wall_rating_value:
                        # Get the door's Fire Rating parameter
                        door_param = door.get_Parameter(door_rating_bip)

                        # Check if the door parameter exists, is writable, and is a string type
                        if door_param and not door_param.IsReadOnly:
                            if door_param.StorageType == StorageType.String:
                                current_door_rating = door_param.AsString()
                                # Update only if the door's rating is different from the wall's rating
                                # Handle potential None comparison
                                if current_door_rating != wall_rating_value:
                                    try:
                                        result = door_param.Set(wall_rating_value)
                                        if result: # Set returns True on success
                                            updated_doors_count += 1
                                        else:
                                            # Failed to set for some reason (e.g., value invalid for param)
                                            skipped_doors_count += 1
                                    except InvalidOperationException:
                                        # Catch specific exception if setting fails due to context (e.g., Revit constraint)
                                        skipped_doors_count += 1
                                # else: Door rating already matches
                            else:
                                skipped_doors_count += 1 # Door parameter not string
                        else:
                            skipped_doors_count += 1 # Door parameter doesn't exist or is read-only
                    else:
                         skipped_doors_count += 1 # Wall rating value is empty
                 else:
                    skipped_doors_count += 1 # Wall parameter not string
            else:
                skipped_doors_count += 1 # Wall parameter doesn't exist or has no value
        else:
             skipped_doors_count += 1 # Host is not a wall or no host found

    except Exception as e:
        # Catch any unexpected errors during processing for a specific door
        # Use __revit__.Application.Username or similar to help identify user in logs if needed
        # print("Error processing Door ID {}: {}".format(door.Id, e)) # Optional Debug - Keep commented out for final submission
        skipped_doors_count += 1


# --- Final Output ---
# Use standard Python string formatting available in IronPython 2.7
print("# Processed {} doors.".format(processed_doors_count))
print("# Successfully updated 'Fire Rating' for {} doors.".format(updated_doors_count))
if skipped_doors_count > 0:
    print("# Skipped {} doors due to missing host, host not being a wall, missing/invalid/read-only parameters, empty wall rating, or other errors.".format(skipped_doors_count))