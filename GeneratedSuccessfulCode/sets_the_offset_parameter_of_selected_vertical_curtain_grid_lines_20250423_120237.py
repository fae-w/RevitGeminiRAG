# Purpose: This script sets the offset parameter of selected vertical curtain grid lines.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from System import Exception
from Autodesk.Revit.DB import (
    ElementId,
    CurtainGridLine,
    Parameter,
    # BuiltInParameter is removed as CURTAIN_GRID_LINE_OFFSET is not a valid member
    UnitUtils,
    Transaction # Required for modifying elements - Although handled by wrapper, keep import for context if needed elsewhere
)
# Attempt to import newer unit types, fallback if necessary
try:
    from Autodesk.Revit.DB import ForgeTypeId, UnitTypeId, DisplayUnitType
    use_forge_type_id = True
    use_display_unit_type = True
except ImportError:
    try:
        from Autodesk.Revit.DB import DisplayUnitType
        use_forge_type_id = False
        use_display_unit_type = True
    except ImportError:
        use_forge_type_id = False
        use_display_unit_type = False
        print("# Warning: Could not import ForgeTypeId or DisplayUnitType. Unit conversion might fail.")

from System.Collections.Generic import List

# --- Constants ---
target_offset_mm = 100.0
offset_value_feet = None # Initialize to None
parameter_name = "Offset" # Target parameter name

# --- Unit Conversion ---
# Try converting using available methods, prioritizing DisplayUnitType for broader compatibility
conversion_success = False
if use_display_unit_type:
    try:
        # Attempt conversion using DisplayUnitType enum value first
        offset_value_feet = UnitUtils.ConvertToInternalUnits(target_offset_mm, DisplayUnitType.DUT_MILLIMETERS)
        conversion_success = True
    except Exception as e_dut:
        print("# Info: Unit conversion using DisplayUnitType failed: {}. Trying ForgeTypeId if available.".format(e_dut))

if not conversion_success and use_forge_type_id:
    try:
        # Fallback to ForgeTypeId for newer APIs if DisplayUnitType failed or wasn't available
        mm_unit_id = ForgeTypeId(UnitTypeId.Millimeters)
        offset_value_feet = UnitUtils.ConvertToInternalUnits(target_offset_mm, mm_unit_id)
        conversion_success = True
    except Exception as e_forge:
         print("# Error: Unit conversion using ForgeTypeId also failed: {}".format(e_forge))

if not conversion_success:
     print("# Error: Could not perform unit conversion. Halting script.")
     # Set offset_value_feet to a state that prevents execution (e.g., None)
     offset_value_feet = None

# --- Script Core Logic ---
if offset_value_feet is not None: # Proceed only if unit conversion was successful
    selected_ids = uidoc.Selection.GetElementIds()
    modified_count = 0
    skipped_locked_readonly = 0
    skipped_no_param = 0
    skipped_not_v_gridline = 0
    skipped_not_gridline = 0
    error_count = 0

    if not selected_ids or selected_ids.Count == 0:
        print("# Please select one or more Curtain Grid Lines.")
    else:
        # No transaction management needed here - handled by C# wrapper

        for element_id in selected_ids:
            try:
                element = doc.GetElement(element_id)

                # Check if it is a CurtainGridLine
                if isinstance(element, CurtainGridLine):
                    grid_line = element

                    # Check if it is a Vertical grid line
                    is_vertical = False
                    try:
                         # Use property (common in newer APIs)
                         is_vertical = grid_line.IsVertical
                    except AttributeError:
                         # Fallback to method (common in older APIs)
                         try:
                             is_vertical = grid_line.IsVGridLine()
                         except AttributeError:
                             print("# Warning: Could not determine orientation for Grid Line ID {}. Skipping.".format(grid_line.Id))
                             error_count += 1
                             continue # Skip this element

                    if is_vertical:
                        # Attempt to get the specific offset parameter by name
                        param = grid_line.LookupParameter(parameter_name)

                        if param and param.Definition is not None: # Check if parameter exists
                            # Check if the parameter can be changed
                            if not param.IsReadOnly:
                                try:
                                    param.Set(offset_value_feet)
                                    modified_count += 1
                                except Exception as set_ex:
                                    print("# Error setting offset for Vertical Grid Line ID {}: {}".format(grid_line.Id, set_ex))
                                    # Count as error, potentially due to constraints not caught by IsReadOnly
                                    error_count += 1
                                    skipped_locked_readonly += 1 # Assume it's a lock/constraint issue
                            else:
                                # Parameter is read-only (likely locked or driven by pattern)
                                skipped_locked_readonly += 1
                        else:
                            # The specific Offset parameter does not exist on this grid line
                            skipped_no_param += 1
                    else:
                        # Element is a CurtainGridLine but not vertical
                        skipped_not_v_gridline += 1
                else:
                    # Element in selection was not a CurtainGridLine
                    skipped_not_gridline += 1

            except Exception as e:
                print("# Error processing element ID {}: {}".format(element_id, e))
                error_count += 1

        # --- Summary ---
        print("# --- Script Summary ---")
        print("# Selected elements processed: {}".format(selected_ids.Count))
        print("# Vertical Curtain Grid Lines Offset Set: {}".format(modified_count))
        if skipped_locked_readonly > 0:
            print("# Skipped Vertical Lines (Locked/Read-Only/Pattern Driven): {}".format(skipped_locked_readonly))
        if skipped_no_param > 0:
             print("# Skipped Vertical Lines ('{}' parameter not found): {}".format(parameter_name, skipped_no_param))
        if skipped_not_v_gridline > 0:
            print("# Skipped (Horizontal Curtain Grid Line): {}".format(skipped_not_v_gridline))
        if skipped_not_gridline > 0:
            print("# Skipped (Not a Curtain Grid Line): {}".format(skipped_not_gridline))
        if error_count > 0:
            print("# Errors encountered during processing: {}".format(error_count))

        total_processed_v_gridlines = modified_count + skipped_locked_readonly + skipped_no_param
        if total_processed_v_gridlines == 0 and skipped_not_v_gridline == 0 and skipped_not_gridline == 0 and selected_ids.Count > 0:
             print("# No applicable vertical curtain grid lines found or processed in selection.")
        elif modified_count == 0 and total_processed_v_gridlines > 0:
            print("# No changes were made to vertical grid lines. Check if lines are locked or if the correct lines were selected.")
# else: # Handles the case where offset_value_feet is None from the start
#    print("# Script halted due to initial unit conversion failure.")