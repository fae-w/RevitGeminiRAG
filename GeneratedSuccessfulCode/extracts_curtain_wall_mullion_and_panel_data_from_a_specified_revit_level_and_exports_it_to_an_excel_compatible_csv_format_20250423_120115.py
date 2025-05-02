# Purpose: This script extracts curtain wall, mullion, and panel data from a specified Revit level and exports it to an Excel-compatible CSV format.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
clr.AddReference('System.Collections') # Required for List
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, Level, Wall, CurtainGrid,
    Mullion, Panel, Element, ElementId, BuiltInParameter, ElementType, WallType,
    MullionType, Parameter, HostObject, Curve, LocationCurve # Added Curve, LocationCurve
)
from System.Collections.Generic import List, ICollection # Explicitly import ICollection
import System # For Math.Round

# --- Configuration ---
target_level_name = "L1 - Block 35"
output_filename = "curtain_elements_report.xlsx" # Default filename

# --- Helper Functions ---

def get_parameter_value_double(element, built_in_param):
    """Safely get parameter value as double, returning 0.0 if not found/no value."""
    if not element: return 0.0
    param = element.get_Parameter(built_in_param)
    if param and param.HasValue:
        try:
            # Revit internal units are usually feet or feet^2
            return param.AsDouble()
        except Exception:
            return 0.0 # Handle cases where value exists but isn't double
    return 0.0

def get_element_type(element):
    """Safely get the ElementType of an element."""
    if not element: return None
    type_id = element.GetTypeId()
    if type_id and type_id != ElementId.InvalidElementId:
        try:
            return doc.GetElement(type_id)
        except Exception:
            return None
    return None

def safe_get_name(element_or_type):
    """Safely get the name of an element or its type."""
    if not element_or_type: return "N/A"
    name = "N/A"
    try:
        # Try direct Name property first (common for types)
        if hasattr(element_or_type, 'Name'):
            name_prop = element_or_type.Name
            if name_prop:
                return name_prop

        # Fallback to standard Type Name parameter if it's an instance element
        if isinstance(element_or_type, Element) and not isinstance(element_or_type, ElementType):
             type_elem = get_element_type(element_or_type)
             if type_elem and hasattr(type_elem, 'Name') and type_elem.Name:
                 return type_elem.Name # Get name from its type

        # Fallback to parameter access
        type_name_params = [
            BuiltInParameter.ELEM_TYPE_PARAM,
            BuiltInParameter.ALL_MODEL_TYPE_NAME
        ]
        for bip in type_name_params:
            param = element_or_type.get_Parameter(bip)
            if param and param.HasValue:
                name_val = param.AsValueString()
                if name_val:
                    return name_val

        # Final check if it's an ElementType itself
        if isinstance(element_or_type, ElementType) and hasattr(element_or_type, 'Name') and element_or_type.Name:
           return element_or_type.Name

    except Exception:
        name = "Error Getting Name"
    return name if name else "N/A"

def safe_get_family_name(element_or_type):
    """Safely get the family name from an Element or its ElementType."""
    if not element_or_type: return "N/A"
    element_type = None
    if isinstance(element_or_type, ElementType):
        element_type = element_or_type
    elif isinstance(element_or_type, Element):
        element_type = get_element_type(element_or_type)

    if not element_type: return "N/A"

    family_name = "N/A"
    try:
        # Try direct FamilyName property first
        if hasattr(element_type, 'FamilyName'):
            fam_name_prop = element_type.FamilyName
            if fam_name_prop:
                return fam_name_prop

        # Fallback to parameters on the type
        fam_name_params = [
             BuiltInParameter.ELEM_FAMILY_PARAM,
             BuiltInParameter.ALL_MODEL_FAMILY_NAME
        ]
        for bip in fam_name_params:
            param = element_type.get_Parameter(bip)
            if param and param.HasValue:
                fam_name_val = param.AsValueString()
                if fam_name_val:
                    return fam_name_val

    except Exception:
        family_name = "Error Getting Family"
    return family_name if family_name else "N/A"


def format_csv_value(value):
    """Formats a value for CSV, quoting if necessary and escaping quotes."""
    str_val = str(value)
    # Escape double quotes within the string
    escaped_val = str_val.replace('"', '""')
    # Enclose in double quotes if it contains comma, double quote, or newline
    if ',' in escaped_val or '"' in escaped_val or '\n' in escaped_val or '\r' in escaped_val:
        return '"' + escaped_val + '"'
    else:
        return escaped_val

# --- Main Logic ---

# Find the target level
level_collector = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType()
target_level = None
for level in level_collector:
    if level.Name == target_level_name:
        target_level = level
        break

if not target_level:
    print("# Error: Level '{{}}' not found.".format(target_level_name))
    # No EXPORT marker printed, so no file will be saved
