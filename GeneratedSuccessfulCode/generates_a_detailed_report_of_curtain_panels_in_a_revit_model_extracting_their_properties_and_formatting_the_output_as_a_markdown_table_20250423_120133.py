# Purpose: This script generates a detailed report of curtain panels in a Revit model, extracting their properties and formatting the output as a Markdown table.

﻿# Mandatory Imports
import clr
clr.AddReference('System')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Sometimes needed indirectly

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, BuiltInParameter,
    Element, ElementId, ElementType, Panel, Wall, CurtainSystem, CurtainGrid,
    Parameter, StorageType, Material,
    LocationPoint, LocationCurve, XYZ, BoundingBoxXYZ,
    CompoundStructure, WallKind # Added for completeness
)
from Autodesk.Revit.Exceptions import InvalidObjectException # Added import for exception handling
from System.Collections.Generic import List, ICollection, Dictionary # Ensure Dictionary is imported
import System # For Math, String formatting

# --- Helper Functions ---

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
        # Element types often have a specific Name property
        if isinstance(element_or_type, ElementType) and hasattr(element_or_type, 'Name') and element_or_type.Name:
            return element_or_type.Name
        # For instances, try getting the type first
        elif isinstance(element_or_type, Element):
            type_elem = get_element_type(element_or_type)
            if type_elem and hasattr(type_elem, 'Name') and type_elem.Name:
                return type_elem.Name
        # Fallback for elements without direct Type Name or whose type couldn't be fetched cleanly
        param = element_or_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        if param and param.HasValue:
            name_val = param.AsValueString()
            if name_val: return name_val
        # Last resort for some elements might just be their own name if it exists
        if hasattr(element_or_type, 'Name') and element_or_type.Name:
            return element_or_type.Name

    except Exception:
        name = "Error Getting Name"
    return name if name and name != "" else "N/A"

def safe_get_family_name(element_or_type):
    """Safely get the family name from an Element or its ElementType."""
    if not element_or_type: return "N/A"
    element_type = element_or_type if isinstance(element_or_type, ElementType) else get_element_type(element_or_type)
    if not element_type: return "N/A"
    family_name = "N/A"
    try:
        if hasattr(element_type, 'FamilyName') and element_type.FamilyName:
            return element_type.FamilyName
        param = element_type.get_Parameter(BuiltInParameter.ALL_MODEL_FAMILY_NAME) # General fallback
        if param and param.HasValue:
            fam_name_val = param.AsValueString()
            if fam_name_val: return fam_name_val
    except Exception:
        family_name = "Error Getting Family"
    return family_name if family_name and family_name != "" else "N/A"

def get_parameter_value_string(element, built_in_param, default="N/A"):
    """Safely get parameter value as string."""
    if not element: return default
    param = element.get_Parameter(built_in_param)
    if param:
        try:
            if param.StorageType == StorageType.String:
                val = param.AsString()
                return val if val and val != "" else default
            elif param.StorageType == StorageType.ElementId:
                elem_id = param.AsElementId()
                if elem_id and elem_id != ElementId.InvalidElementId:
                    linked_elem = doc.GetElement(elem_id)
                    # Use safe_get_name to handle potential complexities of linked element names
                    return safe_get_name(linked_elem) if linked_elem else default
                else:
                    return default
            elif param.HasValue:
                # AsValueString() is often the best bet for user-facing representation
                val_str = param.AsValueString()
                return val_str if val_str and val_str != "" else default
            else:
                return default
        except Exception:
            return default # Error during extraction
    return default

def get_parameter_value_double(element, built_in_param, default=0.0):
    """Safely get parameter value as double (feet or sq feet)."""
    if not element: return default
    param = element.get_Parameter(built_in_param)
    if param and param.HasValue:
        try:
            # Check storage type to be sure it's numeric
            if param.StorageType == StorageType.Double:
                return param.AsDouble()
            elif param.StorageType == StorageType.Integer:
                 # Convert integer to double if needed, though less common for these params
                 return float(param.AsInteger())
            else:
                 # Try to parse if it's a string representing a number? Less safe.
                 # For now, return default if not Double or Integer
                 return default
        except Exception:
            return default
    return default

def format_length(value_internal_feet):
    """Formats a length value (in feet) to string with 2 decimal places."""
    # Ensure value is actually a number before formatting
    if isinstance(value_internal_feet, (float, int)):
        return "{:.2f}".format(value_internal_feet) # Corrected format string
    return "N/A"

