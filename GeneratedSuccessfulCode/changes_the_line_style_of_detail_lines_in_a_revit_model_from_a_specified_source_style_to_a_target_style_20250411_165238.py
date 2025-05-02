# Purpose: This script changes the line style of detail lines in a Revit model from a specified source style to a target style.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    DetailLine,
    GraphicsStyle,
    ElementId,
    Element # Included for potential broader type checking, though DetailLine is specific
)

# --- Configuration ---
# Define the names of the source and target line styles
# Note: '<Hidden>' is often used for system hidden lines, but check exact name in Revit project
source_style_name = "<Hidden>"
target_style_name = "Medium Lines"

# --- Find Line Style Elements ---
source_style_element = None
target_style_element = None

# Collect all GraphicsStyle elements (which represent line styles among other things)
graphics_styles = FilteredElementCollector(doc).OfClass(GraphicsStyle).ToElements()

for style in graphics_styles:
    # Check if the style category corresponds to Detail Lines (or Lines in general)
    # GraphicsStyleCategory returns the Category object
    style_category = style.GraphicsStyleCategory
    if style_category and style_category.Id == ElementId(BuiltInCategory.OST_Lines):
        if style.Name == source_style_name:
            source_style_element = style
        elif style.Name == target_style_name:
            target_style_element = style
    # Break loop if both styles are found
    if source_style_element and target_style_element:
        break

# --- Validate Line Styles Found ---
if not source_style_element:
    print("# Error: Source line style '{}' not found.".format(source_style_name))
elif not target_style_element:
    print("# Error: Target line style '{}' not found.".format(target_style_name))
else:
    # --- Find and Modify Detail Lines ---
    source_style_id = source_style_element.Id
    target_style_id = target_style_element.Id # Not strictly needed for setting, but good for clarity
    modified_count = 0

    # Collect all DetailLine elements
    detail_line_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Lines).OfClass(DetailLine).WhereElementIsNotElementType()

    for line in detail_line_collector:
        # Ensure it's a DetailLine instance (collector should handle this, but extra check is safe)
        if isinstance(line, DetailLine):
            try:
                # Get the current line style GraphicsStyle element
                current_style = line.LineStyle
                # Check if the current line style exists and matches the source style ID
                if current_style and current_style.Id == source_style_id:
                    # Change the line style to the target style
                    # The external C# code handles the transaction
                    line.LineStyle = target_style_element
                    modified_count += 1
            except Exception as e:
                # Optional: Log error for specific line if needed
                # print("# Error processing line {}: {}".format(line.Id, e))
                pass # Continue with the next line

    # Optional: Print summary (commented out by default)
    # print("# Processed detail lines. Found and attempted to modify {} lines using '{}' style.".format(modified_count, source_style_name))
    # print("# Changed {} detail lines to '{}' style.".format(modified_count, target_style_name))

# Final check message if styles were not found initially (handled by the initial check)
# if not source_style_element or not target_style_element:
#     print("# No lines were modified because one or both line styles were not found.")