# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # For System.IO

# Import Revit API namespace
import Autodesk.Revit.DB as DB

import System.IO # For Path operations
import System # For Environment

# --- Configuration ---
# !!! USER: Define the exact name of the 3D view to use for generating the image !!!
view_name_to_render = "{{3D}} - Type Image Source" # Example Name - CHANGE THIS

# Define temporary image file path
temp_folder = System.IO.Path.GetTempPath()
temp_image_filename = "revit_type_image_temp.png"
temp_image_path = System.IO.Path.Combine(temp_folder, temp_image_filename)

# Image Export Settings
image_width_pixels = 512 # Adjust desired image width

# --- Script Core Logic ---

image_type_id = DB.ElementId.InvalidElementId
generated_image_path = None
view_found = False
new_image_type = None

# Find the specified 3D View
collector = DB.FilteredElementCollector(doc).OfClass(DB.View3D)
target_view = None
for view in collector:
    # Use view.Name property
    if view.Name == view_name_to_render and not view.IsTemplate:
        target_view = view
        view_found = True
        break

if not view_found:
    print("# Error: 3D View named '{{}}' not found or it's a template.".format(view_name_to_render))
else:
    try:
        # Configure Image Export Options
        export_options = DB.ImageExportOptions()
        export_options.FilePath = temp_image_path
        export_options.ExportRange = DB.ExportRange.CurrentView # Use CurrentView when exporting a single view
        export_options.PixelSize = image_width_pixels
        export_options.ImageResolution = DB.ImageResolution.DPI_72 # Lower DPI is usually fine for thumbnails
        export_options.FitDirection = DB.FitDirectionType.Horizontal # Fit width
        # Qualify HLRAndWFMode
        export_options.HLRandWFMode = DB.HLRandWFMode.RemoveLines # Might improve appearance
        export_options.ShadowViews = False # Typically false for type images
        export_options.ImageFileType = DB.ImageFileType.PNG # PNG supports transparency if needed

        # Set the view to a visual style suitable for type images (e.g., Shaded or Realistic)
        original_display_style = target_view.DisplayStyle
        original_visual_style = target_view.get_Parameter(DB.BuiltInParameter.VIEW_VISUAL_STYLE).AsElementId() # Store the VisualStyle too if DisplayStyle change fails

        new_display_style_set = False
        try:
            # Qualify DisplayStyle
            target_view.DisplayStyle = DB.DisplayStyle.Realistic
            new_display_style_set = True
        except:
            try:
                # Qualify DisplayStyle
                target_view.DisplayStyle = DB.DisplayStyle.Shaded
                new_display_style_set = True
            except Exception as style_err:
                 print("# Warning: Could not set view DisplayStyle to Realistic or Shaded. Using current style. Error: {{}}".format(style_err))

        # Ensure the correct view is active or specified if needed.
        # For ExportRange.CurrentView, Revit *should* use the view context from which the script is run,
        # but explicitly activating or specifying can be safer if issues arise.
        # Here, we will pass the view ID directly to ExportImage, which is more robust.
        # Note: doc.ExportImage(options) uses the active view if options.ExportRange is CurrentView and no views are set.
        # To reliably export *our* target_view, we should set it in the options.

        # Create a list containing the target view ID
        view_id_list = System.Collections.Generic.List[DB.ElementId]([target_view.Id])
        export_options.SetViewsAndSheets(view_id_list)
        # When specifying views/sheets, ExportRange should NOT be CurrentView.
        export_options.ExportRange = DB.ExportRange.SetOfViews # Change this

        # Export the image
        print("# Exporting image from view '{{}}' to '{{}}'...".format(view_name_to_render, temp_image_path))
        doc.ExportImage(export_options)
        generated_image_path = temp_image_path
        print("# Image exported successfully.")

        # Restore original visual style / display style
        if new_display_style_set:
            try:
                target_view.DisplayStyle = original_display_style
            except Exception as restore_err:
                print("# Warning: Could not restore original view DisplayStyle. Error: {{}}".format(restore_err))
        # Attempt to restore Visual Style using parameter if DisplayStyle was used
        # This might be redundant or potentially conflict, depending on how Revit handles these internally.
        # Testing needed to confirm if restoring DisplayStyle is sufficient.
        # try:
        #     style_param = target_view.get_Parameter(DB.BuiltInParameter.VIEW_VISUAL_STYLE)
        #     if style_param and not style_param.IsReadOnly:
        #          style_param.Set(original_visual_style)
        # except Exception as restore_vs_err:
        #     print("# Warning: Could not restore original Visual Style via parameter. Error: {}".format(restore_vs_err))


        # Create ImageType from the exported file
        print("# Creating ImageType from '{{}}'...".format(generated_image_path))
        # Qualify ImageType
        # Check if an ImageType with the same path already exists to avoid duplicates
        img_collector = DB.FilteredElementCollector(doc).OfClass(DB.ImageType)
        existing_image_type = None
        img_name = System.IO.Path.GetFileNameWithoutExtension(temp_image_filename) # Base name for ImageType
        for img_type in img_collector:
             # Comparing path or name might be unreliable. Creating a new one might be safer.
             # Revit typically names the ImageType based on the filename.
             if img_type.Name == img_name:
                 # Found a potential match, but is it the same? Reloading might be needed.
                 # For simplicity, let's always create a new one.
                 pass

        # It's generally better to create a new ImageType if the source image might have changed.
        # Revit might handle duplicates internally by reusing existing ones if the path matches,
        # but creating explicitly ensures we have a handle to *an* ImageType representing the file.
        new_image_type = DB.ImageType.Create(doc, generated_image_path)

        if new_image_type:
            image_type_id = new_image_type.Id
            print("# ImageType created/retrieved successfully (ID: {{}}).".format(image_type_id))
            # Rename the ImageType to avoid generic names like "revit_type_image_temp"
            try:
                new_image_type_name = "Type Image - " + view_name_to_render
                # Ensure name uniqueness if necessary
                name_param = new_image_type.get_Parameter(DB.BuiltInParameter.DATUM_TEXT) # Name param for ImageType
                if name_param:
                    name_param.Set(new_image_type_name)
                    print("# Renamed ImageType to '{}'".format(new_image_type_name))
            except Exception as rename_err:
                print("# Warning: Could not rename the created ImageType. Error: {}".format(rename_err))
        else:
            print("# Error: Failed to create ImageType from the exported image.")

    except Exception as export_create_err:
        print("# Error during image export or ImageType creation: {{}}".format(export_create_err))
        # Attempt cleanup if export failed mid-way or before ImageType creation
        if generated_image_path and System.IO.File.Exists(generated_image_path):
             try:
                 System.IO.File.Delete(generated_image_path)
                 print("# Cleaned up temporary image file due to error.")
             except Exception as cleanup_err:
                 print("# Error cleaning up temporary image file '{{}}': {{}}".format(generated_image_path, cleanup_err))
        generated_image_path = None # Ensure we don't try to use it later
    finally:
        # Ensure original display style is restored even if ImageType creation fails
        if view_found and target_view and new_display_style_set: # Check if target_view exists
            try:
                if target_view.DisplayStyle != original_display_style:
                    target_view.DisplayStyle = original_display_style
                    # print("# Restored original display style in finally block.") # Optional debug info
            except Exception as final_restore_err:
                print("# Warning: Could not restore original view DisplayStyle in finally block. Error: {{}}".format(final_restore_err))


