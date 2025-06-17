# Purpose: This script hides dimensions smaller than a specified threshold in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Needed for potential uidoc usage if required later, good practice
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Dimension,
    AngularDimension, # To skip angular dimensions
    ElementId,
    UnitUtils,
    View,
    # Need to handle potential import errors for different API versions
)

# Attempt to import unit types - handle potential errors gracefully
try:
    # Revit 2021+ preferred method
    from Autodesk.Revit.DB import ForgeTypeId
except ImportError:
    ForgeTypeId = None # Flag that it's not available

try:
    # Revit 2021+ alternative/common method
    from Autodesk.Revit.DB import UnitTypeId
except ImportError:
    UnitTypeId = None # Flag that it's not available

try:
    # Pre-Revit 2021 method
    from Autodesk.Revit.DB import DisplayUnitType
except ImportError:
    DisplayUnitType = None # Flag that it's not available

# --- Configuration ---
# Threshold value in millimeters
threshold_mm = 100.0

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined and available
try:
    active_view = doc.ActiveView
except Exception as e:
    print("# Error getting active view: {}".format(e))
    active_view = None

if not active_view or not isinstance(active_view, View):
    print("# Error: No active valid view found or accessible.")
else:
    # --- Convert Threshold to Internal Units (Feet) ---
    threshold_internal = None # Initialize
    conversion_success = False

    # Try Revit 2021+ ForgeTypeId method first
    if ForgeTypeId and not conversion_success:
        try:
            # Common ForgeTypeId for Millimeters (adjust if necessary for specific Revit version)
            # Using the spec identifier might be more robust than the unit identifier
            # mm_spec_id = ForgeTypeId("autodesk.spec.aec:length-2.0.0")
            # millimeters_type_id = UnitTypeId.Millimeters # Direct property often works
            millimeters_type_id = ForgeTypeId("autodesk.unit.unit:millimeters-1.0.1")
            if UnitUtils.IsValidUnit(millimeters_type_id): # Check if the ForgeTypeId is valid for conversion
                 threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, millimeters_type_id)
                 conversion_success = True
                 # print("# Info: Used ForgeTypeId for unit conversion.") # Optional Debug
            else:
                 # Try the direct UnitTypeId property if ForgeTypeId lookup failed or wasn't valid
                 if UnitTypeId and UnitTypeId.Millimeters:
                     try:
                         threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
                         conversion_success = True
                         # print("# Info: Used UnitTypeId.Millimeters for unit conversion.") # Optional Debug
                     except Exception as ut_e:
                         # print("# Info: Failed to use UnitTypeId.Millimeters: {}".format(ut_e)) # Optional Debug
                         pass # Continue to next fallback
        except Exception as ft_e:
             # print("# Info: Failed to use ForgeTypeId method: {}".format(ft_e)) # Optional Debug
             pass # Continue to next fallback

    # Fallback to UnitTypeId if ForgeTypeId failed or wasn't available
    if UnitTypeId and not conversion_success:
        try:
            threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, UnitTypeId.Millimeters)
            conversion_success = True
            # print("# Info: Used UnitTypeId.Millimeters (fallback) for unit conversion.") # Optional Debug
        except Exception as ut_e:
            # print("# Info: Failed using UnitTypeId.Millimeters (fallback): {}".format(ut_e)) # Optional Debug
            pass # Continue to next fallback

    # Fallback for older API versions (pre-2021) using DisplayUnitType
    if DisplayUnitType and not conversion_success:
        try:
            threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
            conversion_success = True
            # print("# Info: Used DisplayUnitType (legacy) for unit conversion.") # Optional Debug
        except Exception as dut_e:
            print("# Error: Failed converting threshold units using DisplayUnitType: {}".format(dut_e))
            # Keep conversion_success as False

    if not conversion_success or threshold_internal is None:
        print("# Error: Could not determine internal units for threshold. Cannot proceed.")
    else:
        # --- Collect Dimensions in Active View ---
        collector = FilteredElementCollector(doc, active_view.Id).OfClass(Dimension)
        dimensions_to_hide = List[ElementId]()
        processed_count = 0
        hidden_count = 0

        for dim in collector:
            # Ensure it's a Dimension element (redundant with OfClass but safe)
            if isinstance(dim, Dimension):
                processed_count += 1
                try:
                    # AngularDimension Value is in radians, so '< 100mm' doesn't apply directly.
                    # Skip AngularDimensions based on the unit assumption.
                    if isinstance(dim, AngularDimension):
                        continue # Skip angular dimensions

                    # Dimension.Value returns a nullable double? representing the dimension's value
                    # in internal units (feet). This works for Linear, Radial, Diameter, Arc Length dimensions.
                    dim_value_nullable = dim.Value # This is nullable double? in C#, potentially None or a value in IronPython

                    # Check if value exists (is not None) and is less than the threshold
                    # Need to handle the nullable return carefully. In IronPython, testing it directly might work.
                    if dim_value_nullable is not None and dim_value_nullable < threshold_internal:
                        # Check if the specific dimension is already hidden (optional, but good practice)
                        # IsHidden needs the view context.
                        try:
                            if not dim.IsHidden(active_view):
                                dimensions_to_hide.Add(dim.Id)
                                hidden_count += 1
                        except Exception as is_hidden_e:
                             # If checking IsHidden fails for some reason, maybe still try to hide? Or log it.
                             # print("# Warning: Could not check if dimension ID {} is hidden: {}. Adding to hide list anyway.".format(dim.Id, is_hidden_e))
                             dimensions_to_hide.Add(dim.Id) # Add anyway if check fails
                             hidden_count += 1 # Assume it wasn't hidden for counting purposes

                except AttributeError:
                    # Some dimension types might not have a 'Value' property accessible this way.
                    # print("# Skipping dimension ID {} - could not get Value".format(dim.Id)) # Optional Debug
                    pass
                except Exception as e:
                    print("# Error processing dimension ID {}: {}".format(dim.Id, e))


        # --- Hide Collected Dimensions ---
        if dimensions_to_hide.Count > 0:
            try:
                # Hide the elements (Transaction managed externally by the caller)
                active_view.HideElements(dimensions_to_hide)
                print("# Attempted to hide {} dimensions smaller than {}mm in view '{}' (out of {} processed dimensions).".format(hidden_count, threshold_mm, active_view.Name, processed_count))
            except Exception as hide_e:
                # Check if the exception indicates elements cannot be hidden
                # Error messages might vary slightly between Revit versions
                if "One or more of the elements cannot be hidden in the view" in str(hide_e) or \
                   "Element cannot be hidden" in str(hide_e):
                     print("# Warning: Some elements could not be hidden (perhaps already hidden, pinned, part of a group that prevents hiding, or view limitations).")
                     # Optionally, try hiding one by one or filter the list further if needed
                else:
                    print("# Error occurred while hiding elements: {}".format(hide_e))
        else:
            print("# No dimensions found smaller than {}mm to hide in view '{}' ({} dimensions processed).".format(threshold_mm, active_view.Name, processed_count))