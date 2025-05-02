# Purpose: This script copies detail lines from the active drafting view to a specified library view.

# Purpose: This script copies detail lines from the active drafting view to a target drafting view named "Standard Details Library".

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    ElementTransformUtils,
    DetailLine,
    View,
    ViewType,
    XYZ,
    Transform,
    CopyPasteOptions,
    BuiltInCategory
)
from System.Collections.Generic import List

# --- Configuration ---
target_view_name = "Standard Details Library"

# --- Get Active View ---
source_view = None
source_view_name = "N/A"
try:
    active_view = uidoc.ActiveView
    if active_view is None:
        print("# Error: No active view found.")
    elif active_view.ViewType != ViewType.DraftingView:
        print("# Error: The active view '{}' is not a Drafting View.".format(active_view.Name))
    else:
        source_view = active_view
        source_view_name = source_view.Name
except Exception as e:
    print("# Error accessing active view: {}".format(e))

# --- Find Target View ---
target_view = None
if source_view: # Only proceed if active view is valid
    view_collector = FilteredElementCollector(doc).OfClass(View)
    found_target = False
    for v in view_collector:
        # Check if it's a drafting view and matches the name
        if v.ViewType == ViewType.DraftingView and not v.IsTemplate:
            if v.Name == target_view_name:
                # Check if it's the same as the source view
                if v.Id == source_view.Id:
                    print("# Error: Source and target views are the same ('{}'). Cannot copy.".format(target_view_name))
                else:
                    target_view = v
                found_target = True
                break # Exit loop once found

    if not found_target:
        print("# Error: Target drafting view '{}' not found.".format(target_view_name))
    elif not target_view:
        # This condition means the target was found but was the same as the source
        pass # Error already printed

# --- Get Detail Lines from Active View ---
detail_line_ids_list = None
elements_to_copy_count = 0
if source_view and target_view:
    # Collect DetailLine element IDs from the source view
    collector = FilteredElementCollector(doc, source_view.Id).OfClass(DetailLine).WhereElementIsNotElementType()
    detail_line_ids_icollection = collector.ToElementIds() # Returns ICollection<ElementId>

    if not detail_line_ids_icollection or detail_line_ids_icollection.Count == 0:
        print("# No Detail Lines found in the source view '{}'.".format(source_view_name))
    else:
        # Convert ICollection<ElementId> to List<ElementId> required by CopyElements
        detail_line_ids_list = List[ElementId](detail_line_ids_icollection)
        elements_to_copy_count = detail_line_ids_list.Count
        # print("# Found {} Detail Lines in '{}' to copy.".format(elements_to_copy_count, source_view_name)) # Optional debug

# --- Copy Elements ---
copied_elements_count = 0
if source_view and target_view and detail_line_ids_list and elements_to_copy_count > 0:
    try:
        # Use Identity transform: copies elements maintaining their positions relative to the view origin
        copy_transform = Transform.Identity
        # Use default CopyPasteOptions
        copy_options = CopyPasteOptions()
        # copy_options.SetDuplicateTypeNamesHandler(YourCustomHandler()) # Add if needed

        # Perform the copy operation (runs within the C# transaction wrapper)
        copied_ids = ElementTransformUtils.CopyElements(
            source_view,          # Source View object
            detail_line_ids_list, # List<ElementId> of elements to copy
            target_view,          # Destination View object
            copy_transform,       # Transform to apply (Identity for same relative position)
            copy_options          # CopyPasteOptions
        )
        copied_elements_count = copied_ids.Count
        # print("# Successfully copied {} Detail Lines from '{}' to '{}'.".format(copied_elements_count, source_view_name, target_view_name)) # Optional success message

    except Exception as e:
        print("# Error during copy operation: {}".format(e))
        # Provide more context if a known error occurs
        if "Cannot paste view-specific elements from different views" in str(e):
             print("# Detail: This often happens with view-specific elements like dimensions, tags, or annotations if not handled correctly by the API or options.")
        copied_elements_count = -1 # Indicate error state

# Final status reporting (optional, can be commented out)
# if copied_elements_count > 0:
#    print("# Copy complete: {} elements copied to '{}'.".format(copied_elements_count, target_view_name))
# elif copied_elements_count == 0 and source_view and target_view and elements_to_copy_count > 0:
#    print("# Copy operation resulted in 0 elements copied, though {} were selected.".format(elements_to_copy_count))
# elif copied_elements_count < 0:
#    print("# Copy operation failed.")
# elif source_view and target_view and elements_to_copy_count == 0:
    # Handled earlier when checking for elements
#    pass
# else:
    # Handled earlier when checking views
#    print("# Copy operation did not proceed due to view validation errors.")
#    pass