import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    ElementType,
    ElementId,
    LocationPoint,
    BoundingBoxXYZ,
    XYZ,
    ElementMulticategoryFilter,
    Category
)
from System.Collections.Generic import List
import System # For Convert, String

# Define the categories to include
target_categories_enums = [
    BuiltInCategory.OST_Walls,
    BuiltInCategory.OST_Doors,
    BuiltInCategory.OST_Windows,
    BuiltInCategory.OST_Furniture,
    BuiltInCategory.OST_MechanicalEquipment,
    BuiltInCategory.OST_ElectricalEquipment,
    BuiltInCategory.OST_LightingFixtures,
    BuiltInCategory.OST_StructuralColumns, # Represents structural columns
    BuiltInCategory.OST_Columns,           # Represents architectural columns
    BuiltInCategory.OST_StructuralFraming  # Represents beams and other framing
]

# Convert BuiltInCategory enums to ElementId list for the filter
category_ids = List[ElementId]()
for bic in target_categories_enums:
    try:
        cat = Category.GetCategory(doc, bic)
        if cat is not None:
            category_ids.Add(cat.Id)
        # else: # Optional: Warn if a built-in category doesn't exist in the model
        #     print("# Warning: Category {} not found in this document.".format(bic))
    except:
        # print("# Warning: Could not retrieve category for {}.".format(bic)) # Optional logging
        pass

# Check if any valid categories were found
if category_ids.Count == 0:
    print("# Error: No valid target categories found or resolvable in the document.")
else:
    # Create a multicategory filter
    category_filter = ElementMulticategoryFilter(category_ids)

    # Collect elements matching the categories, excluding element types
    collector = FilteredElementCollector(doc).WherePasses(category_filter).WhereElementIsNotElementType()

    # List to hold CSV lines
    csv_lines = []
    # Add header row
    csv_lines.append("ElementID,Category,TypeName,PositionX,PositionY,PositionZ")

    # Helper function for CSV quoting and escaping
    def escape_csv(value):
        """Escapes a value for safe inclusion in a CSV cell."""
        if value is None:
            return "" # Represent null as empty string in CSV
        str_value = System.Convert.ToString(value)
        # Replace double quotes with two double quotes and enclose in double quotes if needed
        if '"' in str_value or ',' in str_value or '\n' in str_value:
            return '"' + str_value.replace('"', '""') + '"'
        return str_value

    processed_count = 0
    # Iterate through collected elements
    for element in collector:
        try:
            element_id_int = element.Id.IntegerValue
            category_name = "N/A"
            type_name = "N/A"
            pos_x, pos_y, pos_z = "N/A", "N/A", "N/A"

            # Get Category Name
            cat = element.Category
            if cat is not None and not System.String.IsNullOrEmpty(cat.Name):
                category_name = cat.Name

            # Get Type Name
            type_id = element.GetTypeId()
            if type_id is not None and type_id != ElementId.InvalidElementId:
                elem_type = doc.GetElement(type_id)
                if elem_type is not None and isinstance(elem_type, ElementType):
                    if not System.String.IsNullOrEmpty(elem_type.Name):
                         type_name = elem_type.Name
                    elif hasattr(elem_type, 'FamilyName') and not System.String.IsNullOrEmpty(elem_type.FamilyName):
                         # Fallback for types with no direct Name but a FamilyName
                         type_name = elem_type.FamilyName + " (Family)"
                    else:
                        type_name = "(Unnamed Type)"
                else:
                     type_name = "(Type Element Not Found)"
            else:
                 type_name = "(No Type ID)" # Elements like basic walls might not have a typical 'type' accessible this way

            # Get Position (LocationPoint or BoundingBox center)
            location = element.Location
            point = None
            if location and isinstance(location, LocationPoint):
                point = location.Point
            else:
                # Fallback to BoundingBox center if no LocationPoint
                # Use the active view if available for potentially tighter bounds, else None
                active_view = doc.ActiveView # Can be None
                bbox = element.get_BoundingBox(active_view) # Pass None if no active view
                if bbox is not None and bbox.Min is not None and bbox.Max is not None:
                     # Check if Min and Max are distinct to avoid division by zero issues with tiny elements
                     if not bbox.Min.IsAlmostEqualTo(bbox.Max):
                          center = (bbox.Min + bbox.Max) / 2.0
                          point = center
                     else:
                          point = bbox.Min # If Min/Max are the same, use Min

            if point is not None and isinstance(point, XYZ):
                pos_x = "{:.6f}".format(point.X) # Format to 6 decimal places
                pos_y = "{:.6f}".format(point.Y)
                pos_z = "{:.6f}".format(point.Z)
            else:
                # Indicate if position could not be determined
                pos_x, pos_y, pos_z = "N/A", "N/A", "N/A"

            # Format and append data row
            row_data = [
                escape_csv(element_id_int),
                escape_csv(category_name),
                escape_csv(type_name),
                escape_csv(pos_x),
                escape_csv(pos_y),
                escape_csv(pos_z)
            ]
            csv_lines.append(",".join(row_data))
            processed_count += 1

        except Exception as e:
            # Optional: Log errors during development/debugging for specific elements
            # print("# Error processing Element ID {}: {}".format(element.Id.IntegerValue, e))
            try:
                 # Try to add row with error indication
                 err_id = element.Id.IntegerValue
                 csv_lines.append(",".join([escape_csv(err_id), escape_csv("ERROR"), escape_csv("Processing Error"), "N/A", "N/A", "N/A"]))
            except:
                pass # Ignore if even error logging fails

    # Check if any data rows were added (more than just the header)
    if processed_count > 0:
        # Format the final output string
        file_content = "\n".join(csv_lines)

        # Suggest a filename, incorporating project name if possible
        filename_suggestion = "model_element_positions.csv"
        try:
            if doc.Title and not System.String.IsNullOrEmpty(doc.Title):
                # Sanitize project title for filename
                proj_name = "".join(c for c in doc.Title if c.isalnum() or c in (' ', '_', '-')).rstrip()
                proj_name = proj_name.replace(' ', '_').replace('.rvt', '')
                if proj_name: # Ensure not empty after sanitizing
                     filename_suggestion = proj_name + "_" + filename_suggestion
        except Exception:
            pass # Ignore errors getting document title

        # Print the export marker and data
        print("EXPORT::CSV::" + filename_suggestion)
        print(file_content)
    else:
        # No elements found matching the criteria
        print("# No elements found in the specified categories.")