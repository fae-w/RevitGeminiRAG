# Purpose: This script updates Revit window instance parameters (Sill Height, Head Height, Comments) based on input data.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    ElementId,
    FamilyInstance,
    BuiltInCategory,
    BuiltInParameter,
    Parameter,
    StorageType,
    UnitTypeId
)
import System # For Decimal conversion if needed, though double is more common

# --- Input Data ---
# Data format: ID,SillHeight(mm),HeadHeight(mm),Comments
input_data = """ID,SillHeight,HeadHeight,Comments
90011,900,2400,Standard
90022,850,2400,Accessible WC
90033,900,2100,Standard"""

# --- Configuration ---
# Assume input dimensions are in millimeters
mm_to_feet = 1.0 / 304.8

# --- Processing ---
lines = input_data.strip().split('\n')
header = lines[0]
data_lines = lines[1:]

print("# Starting window parameter update...")

for line in data_lines:
    try:
        parts = line.strip().split(',')
        if len(parts) != 4:
            print("# Warning: Skipping invalid line format: {}".format(line))
            continue

        element_id_int = int(parts[0])
        sill_height_mm = float(parts[1])
        head_height_mm = float(parts[2])
        comments_str = parts[3]

        # Convert values to Revit internal units (feet)
        target_sill_height_feet = sill_height_mm * mm_to_feet
        target_head_height_feet = head_height_mm * mm_to_feet
        target_comments = comments_str

        target_element_id = ElementId(element_id_int)
        element = doc.GetElement(target_element_id)

        # --- Validate Element ---
        if element is None:
            print("# Error: Element ID {} not found.".format(element_id_int))
            continue

        # Check if it's a FamilyInstance and specifically a Window
        if not isinstance(element, FamilyInstance):
            print("# Error: Element ID {} is not a FamilyInstance (Type: {}). Skipping.".format(element_id_int, element.GetType().Name))
            continue

        # Get the category, handle potential null symbol/family/category
        category = None
        try:
            if element.Symbol and element.Symbol.Family:
                 category = element.Symbol.Family.FamilyCategory
        except Exception:
             pass # Ignore errors getting category info

        if category is None or category.Id.IntegerValue != int(BuiltInCategory.OST_Windows):
            category_name = category.Name if category else "Unknown"
            print("# Error: Element ID {} is not a Window (Category: {}). Skipping.".format(element_id_int, category_name))
            continue

        print("# Processing Window ID: {}".format(element_id_int))
        success_messages = []
        error_messages = []

        # --- 1. Update Sill Height ---
        try:
            sill_param = element.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)
            if sill_param and not sill_param.IsReadOnly:
                if sill_param.StorageType == StorageType.Double:
                    current_value = sill_param.AsDouble()
                    # Use a small tolerance for floating point comparison
                    if abs(current_value - target_sill_height_feet) > 0.0001:
                        # --- Modification Start (Requires Transaction - handled externally) ---
                        set_success = sill_param.Set(target_sill_height_feet)
                        # --- Modification End ---
                        if set_success:
                            success_messages.append("Sill Height: Set to {:.2f} mm ({:.4f} ft).".format(sill_height_mm, target_sill_height_feet))
                        else:
                            error_messages.append("Sill Height: Failed to set value using Set().")
                    else:
                         success_messages.append("Sill Height: Already set correctly.")
                else:
                    error_messages.append("Sill Height: Parameter is not a Double type (found {}).".format(sill_param.StorageType.ToString()))
            elif sill_param is None:
                error_messages.append("Sill Height: Parameter (INSTANCE_SILL_HEIGHT_PARAM) not found.")
            else: # Parameter exists but is read-only
                error_messages.append("Sill Height: Parameter is read-only.")
        except Exception as sh_ex:
            error_messages.append("Sill Height: Error setting parameter: {}".format(sh_ex))

        # --- 2. Update Head Height ---
        try:
            # Head height might be directly set or calculated. INSTANCE_HEAD_HEIGHT_PARAM is common.
            head_param = element.get_Parameter(BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM)
            if head_param and not head_param.IsReadOnly:
                if head_param.StorageType == StorageType.Double:
                     current_value = head_param.AsDouble()
                     # Use a small tolerance for floating point comparison
                     if abs(current_value - target_head_height_feet) > 0.0001:
                        # --- Modification Start (Requires Transaction - handled externally) ---
                        set_success = head_param.Set(target_head_height_feet)
                        # --- Modification End ---
                        if set_success:
                            success_messages.append("Head Height: Set to {:.2f} mm ({:.4f} ft).".format(head_height_mm, target_head_height_feet))
                        else:
                            error_messages.append("Head Height: Failed to set value using Set().")
                     else:
                        success_messages.append("Head Height: Already set correctly.")
                else:
                    error_messages.append("Head Height: Parameter is not a Double type (found {}).".format(head_param.StorageType.ToString()))
            elif head_param is None:
                 # Head height might be controlled by Sill Height + Type Height Parameter (WINDOW_HEIGHT)
                 # This script only attempts to set the direct instance parameter if available.
                error_messages.append("Head Height: Parameter (INSTANCE_HEAD_HEIGHT_PARAM) not found. It might be calculated.")
            else: # Parameter exists but is read-only
                error_messages.append("Head Height: Parameter is read-only. It might be calculated.")
        except Exception as hh_ex:
            error_messages.append("Head Height: Error setting parameter: {}".format(hh_ex))

        # --- 3. Update Comments ---
        try:
            comments_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
            if comments_param and not comments_param.IsReadOnly:
                if comments_param.StorageType == StorageType.String:
                    current_value = comments_param.AsString()
                    if current_value != target_comments:
                        # --- Modification Start (Requires Transaction - handled externally) ---
                        set_success = comments_param.Set(target_comments)
                        # --- Modification End ---
                        if set_success:
                            success_messages.append("Comments: Set to '{}'.".format(target_comments))
                        else:
                            error_messages.append("Comments: Failed to set value using Set().")
                    else:
                         success_messages.append("Comments: Already set correctly.")
                else:
                    error_messages.append("Comments: Parameter is not a String type (found {}).".format(comments_param.StorageType.ToString()))
            elif comments_param is None:
                error_messages.append("Comments: Parameter (ALL_MODEL_INSTANCE_COMMENTS) not found.")
            else: # Parameter exists but is read-only
                error_messages.append("Comments: Parameter is read-only.")
        except Exception as cm_ex:
            error_messages.append("Comments: Error setting parameter: {}".format(cm_ex))

        # --- Report for the element ---
        if success_messages:
            print("  Successful Updates/Checks:")
            for msg in success_messages:
                print("    + {}".format(msg))
        if error_messages:
            print("  Errors/Warnings:")
            for msg in error_messages:
                print("    - {}".format(msg))
        if not success_messages and not error_messages:
            print("  No changes were attempted or needed based on checks.")

    except ValueError as ve:
        print("# Error: Could not parse data in line: '{}'. Error: {}".format(line, ve))
    except Exception as e:
        print("# Error: Unexpected error processing line '{}': {}".format(line, e))

print("# Window parameter update finished.")