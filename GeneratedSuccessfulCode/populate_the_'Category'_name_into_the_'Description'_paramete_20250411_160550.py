import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, Parameter, Category, StorageType

# Get selected element IDs
selected_ids = uidoc.Selection.GetElementIds()

if not selected_ids:
    print("# No elements selected.")
else:
    processed_count = 0
    error_count = 0
    skipped_category_count = 0
    skipped_param_count = 0
    errors = []

    for element_id in selected_ids:
        try:
            element = doc.GetElement(element_id)
            if not element:
                # Should not happen with IDs from selection, but good practice
                continue

            # Check if the element belongs to the Generic Models category
            if element.Category and element.Category.Id == ElementId(BuiltInCategory.OST_GenericModel):
                category_name = element.Category.Name

                # Get the 'Description' parameter
                # Using LookupParameter is generally safer than relying on BuiltInParameter
                # as project/shared parameters might also be named 'Description'.
                desc_param = element.LookupParameter("Description")

                if desc_param and not desc_param.IsReadOnly:
                    # Check if the parameter can store a string
                    if desc_param.StorageType == StorageType.String:
                        # Set the Description parameter value to the Category name
                        # Transaction is handled externally per instructions
                        current_value = desc_param.AsString()
                        if current_value != category_name:
                            desc_param.Set(category_name)
                            processed_count += 1
                        else:
                            # No change needed, consider it skipped for parameter update
                            skipped_param_count +=1
                    else:
                        # Parameter exists but is not a string type
                        errors.append("# Skipped Element ID {}: 'Description' parameter is not a Text type.".format(element_id.IntegerValue))
                        skipped_param_count += 1
                else:
                    # Parameter not found or is read-only
                    errors.append("# Skipped Element ID {}: 'Description' parameter not found or is read-only.".format(element_id.IntegerValue))
                    skipped_param_count += 1
            else:
                # Element is not a Generic Model
                skipped_category_count += 1
                # Optional: Add message if needed for debugging non-generic models
                # errors.append("# Skipped Element ID {}: Not a Generic Model.".format(element_id.IntegerValue))

        except Exception as e:
            error_count += 1
            errors.append("# Error processing Element ID {}: {}".format(element_id.IntegerValue, str(e)))

    # Optional: Print summary (comment out if not needed)
    # print("--- Processing Summary ---")
    # print("Successfully updated 'Description' for {} Generic Models.".format(processed_count))
    # print("Skipped {} selected elements (not Generic Models).".format(skipped_category_count))
    # print("Skipped {} Generic Models (Description param issue or no change needed).".format(skipped_param_count))
    # print("Encountered {} errors.".format(error_count))
    # if errors:
    #     print("--- Errors/Skipped Details ---")
    #     for error_msg in errors:
    #         print(error_msg)