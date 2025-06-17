# Import necessary namespaces
import clr
clr.AddReference('RevitAPI')
# Import specific classes needed
from Autodesk.Revit.DB import FilteredElementCollector, TextNoteType, BuiltInParameter, ElementId, ElementType

# --- Configuration ---
# The exact name of the desired ArrowheadType style as it appears in Revit ElementType names
target_arrowhead_name = "Filled Dot 1.5mm"

# --- Find the Target Arrowhead ElementId ---
target_arrowhead_id = None
# Arrowhead types are represented as ElementTypes. Collect all ElementTypes
# and find the one matching the target name.
element_type_collector = FilteredElementCollector(doc).OfClass(ElementType).WhereElementIsElementType()

found_arrowhead_element = None
for etype in element_type_collector:
    # Use the parameter for name checking for robustness
    name_param = etype.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    if name_param and name_param.AsString() == target_arrowhead_name:
        # Found an ElementType with the matching name. Assume it's the correct arrowhead.
        # A perfect validation that it's *specifically* an arrowhead type is difficult,
        # but matching the name is the standard approach.
        found_arrowhead_element = etype
        target_arrowhead_id = etype.Id
        break # Exit loop once found

if target_arrowhead_id is None:
    print("# Error: Arrowhead ElementType named '{}' not found in the document. Cannot proceed.".format(target_arrowhead_name))
else:
    # --- Collect TextNoteType Elements ---
    # Use TextNoteType for the OfClass filter and ensure they are types
    text_note_type_collector = FilteredElementCollector(doc).OfClass(TextNoteType).WhereElementIsElementType()
    text_types_list = list(text_note_type_collector) # Convert to list

    modified_count = 0
    error_count = 0
    skipped_count = 0

    if not text_types_list:
         print("# No TextNoteTypes found in the document.")
    else:
        # --- Iterate and Modify TextNoteTypes ---
        for text_type in text_types_list:
            # Check if it's actually a TextNoteType (though filtered, belt-and-suspenders)
            if isinstance(text_type, TextNoteType):
                try:
                    # Get the 'Leader Arrowhead' parameter using BuiltInParameter
                    leader_arrowhead_param = text_type.get_Parameter(BuiltInParameter.LEADER_ARROWHEAD)

                    if leader_arrowhead_param:
                        # Check if the parameter can be changed
                        if not leader_arrowhead_param.IsReadOnly:
                            # Check if the current value is already the target value
                            current_value_id = leader_arrowhead_param.AsElementId()
                            if current_value_id != target_arrowhead_id:
                                # Set the parameter to the target ArrowheadType ElementId
                                leader_arrowhead_param.Set(target_arrowhead_id)
                                modified_count += 1
                            else:
                                 skipped_count += 1 # Already set correctly
                        else:
                            # Parameter is read-only for this type
                            skipped_count += 1
                    else:
                        # Parameter doesn't exist on this text note type
                        skipped_count += 1

                except Exception as e:
                    # Attempt to get the type name for better error reporting
                    type_name = "Unknown Type Name"
                    try:
                        name_param = text_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                        if name_param:
                           type_name = name_param.AsString()
                    except:
                        pass # Keep default "Unknown Type Name"
                    print("# Error modifying TextNoteType '{}' (ID: {}): {}".format(type_name, text_type.Id, e))
                    error_count += 1
            else:
                 # Should not happen with the collector setup, but log if it does
                 print("# Skipped element ID {} as it is not a TextNoteType.".format(text_type.Id))
                 skipped_count += 1


        # --- Final Report ---
        print("# --- Script Execution Summary ---")
        if modified_count > 0:
            print("# Successfully set Leader Arrowhead to '{}' for {} TextNoteType(s).".format(target_arrowhead_name, modified_count))
        if skipped_count > 0:
             print("# Skipped {} TextNoteType(s) (already set, read-only, or missing parameter).".format(skipped_count))
        if error_count > 0:
            print("# Encountered errors modifying {} TextNoteType(s). Check details above.".format(error_count))
        if modified_count == 0 and error_count == 0 and skipped_count > 0 and text_types_list:
             print("# No modifications were needed for the {} TextNoteType(s) found.".format(len(text_types_list)))
        elif modified_count == 0 and error_count == 0 and skipped_count == 0 and text_types_list:
             # This case might indicate the target arrowhead wasn't found or other issues
             print("# Found {} TextNoteType(s), but none were modified, skipped, or caused errors.".format(len(text_types_list)))
        # Case for no text types found handled above.
        # Case for arrowhead not found handled at the beginning.

# else: Error message about missing arrowhead ElementType was already printed above