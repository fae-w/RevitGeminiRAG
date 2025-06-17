# Purpose: This script extracts sheet number, name, issue date, and current revision information from Revit projects and exports it to a CSV format.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, BuiltInParameter, ElementId, Revision, StorageType
from System import String

# List to hold CSV lines
csv_lines = []
# Add header row - Ensure parameters are quoted if they might contain commas
csv_lines.append('"Sheet Number","Sheet Name","Sheet Issue Date","Current Revision"')

# Collect all ViewSheet elements
collector = FilteredElementCollector(doc).OfClass(ViewSheet)

# Iterate through sheets and get data
processed_count = 0
for sheet in collector:
    if isinstance(sheet, ViewSheet) and sheet.IsValidObject:
        try:
            sheet_number = sheet.SheetNumber if sheet.SheetNumber else "N/A"
            sheet_name = sheet.Name if sheet.Name else "Unnamed Sheet"

            # --- Get 'Sheet Issue Date' parameter value ---
            issue_date_value = "N/A" # Default value
            issue_date_param = sheet.get_Parameter(BuiltInParameter.SHEET_ISSUE_DATE)
            # Fallback to lookup by name if BuiltInParameter fails or doesn't exist
            if issue_date_param is None or issue_date_param.Id == ElementId.InvalidElementId:
                issue_date_param = sheet.LookupParameter("Sheet Issue Date")

            if issue_date_param and issue_date_param.HasValue:
                # AsString is generally best for dates stored as text
                issue_date_str = issue_date_param.AsString()
                if not String.IsNullOrEmpty(issue_date_str):
                    issue_date_value = issue_date_str
                # elif issue_date_param.StorageType == StorageType.Double: # Check if it's stored as number (unlikely for issue date)
                #     # Potentially convert from internal units if needed, or format directly
                #     issue_date_value = issue_date_param.AsDouble().ToString()
                # elif issue_date_param.StorageType == StorageType.Integer: # Less likely
                #     issue_date_value = issue_date_param.AsInteger().ToString()

            # --- Get 'Current Revision' parameter value ---
            current_rev_value = "N/A" # Default value
            current_rev_param = sheet.get_Parameter(BuiltInParameter.SHEET_CURRENT_REVISION)
            # Fallback to lookup by name
            if current_rev_param is None or current_rev_param.Id == ElementId.InvalidElementId:
                 current_rev_param = sheet.LookupParameter("Current Revision")

            if current_rev_param and current_rev_param.HasValue:
                # AsString() is typical for this parameter which usually holds the revision sequence ID (e.g., "1", "A")
                current_rev_str = current_rev_param.AsString()
                if not String.IsNullOrEmpty(current_rev_str):
                    current_rev_value = current_rev_str
                # Fallback check if it's an ElementId (less common for this specific *parameter*)
                elif current_rev_param.StorageType == StorageType.ElementId:
                    rev_id = current_rev_param.AsElementId()
                    if rev_id != ElementId.InvalidElementId:
                        rev_elem = doc.GetElement(rev_id)
                        if rev_elem and isinstance(rev_elem, Revision):
                            # Try to get the sequence number or description from the Revision element
                            rev_num_param = rev_elem.get_Parameter(BuiltInParameter.REVISION_SEQUENCE_NUM)
                            if rev_num_param and rev_num_param.HasValue:
                                current_rev_value = rev_num_param.AsInteger().ToString()
                            else:
                                rev_desc_param = rev_elem.get_Parameter(BuiltInParameter.REVISION_DESCRIPTION)
                                if rev_desc_param and rev_desc_param.HasValue and not String.IsNullOrEmpty(rev_desc_param.AsString()):
                                     current_rev_value = rev_desc_param.AsString()
                                else:
                                     current_rev_value = "Rev ID:{}".format(rev_id.IntegerValue) # Fallback display
                        else:
                             current_rev_value = "Invalid Rev ID:{}".format(rev_id.IntegerValue)
                    else: # Parameter is ElementId type but holds InvalidElementId
                         current_rev_value = "N/A (Invalid ID)"
                else: # Parameter HasValue but AsString is null/empty and not ElementId
                     current_rev_value = "N/A (Unknown Format)"

            # --- Secondary Fallback: Use GetCurrentRevision() method ---
            # This method directly gives the ElementId of the latest revision applied to the sheet.
            # Useful if the SHEET_CURRENT_REVISION *parameter* is not populated but revisions exist.
            if current_rev_value == "N/A": # Only try if the parameter didn't yield a result
                current_rev_id = sheet.GetCurrentRevision()
                if current_rev_id != ElementId.InvalidElementId:
                    current_rev_elem = doc.GetElement(current_rev_id)
                    if current_rev_elem and isinstance(current_rev_elem, Revision):
                         # Attempt to get the Revision Number (Sequence Number) or Description
                         rev_num_param = current_rev_elem.get_Parameter(BuiltInParameter.REVISION_SEQUENCE_NUM)
                         if rev_num_param and rev_num_param.HasValue:
                              current_rev_value = rev_num_param.AsInteger().ToString()
                         else:
                            rev_desc_param = current_rev_elem.get_Parameter(BuiltInParameter.REVISION_DESCRIPTION)
                            if rev_desc_param and rev_desc_param.HasValue and not String.IsNullOrEmpty(rev_desc_param.AsString()):
                                current_rev_value = rev_desc_param.AsString()
                            else: # Fallback if sequence/description not found on Revision element
                                current_rev_value = "Rev ID:{}".format(current_rev_id.IntegerValue)
                    else: # ID from GetCurrentRevision is valid but not a Revision element (unlikely)
                         current_rev_value = "Rev ID:{} (Not Revision Element)".format(current_rev_id.IntegerValue)
                # If GetCurrentRevision also returns InvalidElementId, current_rev_value remains "N/A"

            # Escape quotes for CSV safety
            safe_sheet_number = '"' + sheet_number.replace('"', '""') + '"'
            safe_sheet_name = '"' + sheet_name.replace('"', '""') + '"'
            safe_issue_date = '"' + issue_date_value.replace('"', '""') + '"'
            safe_current_rev = '"' + current_rev_value.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_sheet_number, safe_sheet_name, safe_issue_date, safe_current_rev]))
            processed_count += 1
        except Exception as e:
            # Attempt to add partial info if possible during an error
            try:
                error_name = sheet.Name if sheet and sheet.IsValidObject else "Invalid Sheet ID:{}".format(sheet.Id if sheet else "Unknown")
                error_number = sheet.SheetNumber if sheet and sheet.IsValidObject and sheet.SheetNumber else "Unknown"
                csv_lines.append('"{}","{}","Error","Error Retrieving Data: {}"'.format(
                    error_number.replace('"', '""'),
                    error_name.replace('"', '""'),
                    str(e).replace('"', '""')
                ))
            except:
                 csv_lines.append('"Unknown","Error","Error","Error during error handling for sheet"')


# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::sheet_issue_revision_data.csv")
    print(file_content)
else:
    # If only the header is present or collector was empty
    if processed_count == 0 and len(csv_lines) == 1 :
         print("# No ViewSheet elements found in the project.")
    elif len(csv_lines) <=1 : # Should not happen if header is added, defensive check
         print("# No data generated.")
    # else: # Only header + error rows might exist, let the CSV export happen

# Optional: Print summary message to RevitPythonShell output (not part of export)
# print("# Processed {} sheets.".format(processed_count))