# Purpose: This script creates and renames a drafting view in Autodesk Revit.

﻿import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewFamilyType,
    ViewFamily,
    ElementId,
    ViewDrafting
)
import System # Required for exception handling

# --- Configuration ---
new_view_name = "Detail - Parking Ramp Transition"

# --- Step 1: Find a suitable ViewFamilyType for Drafting Views ---
drafting_view_family_type_id = ElementId.InvalidElementId
collector = FilteredElementCollector(doc).OfClass(ViewFamilyType)
for vft in collector:
    if vft.ViewFamily == ViewFamily.Drafting:
        drafting_view_family_type_id = vft.Id
        break # Found one, stop searching

# --- Step 2: Create the Drafting View ---
if drafting_view_family_type_id == ElementId.InvalidElementId:
    print("# Error: No ViewFamilyType found for Drafting Views in the document.")
else:
    try:
        # Create the new drafting view using the found ViewFamilyType ID
        new_view = ViewDrafting.Create(doc, drafting_view_family_type_id)

        if new_view is not None:
            original_new_name = new_view.Name # Get the default name assigned by Revit
            try:
                # --- Step 3: Rename the newly created view ---
                new_view.Name = new_view_name
                print("# Successfully created and renamed drafting view to '{{}}' (ID: {{}}, original name: '{{}}').".format(new_view_name, new_view.Id.ToString(), original_new_name)) # Escaped format
            except System.ArgumentException as arg_ex:
                # Handle potential duplicate name error or invalid characters
                print("# Successfully created drafting view (ID: {{}}, original name: '{{}}'), but failed to rename to '{{}}'. Error: {{}}".format(new_view.Id.ToString(), original_new_name, new_view_name, arg_ex.Message)) # Escaped format
            except Exception as rename_ex:
                # Handle other potential renaming errors
                 print("# Successfully created drafting view (ID: {{}}, original name: '{{}}'), but failed to rename to '{{}}'. Unexpected error: {{}}".format(new_view.Id.ToString(), original_new_name, new_view_name, rename_ex)) # Escaped format
        else:
            print("# Error: ViewDrafting.Create returned null, failed to create the view.")

    except System.ArgumentException as arg_ex:
        # This might occur if the viewFamilyTypeId is invalid (though we checked)
        print("# Error creating drafting view: Invalid ViewFamilyType ID used ({}). Details: {}".format(drafting_view_family_type_id.ToString(), arg_ex.Message)) # Escaped format
    except Exception as create_ex:
        # Catch other potential errors during creation
        print("# Error creating drafting view: {}".format(create_ex)) # Escaped format