def format_area(value_internal_sqfeet):
    """Formats an area value (in sq feet) to string with 2 decimal places."""
    if isinstance(value_internal_sqfeet, (float, int)):
        return "{:.2f}".format(value_internal_sqfeet) # Corrected format string
    return "N/A"

def format_point(xyz):
    """Formats an XYZ point to a string."""
    if isinstance(xyz, XYZ):
        return "({:.2f}, {:.2f}, {:.2f})".format(xyz.X, xyz.Y, xyz.Z) # Corrected format string
    return "N/A"

def get_bounding_box_center(element):
    """Safely get the center of the element's bounding box."""
    center_pt = None
    if not element or not hasattr(element, 'get_BoundingBox'): return "N/A"
    try:
        bb = element.get_BoundingBox(None) # Pass None for view to get model extents
        if bb:
            center_pt = (bb.Min + bb.Max) / 2.0
    except Exception:
        pass # Ignore errors getting bounding box
    return center_pt

def get_material_name(element_type):
    """Safely get the primary material name from an ElementType."""
    if not element_type or not isinstance(element_type, ElementType): return "N/A"
    material_name = "N/A"
    try:
        # Try common parameters for material on the Type
        param_bips = [
            BuiltInParameter.MATERIAL_ID_PARAM,        # General material parameter
            BuiltInParameter.STRUCTURAL_MATERIAL_PARAM # For structural elements
            # Add other potential material parameters if needed (e.g., specific family type params)
        ]
        for bip in param_bips:
            mat_param = element_type.get_Parameter(bip)
            if mat_param and mat_param.StorageType == StorageType.ElementId:
                mat_id = mat_param.AsElementId()
                if mat_id and mat_id != ElementId.InvalidElementId:
                    material = doc.GetElement(mat_id)
                    if isinstance(material, Material) and hasattr(material, 'Name'):
                        material_name = material.Name
                        if material_name and material_name != "":
                             break # Found a valid material name

        # If still N/A, check if it's a WallType and look at CompoundStructure
        if (material_name == "N/A" or material_name == "") and hasattr(element_type, 'GetCompoundStructure'):
             cs = element_type.GetCompoundStructure()
             if cs:
                 # Try the exterior layer first as a guess
                 ext_layer_index = cs.GetExteriorLayerIndex()
                 if ext_layer_index != -1:
                     layers = cs.GetLayers()
                     if layers and ext_layer_index < layers.Count:
                        layer_mat_id = layers[ext_layer_index].MaterialId
                        if layer_mat_id and layer_mat_id != ElementId.InvalidElementId:
                            material = doc.GetElement(layer_mat_id)
                            if isinstance(material, Material) and hasattr(material, 'Name'):
                                material_name = material.Name

                 # If exterior didn't work, try the first layer (less specific)
                 if (material_name == "N/A" or material_name == ""):
                     layers = cs.GetLayers()
                     if layers and layers.Count > 0:
                         first_layer_mat_id = layers[0].MaterialId
                         if first_layer_mat_id and first_layer_mat_id != ElementId.InvalidElementId:
                             material = doc.GetElement(first_layer_mat_id)
                             if isinstance(material, Material) and hasattr(material, 'Name'):
                                 material_name = material.Name

    except Exception:
        material_name = "Error Getting Material"

    return material_name if material_name and material_name != "" else "N/A"


def format_markdown_table_cell(value):
    """Escapes pipe characters for Markdown table cells and handles None."""
    str_val = str(value) if value is not None else "N/A"
    str_val = str_val.replace('\r', '').replace('\n', ' ') # Remove newlines
    return str_val.replace("|", "\\|")


# --- Main Logic ---

panel_data_list = []

# Collect potential Curtain Grid hosts: Walls and Curtain Systems
host_collector = FilteredElementCollector(doc).WhereElementIsNotElementType()
potential_hosts = list(host_collector.OfCategory(BuiltInCategory.OST_Walls).ToElements())
# Use extend or + to combine lists, ensure CurtainSystem collector is separate if needed
cs_collector = FilteredElementCollector(doc).WhereElementIsNotElementType().OfCategory(BuiltInCategory.OST_Curtain_Systems)
potential_hosts.extend(list(cs_collector.ToElements()))


processed_panel_ids = set() # Keep track of panels already processed

