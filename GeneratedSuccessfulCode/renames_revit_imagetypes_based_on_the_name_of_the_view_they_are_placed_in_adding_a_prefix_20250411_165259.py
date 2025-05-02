# Purpose: This script renames Revit ImageTypes based on the name of the view they are placed in, adding a prefix.

﻿# Imports
import clr
clr.AddReference('System') # Required for Exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ImageInstance,
    ImageType,
    View,
    ElementId,
    BuiltInCategory,
    Element
)
import System # For Exception handling

# --- Configuration ---
new_prefix = "IMG_"

# --- Initialization ---
renamed_count = 0
already_prefixed_count = 0
skipped_no_view_count = 0
skipped_no_type_count = 0
failed_count = 0
processed_image_type_ids = set() # Keep track of types already renamed
errors = []

# --- Step 1: Collect all Image Instances ---
collector = FilteredElementCollector(doc).OfClass(ImageInstance) # More specific than category
# collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_RasterImages).WhereElementIsNotElementType() # Alternative
image_instances = list(collector)

if not image_instances:
    print("# No ImageInstance elements found in the project.")
else:
    print("# Found {} ImageInstance elements. Processing...".format(len(image_instances)))

    # --- Step 2: Iterate through Image Instances ---
    for img_instance in image_instances:
        image_type = None
        image_type_id = ElementId.InvalidElementId
        owner_view = None
        original_type_name = None

        try:
            # --- Step 2a: Get associated ImageType ---
            image_type_id = img_instance.GetTypeId()
            if image_type_id == ElementId.InvalidElementId:
                skipped_no_type_count += 1
                errors.append("# Skipped: ImageInstance ID {} has no valid TypeId.".format(img_instance.Id))
                continue

            # Check if this ImageType has already been processed/renamed
            if image_type_id in processed_image_type_ids:
                continue # Skip if already handled based on another instance

            image_type = doc.GetElement(image_type_id)
            if not image_type or not isinstance(image_type, ImageType):
                skipped_no_type_count += 1
                errors.append("# Skipped: Could not retrieve valid ImageType for ID {} (from Instance ID {}).".format(image_type_id, img_instance.Id))
                continue

            # Get original name for checks and messages
            try:
                original_type_name = Element.Name.GetValue(image_type) # Safer way to get name
            except Exception as name_ex:
                failed_count += 1
                errors.append("# Error getting name for ImageType ID {}: {}".format(image_type_id, name_ex))
                processed_image_type_ids.add(image_type_id) # Mark as processed even if failed
                continue

            # --- Step 2b: Check if already prefixed ---
            if original_type_name and original_type_name.startswith(new_prefix):
                already_prefixed_count += 1
                processed_image_type_ids.add(image_type_id) # Mark as processed
                continue

            # --- Step 2c: Get Owner View ---
            owner_view_id = img_instance.OwnerViewId
            if owner_view_id == ElementId.InvalidElementId:
                # This image instance isn't placed in a specific view (e.g., could be on a sheet directly? Unlikely for ImageInstance)
                # Or it might be associated with a view that got deleted.
                skipped_no_view_count += 1
                errors.append("# Skipped: ImageInstance ID {} (Type: '{}') has no valid OwnerViewId.".format(img_instance.Id, original_type_name))
                # Don't mark image_type_id as processed yet, another instance might have a view
                continue

            owner_view = doc.GetElement(owner_view_id)
            if not owner_view or not isinstance(owner_view, View):
                skipped_no_view_count += 1
                errors.append("# Skipped: Could not retrieve valid View (ID {}) for ImageInstance ID {} (Type: '{}').".format(owner_view_id, img_instance.Id, original_type_name))
                # Don't mark image_type_id as processed yet
                continue

            # --- Step 2d: Get View Name ---
            try:
                view_name = owner_view.Name
                if not view_name: # Handle empty view names
                     view_name = "UnnamedView{}".format(owner_view.Id.IntegerValue)
                     errors.append("# Warning: View ID {} has an empty name. Using default.".format(owner_view.Id))
            except Exception as view_name_ex:
                failed_count += 1
                errors.append("# Error getting name for View ID {}: {}".format(owner_view_id, view_name_ex))
                processed_image_type_ids.add(image_type_id) # Mark type as processed since we failed on view name
                continue

            # --- Step 2e: Construct New Name ---
            # Basic check for potentially problematic characters, although Revit often handles this
            safe_view_name = "".join(c for c in view_name if c.isalnum() or c in (' ', '_', '-'))
            new_name = new_prefix + safe_view_name
            # Optional: Truncate if too long (Revit might have limits)
            # max_len = 100
            # if len(new_name) > max_len:
            #     new_name = new_name[:max_len]

            # --- Step 2f: Attempt Rename ---
            try:
                # Use Element.Name property setter
                # Make sure it's not already named this way (avoids unnecessary transaction noise)
                if original_type_name != new_name:
                    image_type.Name = new_name
                    renamed_count += 1
                    # print("# Renamed ImageType '{}' to '{}' (ID: {}) based on View '{}'".format(original_type_name, new_name, image_type_id, view_name)) # Optional debug
                else:
                    # If the generated name happens to be the same as original, count as prefixed/skipped
                    already_prefixed_count += 1


                processed_image_type_ids.add(image_type_id) # Mark as successfully processed/renamed

            except System.ArgumentException as arg_ex:
                failed_count += 1
                error_msg = "# Rename Error: ImageType '{}' (ID: {}) to '{}': {}. (Likely duplicate name)".format(original_type_name, image_type_id, new_name, arg_ex.Message)
                errors.append(error_msg)
                print(error_msg) # Print immediately
                processed_image_type_ids.add(image_type_id) # Mark as processed even if failed rename

            except Exception as rename_ex:
                failed_count += 1
                error_msg = "# Rename Error: ImageType '{}' (ID: {}) to '{}': {}".format(original_type_name, image_type_id, new_name, rename_ex)
                errors.append(error_msg)
                print(error_msg) # Print immediately
                processed_image_type_ids.add(image_type_id) # Mark as processed even if failed rename

        except Exception as outer_ex:
             # Catch errors during instance processing (before rename attempt)
             failed_count += 1
             error_msg = "# Unexpected Error processing ImageInstance ID {}: {}".format(img_instance.Id, outer_ex)
             errors.append(error_msg)
             print(error_msg) # Print immediately
             # If we know the type ID, mark it as processed to avoid retries
             if image_type_id != ElementId.InvalidElementId:
                 processed_image_type_ids.add(image_type_id)


    # --- Final Summary ---
    print("\n# --- ImageType Renaming Summary ---")
    print("# Total ImageInstances found: {}".format(len(image_instances)))
    print("# Unique ImageTypes successfully renamed: {}".format(renamed_count))
    print("# ImageTypes already had the prefix '{}' or matched new name: {}".format(new_prefix, already_prefixed_count))
    print("# Instances skipped (no valid OwnerView): {}".format(skipped_no_view_count))
    print("# Instances skipped (no valid ImageType): {}".format(skipped_no_type_count))
    print("# ImageTypes failed during rename attempt (e.g., duplicates, errors): {}".format(failed_count))
    # Note: Counts might not sum perfectly if errors occurred before rename attempt

    # if errors:
    #     print("\n# --- Encountered Errors/Warnings ---")
    #     for error in errors:
    #         print(error)

    print("# Assumption: If an ImageType is used in multiple views, it was renamed based on the first encountered instance with a valid view.")