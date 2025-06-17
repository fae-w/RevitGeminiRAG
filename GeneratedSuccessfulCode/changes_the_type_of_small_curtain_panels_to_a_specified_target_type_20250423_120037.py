# Purpose: This script changes the type of small curtain panels to a specified target type.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ElementId,
    ElementType,
    Element,
    Panel,
    Wall,
    CurtainGrid,
    HostObject,
    PanelType,
    WallType,
    BuiltInCategory,
    BuiltInParameter,
    UnitUtils,
    UnitTypeId # For unit conversion
)
import System # For exception handling, Environment

# --- Configuration ---
target_panel_type_name = "Spandrel Panel - Dark"
area_threshold_sqm = 0.5
found_target_type = None
target_type_id = ElementId.InvalidElementId

# --- Helper to find ElementType (PanelType or WallType) ---
def find_panel_or_wall_type_by_name(doc, type_name):
    """Finds a PanelType or WallType by name (case-insensitive). Returns the ElementType object."""
    # Try PanelType first
    collector_panel = FilteredElementCollector(doc).OfClass(PanelType)
    for pt in collector_panel:
        if pt.Name.lower() == type_name.lower():
            return pt # Return the PanelType object

    # Try WallType if not found as PanelType (some curtain panels can be walls)
    collector_wall = FilteredElementCollector(doc).OfClass(WallType)
    for wt in collector_wall:
        # Assumption: A WallType with the same name might be used as a panel.
        if wt.Name.lower() == type_name.lower():
            return wt # Return the WallType object
    return None # Not found

# --- Find the target type ---
try:
    found_target_type = find_panel_or_wall_type_by_name(doc, target_panel_type_name)

    if found_target_type:
        target_type_id = found_target_type.Id
        print("# Found target type '{{}}' with ID: {{}}".format(target_panel_type_name, target_type_id))
    else:
        print("# Error: Target panel type '{{}}' not found in the project. Cannot proceed.".format(target_panel_type_name))
        # Script will continue but skip changes if target type is missing

except System.Exception as e:
     print("# Error finding target panel type: {{}}".format(e))
     found_target_type = None # Ensure it's None on error

# --- Convert Area Threshold to Internal Units (Square Feet) ---
area_threshold_sqft = -1.0 # Initialize with invalid value
try:
    area_threshold_sqft = UnitUtils.ConvertToInternalUnits(area_threshold_sqm, UnitTypeId.SquareMeters)
    print("# Area threshold: {{}} sqm = {{:.4f}} sqft (internal)".format(area_threshold_sqm, area_threshold_sqft))
except System.Exception as e:
    print("# Error converting area threshold units: {{}}. Cannot proceed with area check.".format(e))
    found_target_type = None # Prevent processing if conversion fails

# --- Counters ---
processed_panel_count = 0
changed_count = 0
skipped_target_type_missing = 0
skipped_area_too_large = 0
skipped_already_target_type = 0
skipped_no_host_grid = 0
skipped_no_area_param = 0
skipped_area_conversion_failed = 0
error_count = 0

