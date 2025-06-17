# Purpose: This script renames CAD link types in a Revit model to match their base file names.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
clr.AddReference('System.IO') # Required for Path operations
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    CADLinkType,
    Element,
    ExternalFileReference,
    ModelPathUtils,
    ElementId # Not strictly needed here but good practice
)
import System # For Exception handling
import System.IO # For Path class

# --- Initialization ---
renamed_count = 0
skipped_count = 0 # Already named correctly or is an import/invalid link
error_count = 0
processed_count = 0
errors = []

# --- Step 1: Collect CADLinkType elements ---
# CADLinkType represents both linked and imported CAD files.
collector = FilteredElementCollector(doc).OfClass(CADLinkType)
cad_link_types = list(collector)

if not cad_link_types:
    print("# No CADLinkType elements found in the project.")
else:
    print("# Found {} CADLinkType elements. Processing...".format(len(cad_link_types)))

    # --- Step 2: Iterate and Rename ---
    for link_type in cad_link_types:
        processed_count += 1
        original_name = None
        ext_ref = None
        model_path = None
        path_str = None
        base_name = None

        try:
            # --- Step 2a: Get Original Name ---
            try:
                original_name = Element.Name.GetValue(link_type) # Use static method for safety
                if not original_name:
                     original_name = "UnnamedLinkType{}".format(link_type.Id.IntegerValue) # Handle empty name case
            except Exception as name_ex:
                error_count += 1
                errors.append("# Error getting name for CADLinkType ID {}: {}".format(link_type.Id, name_ex))
                continue # Skip to next link type

            # --- Step 2b: Get External File Reference to distinguish links from imports ---
            # Imports don't have a typical external file reference pointing to the original file.
            # GetExternalFileReference is inherited from Element.
            try:
                ext_ref = link_type.GetExternalFileReference()
                if ext_ref is None:
                    # This is likely an imported CAD file, not a link. Skip it.
                    skipped_count += 1
                    # print("# Skipping CADLinkType '{}' (ID: {}): Not an external link (likely import).".format(original_name, link_type.Id)) # Debug
                    continue
            except Exception as ext_ref_ex:
                 error_count += 1
                 errors.append("# Error getting ExternalFileReference for '{}' (ID: {}): {}".format(original_name, link_type.Id, ext_ref_ex))
                 continue

            # --- Step 2c: Get Path and Extract Base Name ---
            try:
                model_path = ext_ref.GetPath()
                path_str = ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)

                if not path_str:
                    error_count += 1
                    errors.append("# Error: Could not get valid path string for '{}' (ID: {}).".format(original_name, link_type.Id))
                    continue

                # Use System.IO.Path to reliably get the name without extension
                base_name = System.IO.Path.GetFileNameWithoutExtension(path_str)

                if not base_name:
                    error_count += 1
                    errors.append("# Error: Could not extract base file name from path '{}' for '{}' (ID: {}).".format(path_str, original_name, link_type.Id))
                    continue

            except Exception as path_ex:
                error_count += 1
                errors.append("# Error processing path for '{}' (ID: {}): {}".format(original_name, link_type.Id, path_ex))
                continue

            # --- Step 2d: Compare and Rename ---
            if original_name != base_name:
                try:
                    link_type.Name = base_name
                    renamed_count += 1
                    # print("# Renamed CADLinkType '{}' to '{}' (ID: {})".format(original_name, base_name, link_type.Id)) # Debug
                except System.ArgumentException as arg_ex:
                    error_count += 1
                    error_msg = "# Rename Error: CADLinkType '{}' (ID: {}) to '{}': {}. (Likely duplicate name)".format(original_name, link_type.Id, base_name, arg_ex.Message)
                    errors.append(error_msg)
                    print(error_msg) # Print critical errors immediately
                except Exception as rename_ex:
                    error_count += 1
                    error_msg = "# Rename Error: CADLinkType '{}' (ID: {}) to '{}': {}".format(original_name, link_type.Id, base_name, rename_ex)
                    errors.append(error_msg)
                    print(error_msg) # Print critical errors immediately
            else:
                # Name already matches the base file name
                skipped_count += 1
                # print("# Skipping CADLinkType '{}' (ID: {}): Name already matches base file name.".format(original_name, link_type.Id)) # Debug

        except Exception as outer_ex:
             # Catch errors during processing before rename attempt
             error_count += 1
             error_msg = "# Unexpected Error processing CADLinkType ID {}: {}".format(link_type.Id, outer_ex)
             errors.append(error_msg)
             print(error_msg) # Print critical errors immediately

    # --- Final Summary ---
    print("\n# --- CAD Link Renaming Summary ---")
    print("# Total CADLinkType elements processed: {}".format(processed_count))
    print("# Successfully renamed: {}".format(renamed_count))
    print("# Skipped (already correct name, import, or invalid): {}".format(skipped_count))
    print("# Errors encountered: {}".format(error_count))

    # if errors:
    #     print("\n# --- Encountered Errors ---")
    #     for error in errors:
    #         print(error)

    print("# Note: Only actual CAD Links were processed. Imported CAD files were skipped.")