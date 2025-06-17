# Purpose: This script exports data about the currently selected elements to an Excel file (CSV format).

import clr
clr.AddReference('RevitAPI')
clr.AddReference('System') # For String formatting

from Autodesk.Revit.DB import ElementId, ElementType, Category, WorksetTable, WorksetId, WorksetKind, Element
from Autodesk.Revit.UI.Selection import Selection # Technically already in uidoc.Selection
import System

# Function to escape quotes for CSV
def escape_csv(value):
    if value is None:
        return '""'
    # Ensure value is string, replace double quotes with two double quotes, and enclose in double quotes
    return '"' + str(value).replace('"', '""') + '"'

# Get the currently selected element IDs
try:
    selected_ids = uidoc.Selection.GetElementIds()
except Exception as e:
    print("# Error getting selection: {}".format(e))
    selected_ids = []

# Check if any elements are selected
if not selected_ids or len(selected_ids) == 0:
    print("# No elements selected.")
else:
    # List to hold CSV lines (for Excel export)
    csv_lines = []
    # Add header row
    csv_lines.append('"Element ID","Category","Type Name","Element Name","Workset Name"')

    # Check if the document is workshared to get workset info
    is_workshared = doc.IsWorkshared
    workset_table = None
    if is_workshared:
        try:
            workset_table = doc.GetWorksetTable()
        except Exception as e:
            # print("# Warning: Could not get WorksetTable: {}".format(e)) # Optional debug
            is_workshared = False # Treat as non-workshared if table fails

    processed_count = 0
    for element_id in selected_ids:
        try:
            element = doc.GetElement(element_id)
            if element is None:
                # Element might have been deleted between selection and script run
                csv_lines.append(','.join([escape_csv(element_id.IntegerValue), escape_csv("Error"), escape_csv("Element Not Found"), escape_csv("N/A"), escape_csv("N/A")]))
                continue

            # --- Get Element ID ---
            elem_id_str = str(element.Id.IntegerValue)

            # --- Get Category Name ---
            category_name = "N/A"
            cat = element.Category
            if cat is not None and not System.String.IsNullOrEmpty(cat.Name):
                category_name = cat.Name
            elif cat is not None:
                category_name = "(Unnamed Category)"

            # --- Get Type Name ---
            type_name = "N/A"
            type_id = element.GetTypeId()
            if type_id is not None and type_id != ElementId.InvalidElementId:
                elem_type = doc.GetElement(type_id)
                if isinstance(elem_type, ElementType):
                    family_name = elem_type.FamilyName if hasattr(elem_type, 'FamilyName') else None
                    t_name = elem_type.Name
                    if not System.String.IsNullOrEmpty(family_name):
                        type_name = family_name + " : " + (t_name if not System.String.IsNullOrEmpty(t_name) else "(Unnamed Type)")
                    elif not System.String.IsNullOrEmpty(t_name):
                         type_name = t_name
                    else:
                         type_name = "(Unnamed Type)"
                elif elem_type is not None and hasattr(elem_type, 'Name') and not System.String.IsNullOrEmpty(elem_type.Name):
                     # Handle cases where GetTypeId() might return something other than ElementType but has a name
                     type_name = elem_type.Name + " (Non-ElementType)"
                else:
                     type_name = "(Type Not Found)"
            else:
                # Elements without a type (e.g., some system families instances like Grids, Levels)
                 if hasattr(element, 'Name') and not System.String.IsNullOrEmpty(element.Name):
                     # For things like Grids, Levels, the element name might be the most relevant 'type' indicator
                     type_name = "(System Instance)" # element.Name # Optionally use element name here
                 else:
                     type_name = "(No Type ID / System Instance)"


            # --- Get Element Name ---
            # Use Element.Name property directly
            element_name = element.Name
            if System.String.IsNullOrEmpty(element_name):
                 element_name = "(No Name)" # Provide a placeholder if name is empty

            # --- Get Workset Name ---
            workset_name = "N/A (Not Workshared)"
            if is_workshared and workset_table:
                try:
                    workset_id = element.WorksetId
                    if workset_id is not None and workset_id != WorksetId.InvalidWorksetId:
                        workset = workset_table.GetWorkset(workset_id)
                        if workset is not None:
                            workset_name = workset.Name
                        else:
                            workset_name = "(Workset Not Found)"
                    else:
                        # Might be on View Workset, User Created, etc. but ID is invalid?
                        kind_param = element.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
                        if kind_param and kind_param.HasValue:
                             ws_id_int = kind_param.AsInteger()
                             # -2 is View Workset, -3 is Standard Family workset, etc.
                             # Could try looking up by integer ID if needed, but name is usually sufficient
                             workset_name = "({})".format(ws_id_int)
                        else:
                             workset_name = "(Unknown Workset ID)"
                except Exception as ws_ex:
                    workset_name = "(Error getting Workset)"

            # Add row to CSV lines, escaping fields
            csv_line = ",".join([
                escape_csv(elem_id_str),
                escape_csv(category_name),
                escape_csv(type_name),
                escape_csv(element_name),
                escape_csv(workset_name)
            ])
            csv_lines.append(csv_line)
            processed_count += 1

        except Exception as e:
            # Log error for the specific element ID
            err_id_str = "Unknown ID"
            try:
                err_id_str = str(element_id.IntegerValue)
            except: pass
            csv_lines.append(','.join([escape_csv(err_id_str), escape_csv("ERROR"), escape_csv("Processing Error: {}".format(e)), escape_csv("N/A"), escape_csv("N/A")]))

    # Check if we gathered any data (more than just the header)
    if len(csv_lines) > 1:
        # Format the final output for export as CSV (Excel compatible)
        file_content = "\n".join(csv_lines)
        # Indicate EXCEL format, suggest .xlsx extension. Data is CSV formatted.
        print("EXPORT::EXCEL::selected_elements_report.xlsx")
        print(file_content)
    else:
        # Should not happen if selection was initially > 0, but handle just in case
        print("# No data processed from selected elements.")

# End of script