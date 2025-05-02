# Purpose: This script extracts information about Revit and other linked files (CAD, DWF, etc.) within a Revit project and outputs it as a CSV string.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('System')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkInstance,
    ImportInstance,
    RevitLinkType,
    CADLinkType, # Check if ImportInstance uses this or just generic ImportInstance type
    Element,
    ElementId,
    ExternalFileUtils,
    ExternalFileReference,
    ModelPathUtils,
    BuiltInParameter,
    ExternalFileReferenceType
)
import System # For String.Format

# List to hold CSV lines
csv_lines = []
# Add header row - Use more specific headers
csv_lines.append('"Instance ID","Instance Name","Type Name / Source File","File Path","Link Kind","Pinned"')

# --- Process Revit Links ---
collector_rvt = FilteredElementCollector(doc).OfClass(RevitLinkInstance)
for instance in collector_rvt:
    if isinstance(instance, RevitLinkInstance):
        try:
            instance_id_str = instance.Id.ToString()
            # Instance name might not be unique or descriptive, try parameter if needed
            instance_name = instance.Name
            if not instance_name: # Fallback if name is empty
                 instance_name = "Unnamed RVT Link Instance"

            pinned_status = instance.Pinned

            type_id = instance.GetTypeId()
            link_type_name = "Unknown Type"
            file_path_str = "Unknown Path"
            link_kind_str = "Revit Link" # Specific for RevitLinkInstance

            if type_id != ElementId.InvalidElementId:
                link_type = doc.GetElement(type_id)
                if isinstance(link_type, RevitLinkType):
                    link_type_name = link_type.Name # Often includes the file name for RVT links
                    # Try getting path via ExternalFileUtils on the TYPE
                    try:
                        ext_ref = ExternalFileUtils.GetExternalFileReference(doc, type_id)
                        if ext_ref and ext_ref.IsValidObject:
                            model_path = ext_ref.GetAbsolutePath()
                            file_path_str = ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)
                    except Exception as path_ex:
                        # print("# Debug: Could not get path for RVT Link Type {}: {}".format(type_id, path_ex))
                        file_path_str = "Error getting path" # Indicate path retrieval error
                else:
                    link_type_name = "Invalid RVT Link Type"
            else:
                link_type_name = "Invalid Type ID"

            # Escape quotes for CSV safety
            safe_instance_id = '"' + instance_id_str.replace('"', '""') + '"'
            safe_instance_name = '"' + instance_name.replace('"', '""') + '"'
            safe_type_name = '"' + link_type_name.replace('"', '""') + '"'
            safe_file_path = '"' + file_path_str.replace('"', '""') + '"'
            safe_link_kind = '"' + link_kind_str.replace('"', '""') + '"'
            safe_pinned_status = '"' + str(pinned_status) + '"' # Boolean to string

            # Append data row
            csv_lines.append(','.join([safe_instance_id, safe_instance_name, safe_type_name, safe_file_path, safe_link_kind, safe_pinned_status]))

        except Exception as e:
            # print("# Error processing RevitLinkInstance {}: {}".format(instance.Id, e)) # Optional debug
            pass # Silently skip problematic instances

# --- Process Other Links (CAD, DWF, etc.) ---
collector_import = FilteredElementCollector(doc).OfClass(ImportInstance)
for instance in collector_import:
    if isinstance(instance, ImportInstance) and instance.IsLinked:
        try:
            instance_id_str = instance.Id.ToString()
            # Import instance Name is often not useful, use Type Name instead for main description
            instance_name_param = instance.get_Parameter(BuiltInParameter.IMPORT_INSTANCE_NAME) # Try specific parameter
            if instance_name_param and instance_name_param.HasValue:
                instance_name = instance_name_param.AsString()
            else:
                instance_name = instance.Name # Fallback
            if not instance_name:
                instance_name = "Unnamed Link Instance"

            pinned_status = instance.Pinned

            type_id = instance.GetTypeId()
            link_type_name = "Unknown Type"
            file_path_str = "Unknown Path"
            link_kind_str = "Unknown Link" # Default, will try to refine

            if type_id != ElementId.InvalidElementId:
                link_type = doc.GetElement(type_id)
                # Try getting the name from the Type Element directly
                type_name_param = link_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if type_name_param and type_name_param.HasValue:
                     link_type_name = type_name_param.AsString()
                elif link_type and hasattr(link_type, 'Name'):
                     link_type_name = link_type.Name
                else:
                     link_type_name = "Unnamed Link Type"

                if not link_type_name: link_type_name = "Unnamed Link Type"

                # Try getting path and specific type via ExternalFileUtils on the TYPE
                try:
                    ext_ref = ExternalFileUtils.GetExternalFileReference(doc, type_id)
                    if ext_ref and ext_ref.IsValidObject:
                        model_path = ext_ref.GetAbsolutePath()
                        file_path_str = ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)
                        # Get specific link kind (CAD, DWF, etc.)
                        link_kind_enum = ext_ref.ExternalFileReferenceType
                        link_kind_str = link_kind_enum.ToString()
                    # Sometimes the path might be stored directly on the type for CAD links
                    elif isinstance(link_type, CADLinkType):
                        # CADLinkType doesn't directly expose path easily via public API?
                        # Try getting the path parameter if ext_ref failed
                        path_param = link_type.get_Parameter(BuiltInParameter.IMPORT_SYMBOL_NAME) # Might contain path/filename
                        if path_param and path_param.HasValue:
                             file_path_str = path_param.AsString()
                             link_kind_str = "CAD Link" # Assume CAD if it's a CADLinkType

                except Exception as path_ex:
                    # print("# Debug: Could not get path/type for ImportInstance Type {}: {}".format(type_id, path_ex))
                    file_path_str = "Error getting path" # Indicate path retrieval error
            else:
                link_type_name = "Invalid Type ID"

            # Escape quotes for CSV safety
            safe_instance_id = '"' + instance_id_str.replace('"', '""') + '"'
            safe_instance_name = '"' + instance_name.replace('"', '""') + '"'
            safe_type_name = '"' + link_type_name.replace('"', '""') + '"'
            safe_file_path = '"' + file_path_str.replace('"', '""') + '"'
            safe_link_kind = '"' + link_kind_str.replace('"', '""') + '"'
            safe_pinned_status = '"' + str(pinned_status) + '"' # Boolean to string

            # Append data row
            csv_lines.append(','.join([safe_instance_id, safe_instance_name, safe_type_name, safe_file_path, safe_link_kind, safe_pinned_status]))

        except Exception as e:
            # print("# Error processing ImportInstance {}: {}".format(instance.Id, e)) # Optional debug
            pass # Silently skip problematic instances


# Check if we gathered any data
if len(csv_lines) > 1: # More than just the header
    # Format the final output for export
    file_content = "\n".join(csv_lines)
    print("EXPORT::CSV::project_links_status.csv")
    print(file_content)
else:
    print("# No linked file instances found in the project.")