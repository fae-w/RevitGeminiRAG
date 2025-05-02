# Purpose: This script calculates and exports the total length of ducts per system type to a CSV file.

﻿# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # Required for Dictionary

# Import necessary Revit API classes
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    UnitTypeId, # Use UnitTypeId for compatibility
    UnitUtils,
    ElementId,
    Element,
    MEPSystemType # Corrected namespace for MEPSystemType
)
# Import classes from the Mechanical namespace
from Autodesk.Revit.DB.Mechanical import (
    Duct
)
from System.Collections.Generic import Dictionary
import System # Required for string formatting potentially

# Ensure doc is available (pre-defined)
# doc = __revit__.ActiveUIDocument.Document # Example if needed, assume 'doc' is provided

# Initialize dictionary to store total lengths per system type (internal units: feet)
system_lengths = Dictionary[str, float]()

# Collect all Duct elements (instances only)
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_DuctCurves).WhereElementIsNotElementType()

# Iterate through ducts
for duct in collector:
    # Ensure the element is actually a Duct (collector might include other curve types)
    if isinstance(duct, Duct):
        try:
            # Get length parameter
            length_param = duct.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH)
            if not length_param or not length_param.HasValue:
                # print("# Skipping Duct ID {}: No length parameter".format(duct.Id)) # Optional debug
                continue # Skip ducts without a valid length

            length_internal = length_param.AsDouble() # Length in internal units (decimal feet)

            # Get system type name associated with the duct
            system_type_name = "Unassigned" # Default if no system type assigned or found
            system_type_param = duct.get_Parameter(BuiltInParameter.RBS_SYSTEM_TYPE_PARAM)

            if system_type_param and system_type_param.HasValue:
                # Method 1: Try getting the name directly as a string (most common)
                # AsValueString() might return null/empty for some system types, especially if unset
                name_val_obj = system_type_param.AsValueString() # Returns object, check type
                if name_val_obj and isinstance(name_val_obj, basestring) and name_val_obj.strip():
                     system_type_name = name_val_obj
                else:
                     # Method 2: If string is empty/null, try getting as ElementId (points to MEPSystemType)
                     system_type_id = system_type_param.AsElementId()
                     if system_type_id != ElementId.InvalidElementId:
                         system_type_elem = doc.GetElement(system_type_id)
                         # Check if the element is a MEPSystemType and get its Name
                         if system_type_elem and isinstance(system_type_elem, MEPSystemType):
                             # MEPSystemType often uses Element.Name
                             try:
                                 # Use GetName extension method for potentially more robust name retrieval
                                 elem_name = Element.Name.__get__(system_type_elem)
                                 if elem_name and elem_name.strip():
                                     system_type_name = elem_name
                             except Exception:
                                 pass # Keep 'Unassigned' or previous value if name cannot be read
                         # Fallback: Check if it's just an Element with a name property (less likely for system type param)
                         elif system_type_elem and hasattr(system_type_elem, 'Name'):
                              try:
                                   elem_name = Element.Name.__get__(system_type_elem)
                                   if elem_name and elem_name.strip():
                                       system_type_name = elem_name
                              except Exception:
                                   pass # Keep 'Unassigned' or previous value

            # Add length to the dictionary total for this system type
            if system_lengths.ContainsKey(system_type_name):
                system_lengths[system_type_name] += length_internal
            else:
                system_lengths[system_type_name] = length_internal

        except Exception as e:
            # print("# Error processing Duct ID {}: {}".format(duct.Id, e)) # Optional debug
            pass # Silently skip ducts that cause errors during processing

# Prepare CSV output
csv_lines = []
# Add header row
csv_lines.append('"System Type","Total Length (m)"')

if system_lengths.Count > 0:
    # Sort by system type name for consistent output
    # Convert Keys collection to a Python list before sorting
    sorted_system_types = sorted(list(system_lengths.Keys))

    for system_type in sorted_system_types:
        total_length_internal = system_lengths[system_type] # Total length in feet

        # Convert total length from internal units (feet) to meters
        # Use UnitTypeId for compatibility
        total_length_meters = UnitUtils.ConvertFromInternalUnits(total_length_internal, UnitTypeId.Meters) # Corrected line

        # Format to 2 decimal places using standard string formatting
        length_meters_str = "{:.2f}".format(total_length_meters) # Simplified formatting

        # Escape double quotes in system type name for CSV safety
        # Ensure system_type is treated as a string before replace
        safe_system_type = '"' + str(system_type).replace('"', '""') + '"'

        # Append data row: "System Type Name",Length_in_meters
        csv_lines.append(','.join([safe_system_type, length_meters_str]))

    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::duct_lengths_by_system.csv")
    print(file_content)
else:
    # If no ducts were found or processed successfully
    print("EXPORT::TXT::duct_lengths_by_system_report.txt") # Use TXT if no data
    print("No Duct elements with valid System Types and Lengths found or processed.")