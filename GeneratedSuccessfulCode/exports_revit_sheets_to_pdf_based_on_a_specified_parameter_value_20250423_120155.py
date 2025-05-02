# Purpose: This script exports Revit sheets to PDF based on a specified parameter value.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Needed for Environment
import Autodesk.Revit.DB as DB
from System.Collections.Generic import List
from System import Environment # For default path

# --- Configuration ---
param_name = "Include in Permit Set"
output_file_name_base = "Permit_Set" # Just the base name, .pdf is added by Export

# --- Default Output Folder (Needs adjustment in actual environment) ---
# Assume a variable 'output_folder' might be predefined in the C# host.
# If not, use a default like the Desktop. THIS MAY NEED TO BE CHANGED OR PROVIDED EXTERNALLY.
if 'output_folder' not in globals():
    try:
        output_folder = Environment.GetFolderPath(Environment.SpecialFolder.Desktop)
    except Exception as e:
        print("# Error: Could not get default Desktop path. Output folder must be defined externally (e.g., in C# host as 'output_folder').")
        output_folder = None # Indicate failure to determine path

# --- Sheet Collection and Filtering ---
sheets_to_export_ids = List[DB.ElementId]()
all_sheets = DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).WhereElementIsNotElementType().ToElements()

found_count = 0
error_count = 0

for sheet in all_sheets:
    if not isinstance(sheet, DB.ViewSheet) or not sheet.IsValidObject or sheet.IsPlaceholder: # Skip placeholder sheets
        continue
    try:
        param = sheet.LookupParameter(param_name)
        # Check if parameter exists, is Yes/No (Integer storage), and is checked (value == 1)
        if param and param.HasValue and param.StorageType == DB.StorageType.Integer and param.AsInteger() == 1:
            sheets_to_export_ids.Add(sheet.Id)
            found_count += 1
        elif param is None:
            pass # Parameter doesn't exist on this sheet
        elif not param.HasValue:
             pass # Parameter exists but has no value

    except Exception as e:
        error_count += 1
        # Consider logging this error if needed in a real scenario
        # print("# Warning: Error processing sheet {} ({}): {}".format(sheet.Id, sheet.Name, e))

# --- Export Process ---
if sheets_to_export_ids.Count > 0:
    if output_folder and isinstance(output_folder, str) and len(output_folder) > 0:
        # Create ViewSet
        view_set_to_export = DB.ViewSet()
        valid_view_elements_found = False
        for sheet_id in sheets_to_export_ids:
            view_element = doc.GetElement(sheet_id)
            # Ensure element exists and is a View (Sheet inherits from View)
            if view_element and isinstance(view_element, DB.View):
                 view_set_to_export.Insert(view_element)
                 valid_view_elements_found = True

        if not valid_view_elements_found: # Check if any valid Views were actually added
             print("# Error: Could not retrieve valid View elements for the selected Sheet IDs.")
        else:
            # Configure PDF Export Options
            export_options = DB.PDFExportOptions()
            export_options.Combine = True
            export_options.FileName = output_file_name_base # Set the base file name
            export_options.ExportQuality = DB.PDFExportQuality.High
            export_options.PaperFormat = DB.PDFPaperFormat.UseSheetSize # Use individual sheet sizes
            export_options.ZoomType = DB.PDFZoomType.Zoom # Use Zoom instead of FitToPage, works well with UseSheetSize
            export_options.ZoomPercentage = 100
            export_options.PaperPlacement = DB.PaperPlacementType.Center # Place sheet content centered on the paper
            export_options.HideScopeBoxes = True
            export_options.HideReferencePlanes = True
            export_options.HideUnreferencedViewTags = True
            export_options.HideCropBoundaries = True # Often desired for permit sets
            export_options.ColorMode = DB.PDFColorModeType.Color # Or use DB.PDFColorModeType.BlackAndWhite / DB.PDFColorModeType.GrayScale
            # export_options.AlwaysUseRaster = False # Typically default, set to True if vector processing causes issues
            # export_options.ViewLinksinBlue = False # Set True if needed

            try:
                # Export the PDF using the correct overload: Export(string folder, string name, ViewSet views, PDFExportOptions options)
                doc.Export(output_folder, output_file_name_base, view_set_to_export, export_options)
                # Success: No output needed unless explicitly requested or for debugging.
                pass
            except Exception as export_error:
                print("# Error: Failed to export PDF. Check write permissions for '{}'.".format(output_folder))
                # print("# Export error details: {}".format(export_error)) # Uncomment for debugging if needed
    else:
        print("# Error: Output folder is not defined, invalid, or could not be determined. Cannot export PDF.")

elif error_count > 0:
     print("# No sheets found with '{}' checked, and {} errors occurred during processing.".format(param_name, error_count))
else:
    # No sheets selected and no errors, so no action needed, no output required.
    pass