# Apply the created ImageType to FamilySymbols (Family Types)
# Qualify ElementId, FilteredElementCollector, FamilySymbol, BuiltInParameter
if new_image_type and image_type_id != DB.ElementId.InvalidElementId:
    print("# Applying ImageType to Family Symbols...")
    family_symbol_collector = DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol)
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for fs in family_symbol_collector:
        if not isinstance(fs, DB.FamilySymbol): # Qualify FamilySymbol
            continue

        # Check if the family type has the 'Type Image' parameter
        # Qualify BuiltInParameter
        param = fs.get_Parameter(DB.BuiltInParameter.TYPE_IMAGE)
        if param and not param.IsReadOnly:
            try:
                # Check if update is needed (avoids unnecessary transaction entries)
                current_image_id = param.AsElementId()
                # Qualify ElementId
                if current_image_id != image_type_id:
                    param.Set(image_type_id)
                    updated_count += 1
                else:
                    skipped_count += 1 # Already has the correct image
            except Exception as set_param_err:
                # Use fs.Name
                print("# Error setting Type Image for Family Type '{{}}' (ID: {{}}): {{}}".format(fs.Name, fs.Id, set_param_err))
                error_count += 1
        else:
            # print("# Skipping Family Type '{{}}' (ID: {{}}): Type Image parameter not found or read-only.".format(fs.Name, fs.Id))
            skipped_count += 1 # Parameter doesn't exist or cannot be set

    print("# --- Summary ---")
    print("# Family Symbols Updated: {{}}".format(updated_count))
    print("# Family Symbols Skipped (No param/Read-only/Already set): {{}}".format(skipped_count))
    print("# Errors setting parameter: {{}}".format(error_count))

# Clean up the temporary image file *after* it has been loaded into the ImageType
# Deleting it before the transaction commits might cause issues if Revit hasn't fully processed it.
# However, ImageType.Create copies the image data, so deleting immediately should be okay.
if generated_image_path and System.IO.File.Exists(generated_image_path):
    try:
        System.IO.File.Delete(generated_image_path)
        print("# Cleaned up temporary image file '{{}}'.".format(generated_image_path))
    except Exception as cleanup_err:
        print("# Error cleaning up temporary image file '{{}}': {{}}".format(generated_image_path, cleanup_err))
elif view_found and not generated_image_path and image_type_id == DB.ElementId.InvalidElementId:
     # Only print this if export failed *before* image creation
     print("# No temporary image file to clean up (export/creation might have failed).")

if not view_found:
    print("# Script finished: Target view not found.")
elif not new_image_type:
     print("# Script finished: Failed to create ImageType.")
else:
    print("# Script finished.")