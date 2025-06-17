# Purpose: This script updates the image parameter of Revit furniture types based on a provided mapping of type names to image paths.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for String, Exception, IO
clr.AddReference('System.Drawing') # Required for Bitmap, though we don't load it directly, ImageType.Create needs it implicitly

from System import String, Exception as SystemException
from System.IO import File, Path

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementType,
    FamilySymbol, # Furniture types are FamilySymbols
    Parameter,
    StorageType,
    BuiltInParameter,
    Element,
    ElementId,
    ImageType,
    ImageTypeOptions
)

# --- Input Data ---
# Format: TypeName,ImagePath (one entry per line)
# Ensure paths are valid and accessible from where the script runs (e.g., server path if running on Revit Server context)
# Use raw strings (r"...") or double backslashes (\\) for Windows paths.
input_data_string = r"""Standard Chair,C:\Path\To\Images\chair_image.png
Modern Desk - 1600x800,C:\Path\To\Images\desk_modern_1600.jpg
Conference Table - Large,C:\Path\To\Images\conf_table_large.bmp"""

# --- Initialization ---
type_image_map = {}
update_log = [] # To track successes and failures
created_image_types = {} # Dictionary to store {ImagePath: ImageTypeId} to avoid creating duplicates

# --- Step 1: Parse the input data ---
try:
    lines = input_data_string.strip().split('\n')
    for line in lines:
        if ',' in line:
            parts = line.split(',', 1) # Split only on the first comma
            type_name = parts[0].strip()
            image_path = parts[1].strip()
            if type_name and image_path: # Ensure both parts are not empty
                type_image_map[type_name] = image_path
            else:
                update_log.append("# Warning: Skipping invalid line in input data: '{}'".format(line))
        else:
            update_log.append("# Warning: Skipping invalid line in input data (no comma found): '{}'".format(line))
except Exception as parse_ex:
    print("# Error: Failed to parse input data string: {}".format(parse_ex))
    # Stop execution if parsing fails fundamentally
    type_image_map = {} # Clear the map to prevent incorrect updates

# --- Step 2: Pre-create ImageTypes for unique, valid paths ---
if type_image_map:
    unique_paths = set(type_image_map.values())
    for image_path in unique_paths:
        try:
            if not Path.IsPathRooted(image_path):
                 update_log.append("# Warning: Image path '{}' is not absolute. Revit might not find it.".format(image_path))
                 # Continue trying, but it might fail

            if File.Exists(image_path):
                # Check if an ImageType for this path was already created in this run
                if image_path not in created_image_types:
                    options = ImageTypeOptions()
                    options.SetImageSamplingRate(1.0) # Optional: Set properties if needed
                    new_image_type = ImageType.Create(doc, image_path, options)
                    if new_image_type:
                        created_image_types[image_path] = new_image_type.Id
                        update_log.append("# Info: Successfully created ImageType for path: '{}' (ID: {})".format(image_path, new_image_type.Id))
                    else:
                         update_log.append("# Error: Failed to create ImageType for path: '{}'. ImageType.Create returned None.".format(image_path))
            else:
                update_log.append("# Error: Image file not found at path: '{}'. Skipping this image.".format(image_path))
        except SystemException as img_ex:
            update_log.append("# Error creating ImageType for path '{}': {}".format(image_path, img_ex.Message))

# --- Step 3: Collect Furniture Types ---
furniture_types = []
if type_image_map: # Proceed only if parsing was successful and yielded data
    try:
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Furniture).WhereElementIsElementType()
        furniture_types = list(collector)
    except SystemException as col_ex:
        print("# Error collecting Furniture Types: {}".format(col_ex.Message))
        furniture_types = [] # Ensure loop doesn't run if collection failed

# --- Step 4: Iterate and Update Furniture Types ---
if furniture_types and type_image_map and created_image_types:
    updated_count = 0
    target_parameter_bip = BuiltInParameter.FAMILY_IMAGE # Built-in parameter for the type image

    for ft_element in furniture_types:
        # Ensure it's an ElementType or derived class like FamilySymbol
        if not isinstance(ft_element, ElementType):
            continue

        try:
            # Get the type name
            element_name = Element.Name.GetValue(ft_element)

            # Check if this type name is in our map
            if element_name in type_image_map:
                target_image_path = type_image_map[element_name]

                # Check if we successfully created an ImageType for this path
                if target_image_path in created_image_types:
                    target_image_type_id = created_image_types[target_image_path]

                    # Get the 'Image' parameter (FAMILY_IMAGE)
                    image_param = ft_element.get_Parameter(target_parameter_bip)

                    if image_param is None:
                        update_log.append("# Error: Furniture Type '{}' (ID: {}) does not have the 'Image' (FAMILY_IMAGE) parameter.".format(element_name, ft_element.Id))
                    elif image_param.IsReadOnly:
                        update_log.append("# Error: 'Image' parameter for Furniture Type '{}' (ID: {}) is read-only.".format(element_name, ft_element.Id))
                    elif image_param.StorageType != StorageType.ElementId:
                        update_log.append("# Error: 'Image' parameter for Furniture Type '{}' (ID: {}) is not an ElementId type (Actual: {}).".format(element_name, ft_element.Id, image_param.StorageType))
                    else:
                        # Set the new value (the ID of the ImageType)
                        current_value_id = image_param.AsElementId()
                        if current_value_id != target_image_type_id:
                             set_result = image_param.Set(target_image_type_id)
                             if set_result:
                                 update_log.append("# Success: Updated 'Image' for '{}' (ID: {}) to ImageType ID: {}.".format(element_name, ft_element.Id, target_image_type_id))
                                 updated_count += 1
                             else:
                                 update_log.append("# Error: Failed to set 'Image' for '{}' (ID: {}). Parameter.Set returned False.".format(element_name, ft_element.Id))
                        else:
                             update_log.append("# Info: 'Image' for '{}' (ID: {}) is already set to ImageType ID: {}.".format(element_name, ft_element.Id, target_image_type_id))
                else:
                    # Image path was invalid or ImageType creation failed earlier
                    update_log.append("# Warning: Skipping update for '{}' (ID: {}) because its image path '{}' was invalid or ImageType creation failed.".format(element_name, ft_element.Id, target_image_path))

        except SystemException as param_ex:
            try:
                element_name_err = Element.Name.GetValue(ft_element) if ft_element else "Unknown Type"
                update_log.append("# Error processing Furniture Type '{}' (ID: {}): {}".format(element_name_err, ft_element.Id if ft_element else "N/A", param_ex.Message))
            except:
                 update_log.append("# Error processing an unknown Furniture Type: {}".format(param_ex.Message))

# --- Final Feedback ---
if not type_image_map and not update_log:
     print("# Error: Input data parsing failed or resulted in no valid entries.")
elif not furniture_types and type_image_map:
     print("# Info: No Furniture Types found in the document to process.")
elif not created_image_types and type_image_map:
     print("# Error: No valid image paths found or ImageTypes could be created from the input.")
elif not update_log and furniture_types and type_image_map:
     print("# Info: No Furniture Types matching the provided names were found or needed updating, or image creation failed for all.")
else:
    # Print the collected log messages
    for log_entry in update_log:
        print(log_entry)
    print("# --- Update process finished. ---")