for host_element in potential_hosts:
    curtain_grid = None
    host_type_name = "N/A"
    host_id_str = "N/A"
    host_category = "N/A"

    if not host_element: continue # Skip if host is somehow null

    try:
        host_id = host_element.Id
        host_id_str = str(host_id.IntegerValue)
        host_type = get_element_type(host_element)
        host_type_name = safe_get_name(host_type)

        if isinstance(host_element, Wall):
            # Check if it's a curtain wall by trying to access CurtainGrid
            if hasattr(host_element, 'CurtainGrid') and host_element.CurtainGrid: # Direct property check
                curtain_grid = host_element.CurtainGrid
                host_category = "Curtain Wall"
            else:
                 # Double check via WallType Kind if the direct check fails (unlikely needed if grid exists)
                 # wall_type = host_type
                 # if wall_type and isinstance(wall_type, WallType) and wall_type.Kind == WallKind.Curtain:
                 #      Maybe log warning? For this report, only care if it has panels.
                 #      pass
                 continue # Not a curtain wall with a grid we can access


        elif isinstance(host_element, CurtainSystem):
            # Curtain systems have a CurtainGrids property (a map)
            if hasattr(host_element, 'CurtainGrids') and host_element.CurtainGrids and not host_element.CurtainGrids.IsEmpty:
                 # A CurtainSystem can have multiple grids (e.g., different faces)
                 # We need to iterate through them. For simplicity, let's process panels from all grids.
                 # We will store panels by ID, so duplicates across grids are handled.
                 host_category = "Curtain System"
                 # No single 'curtain_grid' assigned here, handled in loop below
            else:
                continue # No grids found for this system

        # --- Process Grids and Panels ---
        grids_to_process = []
        if curtain_grid: # From Curtain Wall
             grids_to_process.append(curtain_grid)
        elif host_category == "Curtain System": # From Curtain System
             try:
                 grid_map = host_element.CurtainGrids
                 if grid_map and not grid_map.IsEmpty:
                     # Use iterator instead of Keys to get values directly might be cleaner, but Keys works.
                     for grid_id in grid_map.Keys: # Iterate through grid IDs in the map
                         grid_elem = doc.GetElement(grid_id)
                         if isinstance(grid_elem, CurtainGrid):
                             grids_to_process.append(grid_elem)
             except Exception as e_gridmap:
                  # print("# Warning: Error accessing grids for Curtain System {}: {}".format(host_id_str, e_gridmap)) # Corrected format
                  pass # Continue processing other hosts

        if not grids_to_process:
            continue # Skip host if no grids found or accessible

        # Iterate through each grid found for the host
        for grid in grids_to_process:
            if not grid: continue

            panel_ids = List[ElementId]()
            unlocked_panel_ids = List[ElementId]()
            try:
                panel_ids_collection = grid.GetPanelIds()
                if panel_ids_collection:
                    panel_ids = List[ElementId](panel_ids_collection)
            except Exception as e:
                # print("# Warning: Failed getting panel IDs for host {} grid: {}".format(host_id_str, e)) # Corrected format
                pass

            try:
                unlocked_panel_ids_collection = grid.GetUnlockedPanelIds()
                if unlocked_panel_ids_collection:
                    unlocked_panel_ids = List[ElementId](unlocked_panel_ids_collection)
            except Exception as e:
                 # print("# Warning: Failed getting unlocked panel IDs for host {} grid: {}".format(host_id_str, e)) # Corrected format
                 pass
            unlocked_ids_set = set(uid.IntegerValue for uid in unlocked_panel_ids if uid is not None)

            for panel_id in panel_ids:
                if not panel_id or panel_id == ElementId.InvalidElementId: continue

                panel_id_int = panel_id.IntegerValue
                # Skip if already processed (e.g. panel belongs to grids from different Curtain Systems pointing to same geometry)
                if panel_id_int in processed_panel_ids:
                    continue

                panel = None
                try:
                    panel = doc.GetElement(panel_id)
                    if panel:
                        processed_panel_ids.add(panel_id_int) # Mark as processed

                        panel_type = get_element_type(panel)
                        panel_data = Dictionary[str, object]() # Use object for flexibility

                        panel_data["Panel ID"] = panel_id_int
                        panel_data["Panel Type"] = safe_get_name(panel_type)
                        panel_data["Panel Family"] = safe_get_family_name(panel_type)
                        panel_data["Element Type"] = panel.GetType().Name # e.g., 'Panel' or 'Wall' if it's a basic wall infill

                        # Geometry & Dimensions
                        panel_data["Area (sq ft)"] = format_area(get_parameter_value_double(panel, BuiltInParameter.HOST_AREA_COMPUTED))
                        panel_data["Width (ft)"] = format_length(get_parameter_value_double(panel, BuiltInParameter.PANEL_WIDTH))
                        panel_data["Height (ft)"] = format_length(get_parameter_value_double(panel, BuiltInParameter.PANEL_HEIGHT))

                        # Thickness - Try parameter first, then specific type properties
                        thickness = get_parameter_value_double(panel, BuiltInParameter.CURTAIN_WALL_PANELS_THICKNESS, -1.0)
                        if thickness < 0:
                            if isinstance(panel, Wall): # Basic Wall used as panel
                                try: thickness = panel.Width # Wall.Width is its thickness
                                except: thickness = -1.0
                            elif isinstance(panel, Panel): # System Panel or Glazed Panel
                                # Thickness might be in the type parameters, but less standardized than BIP
                                # Rely on the BIP for Panels. If BIP fails (-1), report N/A
                                pass
                        panel_data["Thickness (ft)"] = format_length(thickness) if thickness >= 0 else "N/A"

                        # Position & Host Info
                        panel_data["Offset (ft)"] = format_length(get_parameter_value_double(panel, BuiltInParameter.CURTAIN_WALL_PANELS_OFFSET))
                        center_pt = get_bounding_box_center(panel)
                        panel_data["Center Location"] = format_point(center_pt) if center_pt else "N/A"
                        panel_data["Host Category"] = host_category # Category of the wall/system
                        panel_data["Host Type"] = host_type_name    # Type name of the wall/system
                        panel_data["Host ID"] = host_id_str         # Instance ID of the wall/system

                        # Status & Properties
                        panel_data["Locked"] = "No" if panel_id_int in unlocked_ids_set else "Yes"
                        panel_data["Material"] = get_material_name(panel_type) # Material from the panel's type
                        panel_data["Mark"] = get_parameter_value_string(panel, BuiltInParameter.ALL_MODEL_MARK, "")
                        panel_data["Comments"] = get_parameter_value_string(panel, BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, "")

                        panel_data_list.append(panel_data)

                except InvalidObjectException: # Corrected exception type
                    # print("# Info: Panel ID {} no longer exists or is invalid.".format(panel_id_int)) # Corrected format
                    processed_panel_ids.add(panel_id_int) # Mark as processed even if invalid now
                    pass
                except Exception as e_panel:
                    # print("# Error processing Panel ID {}: {}".format(panel_id_int, e_panel)) # Corrected format
                    # Consider logging more details if needed
                    processed_panel_ids.add(panel_id_int) # Add even if error occurred to avoid retrying
                    pass # Continue to next panel

    except InvalidObjectException: # Corrected exception type
         # print("# Info: Host Element ID {} no longer exists or is invalid.".format(host_id_str)) # Corrected format
         pass # Continue to next host
    except Exception as e_host:
        # print("# Error processing Host Element ID {}: {}".format(host_id_str, e_host)) # Corrected format
        pass # Continue to next host

