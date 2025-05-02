# Purpose: This script creates and renames a default 3D orthographic view in Autodesk Revit.

﻿# Mandatory Imports
import clr
clr.AddReference('System') # For exception handling
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewFamilyType,
    ViewFamily,
    View3D,
    ElementId,
    Element
)
import System # For Exception handling

# --- Configuration ---
new_view_name = "Overall Model 3D View"

# --- Step 1: Find the default 3D ViewFamilyType ---
view_family_type_id = ElementId.InvalidElementId
collector = FilteredElementCollector(doc).OfClass(ViewFamilyType)
for vft in collector:
    # Ensure it's a valid ViewFamilyType before checking ViewFamily
    if isinstance(vft, ViewFamilyType):
        # Check if it's the type for 3D views
        if vft.ViewFamily == ViewFamily.ThreeDimensional:
            view_family_type_id = vft.Id
            break # Found the first suitable type

# --- Step 2: Create the 3D Orthographic View ---
created_view = None
if view_family_type_id != ElementId.InvalidElementId:
    try:
        # Create the default orthographic 3D view
        created_view = View3D.CreateOrthographic(doc, view_family_type_id)
        # print("# Successfully created 3D view with ID: {}".format(created_view.Id)) # Debug
    except Exception as create_ex:
        print("# Error creating 3D view: {}".format(create_ex))
else:
    print("# Error: Could not find a 3D ViewFamilyType in the document.")

# --- Step 3: Rename the newly created view ---
if created_view is not None:
    try:
        # Set the name of the newly created view
        created_view.Name = new_view_name
        # print("# Successfully renamed view to: {}".format(new_view_name)) # Debug
    except System.ArgumentException as arg_ex:
        # Handle cases where the name might already exist or is invalid
        print("# Error renaming view (ID: {}): {}. Name '{}' might already exist.".format(created_view.Id, arg_ex.Message, new_view_name))
    except Exception as rename_ex:
        print("# Error renaming view (ID: {}): {}".format(created_view.Id, rename_ex))
# else: # Optional: If creation failed, this step is skipped anyway
    # print("# View creation failed, skipping rename.") # Debug