else:
    target_level_id = target_level.Id
    # Make filename safe, replacing spaces and dashes
    safe_level_name = target_level_name.replace(' ','_').replace('-','_')
    output_filename = "curtain_elements_{{}}.xlsx".format(safe_level_name)

    # List to hold CSV lines
    csv_lines = []
    # Define headers based on the requested fields
    headers = [
        "Mullion Family Name", "Mullion Type Name", "Mullion Length (ft)", "Mullion Calculated Area",
        "Curtain Panel Family Name", "Curtain Panel Type Name", "Curtain Panel Area (rounded)",
        "Curtain Wall Type Name", "Curtain Wall Area (sq ft)"
    ]
    csv_lines.append(",".join([format_csv_value(h) for h in headers]))

    # Find Curtain Walls associated with the target level
    # Check WALL_BASE_CONSTRAINT parameter which holds the LevelId
    wall_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType()

    relevant_curtain_walls = []
    for wall in wall_collector:
        if not isinstance(wall, Wall):
            continue
        try:
            cg = wall.CurtainGrid # Accessing this confirms it's a curtain type
            if cg:
                 level_id_param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
                 if level_id_param and level_id_param.AsElementId() == target_level_id:
                     relevant_curtain_walls.append(wall)
        except Exception:
             continue # Ignore walls that aren't curtain walls or cause errors

    # Process each relevant Curtain Wall
    for wall in relevant_curtain_walls:
        curtain_grid = None
        try:
            curtain_grid = wall.CurtainGrid
        except Exception:
            continue # Skip if cannot get grid

        if not curtain_grid:
            continue

        wall_type = get_element_type(wall)
        wall_type_name = safe_get_name(wall_type)
        # Get wall area in internal units (sq ft)
        wall_area_internal = get_parameter_value_double(wall, BuiltInParameter.HOST_AREA_COMPUTED)
        # Format wall area for output
        wall_area_str = "{:.2f}".format(wall_area_internal)

        # --- Process Mullions ---
        mullion_ids_set = set()
        try:
            locked_mullions = curtain_grid.GetMullionIds() # Includes locked mullions
            if locked_mullions:
                for m_id in locked_mullions: mullion_ids_set.add(m_id)
        except Exception: pass # Ignore errors getting mullion IDs

        try:
            unlocked_mullions = curtain_grid.GetUnlockedMullionIds() # Get unlocked mullions
            if unlocked_mullions:
                for m_id in unlocked_mullions: mullion_ids_set.add(m_id)
        except Exception: pass # Ignore errors getting unlocked mullion IDs

        mullion_ids = List[ElementId](mullion_ids_set) # Convert set back to List for iteration

        for mullion_id in mullion_ids:
            mullion = None
            try:
                mullion = doc.GetElement(mullion_id)
                if isinstance(mullion, Mullion):
                    mullion_type = get_element_type(mullion)
                    mullion_family_name = safe_get_family_name(mullion_type)
                    mullion_type_name = safe_get_name(mullion_type)

                    mullion_length_internal = 0.0 # Revit internal units (feet)
                    loc_curve = None
                    if hasattr(mullion, 'LocationCurve') and mullion.LocationCurve:
                       loc_curve = mullion.LocationCurve
                       if loc_curve and isinstance(loc_curve, Curve):
                           try:
                               mullion_length_internal = loc_curve.Length
                           except Exception: pass # Ignore if length cannot be obtained

                    # Calculate area based on internal length (assuming units are feet)
                    mullion_calc_area_internal = (mullion_length_internal * 0.45) / 2.0
                    # Format for output
                    mullion_length_str = "{:.2f}".format(mullion_length_internal)
                    mullion_calc_area_str = "{:.2f}".format(mullion_calc_area_internal)

                    # Create row data for Mullion
                    row_data = [
                        mullion_family_name, mullion_type_name, mullion_length_str, mullion_calc_area_str,
                        "", "", "", # Empty Panel fields
                        wall_type_name, wall_area_str
                    ]
                    csv_lines.append(",".join([format_csv_value(d) for d in row_data]))

            except Exception as e_mullion:
                # print("# Error processing Mullion ID {{}}: {{}}".format(mullion_id.IntegerValue if mullion_id else "N/A", e_mullion))
                pass # Continue to next mullion

        # --- Process Panels ---
        panel_ids = List[ElementId]()
        try:
            panel_ids_collection = curtain_grid.GetPanelIds()
            if panel_ids_collection:
                 panel_ids = List[ElementId](panel_ids_collection)
        except Exception:
             pass # Ignore errors getting panel IDs

        for panel_id in panel_ids:
            panel = None
            try:
                panel = doc.GetElement(panel_id)
                if panel: # Could be Panel class or Wall class (infill)
                    panel_type = get_element_type(panel)
                    panel_family_name = safe_get_family_name(panel_type)
                    panel_type_name = safe_get_name(panel_type)

                    panel_area_internal = 0.0 # Revit internal units (sq ft)
                    # Try HOST_AREA_COMPUTED parameter first
                    area_param = panel.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                    if area_param and area_param.HasValue:
                        panel_area_internal = area_param.AsDouble()
                    # Fallback: Check if element has Area property
                    elif hasattr(panel, 'Area'):
                        try: panel_area_internal = panel.Area
                        except: pass

                    # Round the panel area to the nearest whole number
                    panel_area_rounded = int(System.Math.Round(panel_area_internal, 0)) # Round to 0 decimal places
                    panel_area_str = str(panel_area_rounded) # Rounded number as string

                    # Create row data for Panel
                    row_data = [
                        "", "", "", "", # Empty Mullion fields
                        panel_family_name, panel_type_name, panel_area_str,
                        wall_type_name, wall_area_str
                    ]
                    csv_lines.append(",".join([format_csv_value(d) for d in row_data]))

            except Exception as e_panel:
                # print("# Error processing Panel ID {{}}: {{}}".format(panel_id.IntegerValue if panel_id else "N/A", e_panel))
                pass # Continue to next panel

    # Combine all lines into a single string for export
    if len(csv_lines) > 1: # Check if we have data besides the header
        csv_data_string = "\n".join(csv_lines)
        # Print the export marker and data
        print("EXPORT::EXCEL::{{}}".format(output_filename))
        print(csv_data_string)
    else:
        print("# No curtain elements found on level '{{}}' or errors occurred during processing.".format(target_level_name))

# End of the 'else' block for level found