# --- Format Output as Markdown Table ---
markdown_lines = []
markdown_lines.append("# Curtain Panel Detailed Report")
markdown_lines.append("")

if not panel_data_list:
    markdown_lines.append("No curtain panels found in the project.")
else:
    # Define headers (ensure keys match the dictionary keys used above)
    headers = [
        "Panel ID", "Panel Type", "Panel Family", "Element Type",
        "Area (sq ft)", "Width (ft)", "Height (ft)", "Thickness (ft)",
        "Offset (ft)", "Center Location",
        "Locked", "Material", "Mark", "Comments",
        "Host Category", "Host Type", "Host ID"
    ]

    # Create header row
    markdown_lines.append("| " + " | ".join(headers) + " |")
    # Create separator row
    markdown_lines.append("|" + "---|"*len(headers))

    # Create data rows
    # Sort list by Panel ID for consistent output
    panel_data_list.sort(key=lambda p: p["Panel ID"])
    for panel_data in panel_data_list:
        row_values = [format_markdown_table_cell(panel_data.get(header, "N/A")) for header in headers]
        markdown_lines.append("| " + " | ".join(row_values) + " |")

# --- Export ---
if markdown_lines:
    markdown_output = "\n".join(markdown_lines)
    print("EXPORT::MD::curtain_panel_detailed_report.md")
    print(markdown_output)
else:
    # This case should only be reached if an error prevented even the "No panels found" message.
    print("# No data generated for the report.")