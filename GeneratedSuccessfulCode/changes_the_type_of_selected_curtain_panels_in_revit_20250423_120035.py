# Purpose: This script changes the type of selected curtain panels in Revit.

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
    HostObject, # Included for completeness, though Panel.Host is primary
    PanelType,
    WallType,
    BuiltInCategory # Useful for collectors, even if not directly used here
)
import System # For exception handling

# --- Configuration ---
target_panel_type_name = "Solid Panel"
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

    # Try WallType if not found as PanelType
    collector_wall = FilteredElementCollector(doc).OfClass(WallType)
    for wt in collector_wall:
        # Assumption: A WallType with the same name might be used as a panel.
        if wt.Name.lower() == type_name.lower():
            # Note: Further checks could verify if wt.Kind allows use as panel, but name match is used here.
            return wt # Return the WallType object
    return None # Not found

# --- Find the target type ---
try:
    found_target_type = find_panel_or_wall_type_by_name(doc, target_panel_type_name)

    if found_target_type:
        target_type_id = found_target_type.Id
        print("# Found target type '{}' with ID: {}".format(target_panel_type_name, target_type_id))
    else:
        print("# Error: Target panel type '{}' not found in the project. Cannot proceed.".format(target_panel_type_name))
        # Script will continue but skip changes if target type is missing

except System.Exception as e:
     print("# Error finding target panel type: {}".format(e))
     found_target_type = None # Ensure it's None on error

# --- Get Selection ---
try:
    selected_ids = uidoc.Selection.GetElementIds()
    if not selected_ids or selected_ids.Count == 0:
         print("# No elements are currently selected.")
         selected_ids = [] # Ensure it's an empty list for logic below
except System.Exception as e:
    print("# Error getting selection: {}".format(e))
    selected_ids = [] # Ensure it's an empty list on error

# --- Counters ---
processed_count = 0
changed_count = 0
skipped_not_panel = 0
skipped_no_host_grid = 0
skipped_already_target_type = 0
skipped_target_type_missing = 0
error_count = 0

# --- Process Selection ---
if found_target_type and selected_ids:
    for elem_id in selected_ids:
        processed_count += 1
        panel_element = None
        host_element = None
        curtain_grid = None

        try:
            element = doc.GetElement(elem_id)
            if not element:
                # This case is unlikely if ID came from selection, but good practice
                skipped_not_panel += 1
                continue

            # We need to operate on Panel elements. Walls selected directly are usually hosts or infill walls.
            # The API `ChangePanelType` requires the *panel* element and the host's grid.
            # `Panel` instances have a `.Host` property making this straightforward.
            # Handling `Wall` instances selected directly (which might be infill panels) is complex
            # as getting the host grid isn't direct. Focus on `Panel` instances.
            if isinstance(element, Panel):
                panel_element = element
                # Get the host (Wall or CurtainSystem)
                host_element = panel_element.Host
                if host_element and hasattr(host_element, 'CurtainGrid'):
                    curtain_grid = host_element.CurtainGrid
                else:
                     # Host might not have a grid (e.g., panel hosted in something else?)
                     skipped_no_host_grid += 1
                     # print("# Skipping Panel ID {} - Host or CurtainGrid not found or invalid.".format(elem_id)) # Debug
                     continue
            else:
                # Skip elements that are not Panel instances
                skipped_not_panel += 1
                # print("# Skipping selected element ID {} - Not a Panel element.".format(elem_id)) # Debug
                continue

            # Now we have a panel_element (Panel type) and its curtain_grid
            if curtain_grid and panel_element:
                 # Check if the panel is already the target type
                current_type_id = panel_element.GetTypeId()
                if current_type_id == target_type_id:
                    skipped_already_target_type +=1
                    continue # Already the correct type

                # Perform the change
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
                              print("# Warning: ChangePanelType executed for Panel ID {} but type did not update.".format(elem_id))
                    else:
                         # This case implies ChangePanelType might have failed silently or returned something unexpected.
                         error_count += 1
                         print("# Warning: ChangePanelType did not return the expected modified panel for ID {}.".format(elem_id))

                except System.ArgumentException as arg_ex:
                     error_count += 1
                     print("# Error changing Panel ID {}: {}. Target type '{}' might be incompatible.".format(elem_id, arg_ex.Message, target_panel_type_name))
                except System.InvalidOperationException as op_ex:
                     error_count += 1
                     print("# Error changing Panel ID {}: {}.".format(elem_id, op_ex.Message))
                     # Check for specific known issues like old curtain walls
                     if "Cannot change the type of curtain panels in walls created with early versions" in op_ex.Message:
                         print("#   Note: This panel might be in an older format curtain wall.")
                except System.Exception as change_ex:
                    error_count += 1
                    print("# Error changing type for Panel ID {}: {}".format(elem_id, change_ex.Message))

            # else case (no curtain_grid) handled by continue statement earlier

        except System.Exception as proc_ex:
            error_count += 1
            print("# Error processing selected element ID {}: {}".format(elem_id, proc_ex.Message))

elif not found_target_type and selected_ids:
    # Target type wasn't found initially, count all selected as skipped for this reason
    skipped_target_type_missing = len(selected_ids)
    processed_count = skipped_target_type_missing # All processed items resulted in this skip reason

# --- Summary ---
print("--- Change Selected Curtain Panels Summary ---")
print("Target Panel Type: '{}' ({})".format(target_panel_type_name, "Found" if found_target_type else "Not Found"))
print("Total Selected Elements Analyzed: {}".format(len(selected_ids) if selected_ids else 0))
print("Panel Elements Processed: {}".format(processed_count - skipped_not_panel))
print("Panels Changed to Target Type: {}".format(changed_count))
if skipped_target_type_missing > 0:
    print("Skipped (Target Type '{}' Not Found): {}".format(target_panel_type_name, skipped_target_type_missing))
if skipped_already_target_type > 0:
     print("Skipped (Already Target Type): {}".format(skipped_already_target_type))
if skipped_not_panel > 0:
    print("Skipped (Selected Element Not a Panel): {}".format(skipped_not_panel))
if skipped_no_host_grid > 0:
    print("Skipped (Panel Host/CurtainGrid Not Found): {}".format(skipped_no_host_grid))
if error_count > 0:
    print("Errors Encountered: {}".format(error_count))
print("--- Script Finished ---")