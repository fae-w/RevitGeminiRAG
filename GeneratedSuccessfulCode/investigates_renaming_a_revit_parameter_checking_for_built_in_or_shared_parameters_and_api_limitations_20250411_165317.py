# Purpose: This script investigates renaming a Revit parameter, checking for built-in or shared parameters and API limitations.

﻿# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ParameterElement, Definition, InternalDefinition, SharedParameterElement, BuiltInParameter

# --- Parameters ---
old_name = "Comments"
new_name = "Notes"

# --- Script ---

# Check if 'Comments' is the built-in parameter
is_builtin = False
try:
    # Attempt to get the BuiltInParameter enum value corresponding to "Comments"
    # A common one is ALL_MODEL_INSTANCE_COMMENTS
    bip = BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS
    bip_param_elem = ParameterElement.GetParameterElement(doc, bip)
    if bip_param_elem:
        bip_def = bip_param_elem.GetDefinition()
        if bip_def and bip_def.Name == old_name:
            is_builtin = True
            print("# The parameter named 'Comments' appears to be the built-in parameter.")
            print("# Built-in parameters cannot be renamed via the API.")
except Exception:
    # Handle cases where ALL_MODEL_INSTANCE_COMMENTS might not exist or other errors
    pass

if is_builtin:
    print("# Error: Cannot rename the built-in 'Comments' parameter.")
else:
    # If not the built-in one, search for project/shared parameters
    found_param_element = None
    param_elements = FilteredElementCollector(doc).OfClass(ParameterElement)

    for elem in param_elements:
        # Ensure it's a ParameterElement before getting definition
        if isinstance(elem, ParameterElement):
            try:
                definition = elem.GetDefinition()
                if definition and definition.Name == old_name:
                    # Check if it's a shared parameter, as they are generally not renameable directly in the project
                    if isinstance(elem, SharedParameterElement):
                         print("# Found a Shared Parameter named 'Comments'. Shared parameter definitions cannot be renamed through the project API.")
                         found_param_element = "shared_no_rename"
                         break # Stop searching if we found a shared one
                    # Check if it's a project parameter based on an internal definition (non-shared)
                    elif isinstance(definition, InternalDefinition):
                         found_param_element = elem
                         break # Found a potentially renameable project parameter
            except Exception as e:
                 # print(f"# Skipping element {elem.Id} due to error: {e}") # Debug
                 pass # Ignore elements that might cause issues getting definition

    if found_param_element == "shared_no_rename":
        print("# Error: Found a Shared Parameter named '{}'. Cannot rename shared parameters this way.".format(old_name))
    elif found_param_element is None:
        print("# No user-defined Project Parameter named '{}' found to rename.".format(old_name))
    elif found_param_element:
         # Attempting to rename a Project Parameter's ParameterElement.
         # WARNING: Renaming the ParameterElement's *element name* might NOT rename the
         # *parameter definition name* as seen by users. The API generally does not
         # allow changing the Definition.Name property after creation.
         # This section is speculative and likely won't achieve the user's goal.
         try:
             # ParameterElement inherits from Element, so it has a Name property.
             # But changing this might not change the *parameter's* user-visible name.
             # The Definition.Name is likely read-only.
             definition_name = found_param_element.GetDefinition().Name
             print("# Found Project Parameter Element: {} (ID: {}) with Definition Name: {}".format(found_param_element.Name, found_param_element.Id.ToString(), definition_name))
             print("# Error: The Revit API does not support renaming the definition of an existing Project Parameter ('{}'). Renaming must be done manually or by recreating the parameter.".format(old_name))
             # If renaming the Element Name was intended (unlikely):
             # found_param_element.Name = new_name
             # print(f"# Attempted to rename ParameterElement ID {found_param_element.Id} to {new_name}. Note: This may not change the parameter's definition name.")
         except Exception as e:
             print("# Error attempting to interact with found ParameterElement: {}".format(e))

# Final message if no definitive action was taken due to limitations
if not is_builtin and found_param_element != "shared_no_rename" and found_param_element is None:
     print("# No rename action taken. Either 'Comments' is built-in, shared, or no such project parameter exists.")
elif found_param_element and found_param_element != "shared_no_rename":
     print("# Renaming the parameter definition itself is not supported by the API.")