# Purpose: This script changes the line style of detail lines in a Revit document from one specified style to another.

# Purpose: This script changes the line style of detail lines in a Revit document from one style to another.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    DetailLine,
    GraphicsStyle,
    ElementId,
    Element
)

# --- Configuration ---
# Define the names of the line styles
source_style_name = "Hidden Lines"
target_style_name = "Medium Lines"

# --- Find Line Style Elements ---
hidden_style_element = None
medium_style_element = None

# Collect all GraphicsStyle elements (which represent line styles among other things)
graphics_styles = FilteredElementCollector(doc).OfClass(GraphicsStyle).ToElements()

for style in graphics_styles:
    # Check if the style category corresponds to Detail Lines (or Lines in general)
    # GraphicsStyleCategory returns the Category object
    style_category = style.GraphicsStyleCategory
    if style_category and style_category.Id == ElementId(BuiltInCategory.OST_Lines):
        if style.Name == source_style_name:
            hidden_style_element = style
        elif style.Name == target_style_name:
            medium_style_element = style
    # Break loop if both styles are found
    if hidden_style_element and medium_style_element:
        break

# --- Validate Line Styles Found ---
if not hidden_style_element:
    print("# Error: Line style '{}' not found.".format(source_style_name))
elif not medium_style_element:
    print("# Error: Line style '{}' not found.".format(target_style_name))
else:
    # --- Find and Modify Detail Lines ---
    hidden_style_id = hidden_style_element.Id
    modified_count = 0

    # Collect all DetailLine elements
    detail_line_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Lines).OfClass(DetailLine).WhereElementIsNotElementType()

    for line in detail_line_collector:
        if isinstance(line, DetailLine):
            try:
                current_style = line.LineStyle
                # Check if the current line style matches the source style
                if current_style and current_style.Id == hidden_style_id:
                    # Change the line style to the target style
                    # Note: The external C# code handles the transaction
                    line.LineStyle = medium_style_element
                    modified_count += 1
            except Exception as e:
                # Log error for specific line if needed
                # print("# Error processing line {}: {}".format(line.Id, e))
                pass # Continue with the next line

    # Optional: Print summary
    # print("# Found {} detail lines using '{}' style.".format(modified_count, source_style_name))
    # print("# Changed {} detail lines to '{}' style.".format(modified_count, target_style_name))

# Final check if styles were not found initially
if not hidden_style_element or not medium_style_element:
    # print("# No lines were modified because one or both line styles were not found.")
    pass