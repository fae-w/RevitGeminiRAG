# Purpose: This script exports plumbing fixture information along with associated space details to a CSV format for Excel.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI') # Though not directly used, good practice if uidoc might be needed indirectly

# Import specific classes from Autodesk.Revit.DB
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    FamilyInstance,
    BuiltInParameter,
    LocationPoint,
    XYZ,
    SpatialElement # Base class for Space
)
# Import Space class specifically from the Mechanical namespace
from Autodesk.Revit.DB.Mechanical import Space
# Import System for potential string formatting needs, although standard Python formatting is often sufficient
import System

# List to hold CSV lines for Excel export
csv_lines = []
# Add header row, ensuring quotes for safety, especially if names/marks contain commas
csv_lines.append('"Fixture Mark","Space Name","Space Number"')

# Collect all Plumbing Fixture instances
collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()

processed_count = 0
# Iterate through the collected plumbing fixtures
for fixture in collector:
    # Ensure the element is a FamilyInstance (most fixtures are)
    if isinstance(fixture, FamilyInstance):
        fixture_mark = "N/A"
        space_name = "Not in Space"
        space_number = "Not in Space"
        fixture_id_for_error = fixture.Id.ToString() # Store ID for potential error logging

        try:
            # --- Get Fixture Mark ---
            mark_param = fixture.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
            if mark_param and mark_param.HasValue:
                fixture_mark_value = mark_param.AsString()
                # Handle cases where the parameter exists but the string is empty or null
                if fixture_mark_value and fixture_mark_value.strip():
                    fixture_mark = fixture_mark_value
                else:
                    fixture_mark = "N/A (Empty)" # Indicate mark exists but is empty
            else:
                fixture_mark = "N/A (No Param)" # Indicate parameter doesn't exist or has no value

            # --- Get Fixture Location Point ---
            location = fixture.Location
            point = None
            if location and isinstance(location, LocationPoint):
                point = location.Point

            # --- Find Space at Location Point ---
            if point:
                # GetSpaceAtPoint uses the default phase settings of the document
                # For specific phase requirements, use GetSpaceAtPoint(point, phase)
                space_at_point = doc.GetSpaceAtPoint(point)

                # Check if a valid Space element was found
                if space_at_point and isinstance(space_at_point, Space):
                    # --- Get Space Name ---
                    # Prefer the Name property, fallback to parameter
                    space_name_prop = space_at_point.Name
                    if space_name_prop and space_name_prop.strip():
                        space_name = space_name_prop
                    else:
                         name_param = space_at_point.get_Parameter(BuiltInParameter.SPACE_NAME)
                         if name_param and name_param.HasValue:
                             space_name_val = name_param.AsString()
                             if space_name_val and space_name_val.strip():
                                 space_name = space_name_val
                             else:
                                 space_name = "Unnamed Space (Empty Param)"
                         else:
                              space_name = "Unnamed Space (No Param)"

                    # --- Get Space Number ---
                    # Prefer the Number property, fallback to parameter
                    space_number_prop = space_at_point.Number
                    if space_number_prop and space_number_prop.strip():
                        space_number = space_number_prop
                    else:
                         num_param = space_at_point.get_Parameter(BuiltInParameter.SPACE_NUMBER)
                         if num_param and num_param.HasValue:
                             space_num_val = num_param.AsString()
                             if space_num_val and space_num_val.strip():
                                 space_number = space_num_val
                             else:
                                 space_number = "Unnumbered Space (Empty Param)"
                         else:
                              space_number = "Unnumbered Space (No Param)"
                # else: fixture point is not within any Space boundary
            else:
                # Handle cases where the fixture doesn't have a LocationPoint (less common for fixtures)
                space_name = "No Location Point"
                space_number = "No Location Point"

            # Format the data row for CSV/Excel, escaping double quotes
            safe_mark = '"' + str(fixture_mark).replace('"', '""') + '"'
            safe_space_name = '"' + str(space_name).replace('"', '""') + '"'
            safe_space_number = '"' + str(space_number).replace('"', '""') + '"'

            # Append the successfully processed row
            csv_lines.append(safe_mark + ',' + safe_space_name + ',' + safe_space_number)
            processed_count += 1

        except Exception as e:
            # Log error details for debugging if needed (uncomment print lines in development)
            # print("Error processing Fixture ID {}: {}".format(fixture_id_for_error, str(e)))
            # Optionally add an error row to the export
            try:
                 safe_mark_error = '"' + str(fixture_mark).replace('"', '""') + '"' # Use mark if retrieved before error
                 safe_space_name_error = '"' + "Error Processing" + '"'
                 safe_space_number_error = '"' + "ID: " + fixture_id_for_error + '"' # Put ID in number field for reference
                 csv_lines.append(safe_mark_error + ',' + safe_space_name_error + ',' + safe_space_number_error)
                 processed_count += 1 # Count errors as processed rows if error row added
            except:
                 pass # Ignore if even error logging fails

# Check if any data rows (including potential error rows) were added beyond the header
if processed_count > 0:
    # Join the lines into a single string with newline separators
    file_content = "\n".join(csv_lines)
    # Print the export header and the data content
    print("EXPORT::EXCEL::plumbing_fixtures_by_space.xlsx")
    print(file_content)
else:
    # If no fixtures were found or processed, print a message
    print("# No plumbing fixture instances found or processed.")