# --- Process Panels ---
if found_target_type and area_threshold_sqft >= 0:
    try:
        # Collect Panel elements (these are typically what fill Curtain Grids)
        panel_collector = FilteredElementCollector(doc).OfClass(Panel).WhereElementIsNotElementType()

        for panel_element in panel_collector:
            processed_panel_count += 1
            host_element = None
            curtain_grid = None
            panel_area_sqft = -1.0

            try:
                # Get the host (Wall or CurtainSystem)
                host_element = panel_element.Host
                if host_element and hasattr(host_element, 'CurtainGrid'):
                    curtain_grid = host_element.CurtainGrid
                else:
                     # Host might not have a grid (e.g., panel hosted in something else?)
                     skipped_no_host_grid += 1
                     continue # Skip this panel

                # Get the panel's area
                # Try BuiltInParameter.HOST_AREA_COMPUTED first
                area_param = panel_element.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                if area_param and area_param.HasValue and area_param.StorageType == Autodesk.Revit.DB.StorageType.Double:
                    panel_area_sqft = area_param.AsDouble()
                else:
                    # Fallback: try calculating from Width and Height if HOST_AREA_COMPUTED fails
                    width_param = panel_element.get_Parameter(BuiltInParameter.CURTAIN_WALL_PANELS_WIDTH) # Or PANEL_WIDTH? Check common parameters
                    height_param = panel_element.get_Parameter(BuiltInParameter.CURTAIN_WALL_PANELS_HEIGHT) # Or PANEL_HEIGHT? Check common parameters
                    if width_param and height_param and width_param.HasValue and height_param.HasValue:
                         w = width_param.AsDouble()
                         h = height_param.AsDouble()
                         if w > 0 and h > 0:
                             panel_area_sqft = w * h
                         else:
                              skipped_no_area_param += 1
                              #print("# Skipping Panel ID {{}} - Could not calculate area from Width/Height (<=0).".format(panel_element.Id)) # Debug
                              continue # Skip if calculation is invalid
                    else:
                        skipped_no_area_param += 1
                        #print("# Skipping Panel ID {{}} - Area parameter not found or invalid.".format(panel_element.Id)) # Debug
                        continue # Skip this panel if area cannot be determined

                # Now we have a panel_element, its curtain_grid, and its panel_area_sqft
                if curtain_grid and panel_area_sqft >= 0:
                     # Check if the panel area is below the threshold
                    if panel_area_sqft < area_threshold_sqft:
                        # Check if the panel is already the target type
                        current_type_id = panel_element.GetTypeId()
                        if current_type_id == target_type_id:
                            skipped_already_target_type +=1
                            continue # Already the correct type

                        # Perform the type change
                        try:
                            # API requires ElementType (PanelType or WallType)
                            modified_panel = curtain_grid.ChangePanelType(panel_element, found_target_type)
                            # Check if modification was successful (method returns the modified element)
                            if modified_panel and modified_panel.Id == panel_element.Id:
                                 # Check if type actually changed (optional, assumes API call worked if no exception)
                                 if doc.GetElement(modified_panel.Id).GetTypeId() == target_type_id:
                                     changed_count += 1
                                 else:
                                     error_count += 1
                                     print("# Warning: ChangePanelType executed for Panel ID {{}} but type did not update.".format(panel_element.Id))
                            else:
                                 error_count += 1
                                 print("# Warning: ChangePanelType did not return the expected modified panel for ID {{}}.".format(panel_element.Id))

                        except System.ArgumentException as arg_ex:
                             error_count += 1
                             print("# Error changing Panel ID {{}}: {{}}. Target type '{{}}' might be incompatible.".format(panel_element.Id, arg_ex.Message, target_panel_type_name))
                        except System.InvalidOperationException as op_ex:
                             error_count += 1
                             print("# Error changing Panel ID {{}}: {{}}.".format(panel_element.Id, op_ex.Message))
                             # Check for specific known issues like old curtain walls
                             if "Cannot change the type of curtain panels in walls created with early versions" in op_ex.Message:
                                 print("#   Note: This panel might be in an older format curtain wall.")
                        except System.Exception as change_ex:
                            error_count += 1
                            print("# Error changing type for Panel ID {{}}: {{}}".format(panel_element.Id, change_ex.Message))

                    else:
                        # Area is not below the threshold
                        skipped_area_too_large += 1

            except System.Exception as proc_ex:
                error_count += 1
                print("# Error processing Panel ID {{}}: {{}}".format(panel_element.Id, proc_ex.Message))

    except System.Exception as col_ex:
        print("# Error collecting Panel elements: {{}}".format(col_ex.Message))
        error_count += 1

elif not found_target_type:
    # Count potential panels that would have been processed
    try:
         panel_collector = FilteredElementCollector(doc).OfClass(Panel).WhereElementIsNotElementType()
         skipped_target_type_missing = panel_collector.GetElementCount()
         if skipped_target_type_missing > 0:
              print("# Skipping {{}} panels because target type '{{}}' was not found.".format(skipped_target_type_missing, target_panel_type_name))
    except Exception as e:
         print("# Could not count panels to report skipping due to missing target type. Error: {{}}".format(e))

elif area_threshold_sqft < 0:
    # Count potential panels that would have been processed
    try:
         panel_collector = FilteredElementCollector(doc).OfClass(Panel).WhereElementIsNotElementType()
         skipped_area_conversion_failed = panel_collector.GetElementCount()
         if skipped_area_conversion_failed > 0:
              print("# Skipping {{}} panels because area threshold conversion failed.".format(skipped_area_conversion_failed))
    except Exception as e:
        print("# Could not count panels to report skipping due to area conversion failure. Error: {{}}".format(e))


# --- Summary ---
print("--- Change Small Curtain Panels Summary ---")
print("Target Panel Type: '{{}}' ({{}})".format(target_panel_type_name, "Found" if found_target_type else "Not Found"))
print("Area Threshold: < {{}} sqm ({:.4f} sqft)".format(area_threshold_sqm, area_threshold_sqft if area_threshold_sqft >= 0 else -1))
print("Total Panel Elements Analyzed: {{}}".format(processed_panel_count))
print("Panels Changed to Target Type: {{}}".format(changed_count))
if skipped_target_type_missing > 0:
    print("Skipped (Target Type '{{}}' Not Found): {{}}".format(target_panel_type_name, skipped_target_type_missing))
if skipped_area_conversion_failed > 0:
     print("Skipped (Area Threshold Conversion Failed): {{}}".format(skipped_area_conversion_failed))
if skipped_already_target_type > 0:
     print("Skipped (Already Target Type): {{}}".format(skipped_already_target_type))
if skipped_area_too_large > 0:
    print("Skipped (Area >= Threshold): {{}}".format(skipped_area_too_large))
if skipped_no_host_grid > 0:
    print("Skipped (Panel Host/CurtainGrid Not Found): {{}}".format(skipped_no_host_grid))
if skipped_no_area_param > 0:
    print("Skipped (Could Not Determine Area): {{}}".format(skipped_no_area_param))
if error_count > 0:
    print("Errors Encountered: {{}}".format(error_count))
print("--- Script Finished ---")