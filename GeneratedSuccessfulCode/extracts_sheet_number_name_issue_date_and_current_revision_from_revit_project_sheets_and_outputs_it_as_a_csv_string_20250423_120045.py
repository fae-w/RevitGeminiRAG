# Purpose: This script extracts sheet number, name, issue date, and current revision from Revit project sheets and outputs it as a CSV string.

﻿import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, BuiltInParameter, ElementId
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
            sheet_number = sheet.SheetNumber
            sheet_name = sheet.Name

            # Get 'Sheet Issue Date' parameter value
            issue_date_param = sheet.get_Parameter(BuiltInParameter.SHEET_ISSUE_DATE)
            # Fallback to lookup by name if BuiltInParameter fails
            if issue_date_param is None or issue_date_param.Id == ElementId.InvalidElementId:
                issue_date_param = sheet.LookupParameter("Sheet Issue Date")

            issue_date_value = "N/A" # Default value
            if issue_date_param and issue_date_param.HasValue:
                issue_date_str = issue_date_param.AsString()
                if not String.IsNullOrEmpty(issue_date_str):
                    issue_date_value = issue_date_str

            # Get 'Current Revision' parameter value
            # This parameter often stores the revision sequence identifier (e.g., "1", "A") as text
            current_rev_param = sheet.get_Parameter(BuiltInParameter.SHEET_CURRENT_REVISION)
            # Fallback to lookup by name
            if current_rev_param is None or current_rev_param.Id == ElementId.InvalidElementId:
                 current_rev_param = sheet.LookupParameter("Current Revision")

            current_rev_value = "N/A" # Default value
            if current_rev_param and current_rev_param.HasValue:
                current_rev_str = current_rev_param.AsString()
                # AsString might return None or empty string for some parameter types even if HasValue is true
                if not String.IsNullOrEmpty(current_rev_str):
                    current_rev_value = current_rev_str
                # Alternative for ElementId-based revisions (less common for this specific param name)
                # elif current_rev_param.StorageType == StorageType.ElementId:
                #     rev_id = current_rev_param.AsElementId()
                #     if rev_id != ElementId.InvalidElementId:
                #         rev_elem = doc.GetElement(rev_id)
                #         if rev_elem:
                #              # Assuming it's a Revision element, get its number/identifier
                #              # Might need Revision class import and check type
                #              # current_rev_value = rev_elem.LookupParameter("Revision Number")?.AsString() or rev_elem.Name or "ID:{}".format(rev_id.IntegerValue)
                #              pass # Implement specific logic if needed
            else:
                # As a secondary fallback, try the GetCurrentRevision method which returns the ElementId
                # This is useful if the parameter isn't populated but the sheet is associated with revisions
                current_rev_id = sheet.GetCurrentRevision()
                if current_rev_id != ElementId.InvalidElementId:
                    current_rev_elem = doc.GetElement(current_rev_id)
                    if current_rev_elem:
                         # Attempt to get the Revision Number property or parameter
                         # Property might not exist directly in API, Parameter is safer
                         rev_num_param = current_rev_elem.get_Parameter(BuiltInParameter.REVISION_SEQUENCE_NUM) # Often holds the sequence number
                         if rev_num_param and rev_num_param.HasValue:
                              current_rev_value = rev_num_param.AsInteger().ToString() # Or AsString() depending on format
                         else: # Fallback parameter names
                            rev_desc_param = current_rev_elem.get_Parameter(BuiltInParameter.REVISION_DESCRIPTION)
                            if rev_desc_param and rev_desc_param.HasValue:
                                current_rev_value = rev_desc_param.AsString()
                            else:
                                current_rev_value = "Rev ID:{}".format(current_rev_id.IntegerValue)


            # Escape quotes for CSV safety
            safe_sheet_number = '"' + sheet_number.replace('"', '""') + '"'
            safe_sheet_name = '"' + sheet_name.replace('"', '""') + '"'
            safe_issue_date = '"' + issue_date_value.replace('"', '""') + '"'
            safe_current_rev = '"' + current_rev_value.replace('"', '""') + '"'

            # Append data row
            csv_lines.append(','.join([safe_sheet_number, safe_sheet_name, safe_issue_date, safe_current_rev]))
            processed_count += 1
        except Exception as e:
            # print("# Error processing Sheet {}: {}".format(sheet.Id, e)) # Optional: Log errors for debugging
            # Attempt to add partial info if possible
            try:
                error_name = sheet.Name if sheet and sheet.IsValidObject else "Invalid Sheet ID {}".format(sheet.Id if sheet else "Unknown")
                csv_lines.append('"{}","{}","Error","Error Retrieving Data: {}"'.format(
                    sheet.SheetNumber.replace('"', '""') if sheet and sheet.SheetNumber else "Unknown",
                    error_name.replace('"', '""'),
                    str(e).replace('"', '""')
                ))
            except:
                 csv_lines.append('"Unknown","Error","Error","Error during error handling"')


# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::sheet_issue_revision_data.csv")
    print(file_content)
else:
    print("# No ViewSheet elements found or processed in the project.")

# Optional: Print summary message
# print("# Processed {} sheets.".format(processed_count))