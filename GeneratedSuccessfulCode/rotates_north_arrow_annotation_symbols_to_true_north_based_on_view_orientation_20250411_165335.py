# Purpose: This script rotates North Arrow annotation symbols to True North based on view orientation.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance, # Changed from AnnotationSymbol
    FamilySymbol, # Changed from AnnotationSymbolType
    ElementId,
    BuiltInParameter,
    Parameter,
    ProjectInfo,
    View # Added for type checking
)
# No specific .NET types needed beyond standard RevitAPI

# --- Constants and Configuration ---
# Assuming North Arrow families have "North Arrow" in their family name (case-insensitive)
NORTH_ARROW_FAMILY_NAME_SUBSTRING = "north arrow"
# Assuming the parameter controlling the rotation *within* the annotation symbol family instance is named "Orientation"
# This might be "Angle", "Rotation", or a custom name depending on the family definition.
# This parameter is assumed to be of type Angle (stores radians).
ORIENTATION_PARAMETER_NAME = "Orientation"

# --- Script Core Logic ---
updated_count = 0
skipped_count = 0
error_count = 0
not_found_count = 0
param_not_found_count = 0
param_read_only_count = 0

# Get Project Information for True North angle
try:
    project_info = doc.ProjectInformation
    if project_info:
        # AngleToTrueNorth property gives the angle in radians from Project North to True North
        angle_to_true_north = project_info.AngleToTrueNorth
    else:
        # Error: Cannot retrieve Project Information
        angle_to_true_north = 0.0 # Default to 0 if not found, though unlikely
        # print("# Warning: Could not retrieve Project Information. Assuming True North angle is 0.") # Debug/Info
        error_count += 1 # Count as error if ProjectInfo isn't available
except Exception as e:
    # Error: Failed to get AngleToTrueNorth from ProjectInfo: {{{{e}}}}
    # print("# Error: Failed to get True North angle: {{}}".format(e)) # Debug/Info
    angle_to_true_north = 0.0 # Default on error
    error_count += 1

# Collect all Family Instances belonging to the Generic Annotations category
# Corrected collector based on the error message
collector = FilteredElementCollector(doc).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType()

# Iterate through collected family instances
for symbol in collector: # Renamed 'element' to 'symbol' for consistency with original logic
    try:
        # Get the family symbol (type)
        symbol_type = doc.GetElement(symbol.GetTypeId())
        if not isinstance(symbol_type, FamilySymbol):
            skipped_count += 1
            continue # Skip if not a valid family symbol type

        # --- Check if it's likely a North Arrow ---
        # Assumption: Check the family name of the symbol's type
        family_name = ""
        if symbol_type.FamilyName:
             family_name = symbol_type.FamilyName.lower() # Case-insensitive comparison

        if NORTH_ARROW_FAMILY_NAME_SUBSTRING not in family_name:
            # This annotation symbol doesn't seem to be a North Arrow based on family name
            not_found_count += 1
            continue

        # --- Get the Owner View ---
        owner_view = None
        if symbol.OwnerViewId != ElementId.InvalidElementId:
            view_element = doc.GetElement(symbol.OwnerViewId)
            # Ensure the owner is actually a View element
            if isinstance(view_element, View):
                owner_view = view_element

        if not owner_view:
            # Annotation might be in a legend or schedule (which might not have orientation), or view deleted? Skip.
            skipped_count += 1
            continue

        # --- Get View Orientation ---
        view_orientation_param = owner_view.get_Parameter(BuiltInParameter.VIEW_ORIENTATION)
        is_true_north_oriented = False
        if view_orientation_param and view_orientation_param.HasValue:
            # VIEW_ORIENTATION values (undocumented, common understanding):
            # 0 = Project North
            # 1 = True North
            try:
                 is_true_north_oriented = (view_orientation_param.AsInteger() == 1)
            except: # Handle cases where AsInteger might fail (e.g., parameter type mismatch, though unlikely for BuiltIn)
                 # print("# Warning: Could not read VIEW_ORIENTATION for view ID {{}}".format(owner_view.Id)) # Debug/Info
                 skipped_count += 1
                 continue # Skip if orientation cannot be determined

        # --- Get the Instance Parameter "Orientation" ---
        orientation_param = symbol.LookupParameter(ORIENTATION_PARAMETER_NAME)

        if orientation_param is None:
            # Parameter not found on this instance
            # print("# Debug: Parameter '{{}}' not found on symbol ID {{}}".format(ORIENTATION_PARAMETER_NAME, symbol.Id)) # Debug/Info
            param_not_found_count += 1
            continue

        if orientation_param.IsReadOnly:
            # Parameter is read-only
            # print("# Debug: Parameter '{{}}' is read-only on symbol ID {{}}".format(ORIENTATION_PARAMETER_NAME, symbol.Id)) # Debug/Info
            param_read_only_count += 1
            continue

        # --- Calculate the Target Angle ---
        target_angle_radians = 0.0 # Default angle (when view is already True North)

        # If the view is oriented to Project North, rotate the symbol by AngleToTrueNorth
        # If the view is already oriented to True North, the symbol should have 0 rotation relative to the view
        if not is_true_north_oriented:
            target_angle_radians = angle_to_true_north
        # else: target_angle_radians remains 0.0

        # --- Set the Parameter Value ---
        try:
            # Check current value to avoid unnecessary changes? Optional but good practice.
            current_value = orientation_param.AsDouble()
            # Use a tolerance for floating-point comparison
            tolerance = 0.0001
            if abs(current_value - target_angle_radians) > tolerance:
                set_result = orientation_param.Set(target_angle_radians)
                if set_result:
                    updated_count += 1
                else:
                    # Failed to set parameter for unknown reason
                    # print("# Warning: Failed to set parameter '{{}}' for symbol ID {{}} (Set returned False)".format(ORIENTATION_PARAMETER_NAME, symbol.Id)) # Debug/Info
                    error_count += 1
            # else: # Already correct - No action needed, don't count as skipped or updated

        except Exception as e_set:
            # print("# Error setting parameter '{{}}' for symbol ID {{}}: {{}}".format(ORIENTATION_PARAMETER_NAME, symbol.Id, e_set)) # Debug/Info
            error_count += 1

    except Exception as e_main:
        # Catch any other errors during processing of a symbol
        # print("# Error processing symbol ID {{}}: {{}}".format(symbol.Id, e_main)) # Debug/Info
        error_count += 1

# Summary printing is removed as per user request.